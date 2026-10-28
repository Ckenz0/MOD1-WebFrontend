const messages = {
  unauthorized: "Sua sessão terminou. Entre novamente para continuar.",
  validation: "Confira o nome e a descrição do projeto e tente novamente.",
  "not-found": "Este projeto não está disponível para sua conta. Volte para a lista.",
  unavailable: "O serviço de projetos está indisponível. Tente novamente em instantes.",
  network: "Não foi possível conectar ao serviço de projetos. Confira a conexão e tente novamente.",
  timeout: "O serviço de projetos demorou para responder. Atualize a lista antes de tentar novamente.",
  "invalid-response": "Não foi possível confirmar os dados do projeto. Tente novamente.",
  cancelled: "A solicitação foi cancelada.",
};

export class ProjectsApiError extends Error {
  constructor(kind) { super(messages[kind]); this.name = "ProjectsApiError"; this.kind = kind; }
}

const uuid = /^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i;
function isProject(p) {
  return p !== null && typeof p === "object" && typeof p.id === "string" && uuid.test(p.id)
    && typeof p.owner_id === "string" && uuid.test(p.owner_id)
    && typeof p.name === "string" && p.name.trim().length > 0 && Array.from(p.name).length <= 120
    && typeof p.description === "string" && Array.from(p.description).length <= 2000
    && (p.objective === undefined || (typeof p.objective === "string" && Array.from(p.objective).length <= 2000))
    && typeof p.created_at === "string" && Number.isFinite(Date.parse(p.created_at));
}
function isPage(p) {
  return p !== null && typeof p === "object" && Array.isArray(p.items) && p.items.every(isProject)
    && Number.isSafeInteger(p.total) && p.total >= 0 && Number.isSafeInteger(p.limit)
    && p.limit >= 1 && p.limit <= 100 && Number.isSafeInteger(p.offset) && p.offset >= 0
    && p.items.length <= p.limit && p.items.length <= p.total;
}

export function createProjectsApiClient({ baseUrl, fetchImpl = fetch, timeoutMs = 10000, readiness = null }) {
  const url = new URL(baseUrl);
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
    throw new TypeError("Configure um endereço HTTP(S) válido para projetos.");
  }
  const base = url.href.replace(/\/$/, "");
  async function request(path, token, options, validate, signal) {
    try { await readiness?.prepare({ signal }); }
    catch (error) { throw new ProjectsApiError(error.kind === "cancelled" ? "cancelled" : "unavailable"); }
    const controller = new AbortController();
    let timedOut = false;
    const cancel = () => controller.abort();
    if (signal?.aborted) cancel();
    signal?.addEventListener("abort", cancel, { once: true });
    const timer = setTimeout(() => { timedOut = true; cancel(); }, timeoutMs);
    try {
      if (controller.signal.aborted) throw new ProjectsApiError("cancelled");
      const response = await fetchImpl(base + path, { ...options,
        headers: { ...options.headers, Authorization: `Bearer ${token}` },
        signal: controller.signal, credentials: "omit", cache: "no-store", redirect: "error" });
      if (controller.signal.aborted) throw new ProjectsApiError(timedOut ? "timeout" : "cancelled");
      if (!response.ok) throw new ProjectsApiError(response.status === 401 ? "unauthorized"
        : response.status === 404 ? "not-found" : response.status === 422 ? "validation" : "unavailable");
      let value;
      try { value = await response.json(); } catch { throw new ProjectsApiError("invalid-response"); }
      if (controller.signal.aborted) throw new ProjectsApiError(timedOut ? "timeout" : "cancelled");
      if (!validate(value)) throw new ProjectsApiError("invalid-response");
      return value;
    } catch (error) {
      if (timedOut) readiness?.invalidate();
      if (controller.signal.aborted) throw new ProjectsApiError(timedOut ? "timeout" : "cancelled");
      if (["unavailable", "network", "timeout"].includes(error.kind) || !(error instanceof ProjectsApiError)) readiness?.invalidate();
      if (error instanceof ProjectsApiError) throw error;
      throw new ProjectsApiError("network");
    } finally { clearTimeout(timer); signal?.removeEventListener("abort", cancel); }
  }
  return {
    create(token, { name, description = "", objective }, { signal } = {}) {
      return request("/projects", token, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description, ...(objective !== undefined ? { objective } : {}) }) }, isProject, signal);
    },
    list(token, { limit = 20, offset = 0, q = "", signal } = {}) {
      const params = new URLSearchParams({ limit, offset });
      if (q.trim()) params.set("q", q.trim());
      return request(`/projects?${params}`, token, { method: "GET" }, isPage, signal);
    },
    update(token, projectId, change, { signal } = {}) {
      if (typeof projectId !== "string" || !uuid.test(projectId)) return Promise.reject(new ProjectsApiError("not-found"));
      return request(`/projects/${projectId}`, token, { method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(change) }, p => isProject(p) && p.id === projectId, signal);
    },
    get(token, projectId, { signal } = {}) {
      if (typeof projectId !== "string" || !uuid.test(projectId)) return Promise.reject(new ProjectsApiError("not-found"));
      return request(`/projects/${projectId}`, token, { method: "GET" }, isProject, signal);
    },
  };
}
