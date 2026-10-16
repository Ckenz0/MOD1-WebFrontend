const messages = {
  unauthorized: "Sua sessão terminou. Entre novamente para continuar.",
  validation: "Confira o título e os campos da história e tente novamente.",
  "not-found": "Esta história não está disponível para sua conta. Volte para a lista.",
  unavailable: "O serviço de backlog está indisponível. Tente novamente em instantes.",
  network: "Não foi possível conectar ao serviço de backlog. Confira a conexão e tente novamente.",
  timeout: "O serviço de backlog demorou para responder. Atualize a lista antes de tentar novamente.",
  "invalid-response": "Não foi possível confirmar os dados da história. Tente novamente.",
  cancelled: "A solicitação foi cancelada.",
};

export class BacklogApiError extends Error {
  constructor(kind) { super(messages[kind]); this.name = "BacklogApiError"; this.kind = kind; }
}

const uuid = /^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i;
// JS whitespace plus Python's NEL and information separators: same rules as StoryDraft.
export const trimStoryTitle = value => value.replace(/^[\s\u0085\u001c-\u001f]+|[\s\u0085\u001c-\u001f]+$/gu, "");
const isId = value => typeof value === "string" && uuid.test(value);
const text = (value, max) => typeof value === "string" && Array.from(value).length <= max;
function isStory(s, projectId, storyId) {
  return s !== null && typeof s === "object" && isId(s.id) && isId(s.created_by)
    && s.project_id === projectId && (!storyId || s.id === storyId)
    && text(s.title, 120) && trimStoryTitle(s.title).length > 0
    && text(s.description, 2000) && text(s.acceptance_criteria, 2000)
    && ["high", "medium", "low"].includes(s.priority) && ["todo", "in_progress", "done"].includes(s.status)
    && typeof s.created_at === "string" && Number.isFinite(Date.parse(s.created_at))
    && typeof s.updated_at === "string" && Number.isFinite(Date.parse(s.updated_at))
    && Date.parse(s.updated_at) >= Date.parse(s.created_at);
}
function isPage(p, projectId, limit, offset) {
  return p !== null && typeof p === "object" && Array.isArray(p.items)
    && p.items.every(s => isStory(s, projectId)) && Number.isSafeInteger(p.total) && p.total >= 0
    && p.limit === limit && p.offset === offset && p.items.length <= limit
    && p.items.length <= Math.max(0, p.total - offset);
}

export function createBacklogApiClient({ baseUrl, fetchImpl = fetch, timeoutMs = 10000, readiness = null }) {
  const url = new URL(baseUrl);
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
    throw new TypeError("Configure um endereço HTTP(S) válido para backlog.");
  }
  const base = url.href.replace(/\/$/, "");
  async function request(path, token, options, validate, signal) {
    try { await readiness?.prepare({ signal }); }
    catch (error) { throw new BacklogApiError(error.kind === "cancelled" ? "cancelled" : "unavailable"); }
    const controller = new AbortController();
    let timedOut = false;
    const cancel = () => controller.abort();
    if (signal?.aborted) cancel();
    signal?.addEventListener("abort", cancel, { once: true });
    const timer = setTimeout(() => { timedOut = true; cancel(); }, timeoutMs);
    try {
      if (controller.signal.aborted) throw new BacklogApiError("cancelled");
      const response = await fetchImpl(base + path, { ...options,
        headers: { ...options.headers, Authorization: `Bearer ${token}` },
        signal: controller.signal, credentials: "omit", cache: "no-store", redirect: "error" });
      if (controller.signal.aborted) throw new BacklogApiError(timedOut ? "timeout" : "cancelled");
      if (!response.ok) throw new BacklogApiError(response.status === 401 ? "unauthorized"
        : response.status === 404 ? "not-found" : response.status === 422 ? "validation" : "unavailable");
      let value;
      try { value = await response.json(); } catch { throw new BacklogApiError("invalid-response"); }
      if (controller.signal.aborted) throw new BacklogApiError(timedOut ? "timeout" : "cancelled");
      if (!validate(value)) throw new BacklogApiError("invalid-response");
      return value;
    } catch (error) {
      if (timedOut) readiness?.invalidate();
      if (controller.signal.aborted) throw new BacklogApiError(timedOut ? "timeout" : "cancelled");
      if (["unavailable", "network", "timeout"].includes(error.kind) || !(error instanceof BacklogApiError)) readiness?.invalidate();
      if (error instanceof BacklogApiError) throw error;
      throw new BacklogApiError("network");
    } finally { clearTimeout(timer); signal?.removeEventListener("abort", cancel); }
  }

  const collection = projectId => `/projects/${projectId}/stories`;
  const validIds = (projectId, storyId) => isId(projectId) && (storyId === undefined || isId(storyId));
  const rejected = () => Promise.reject(new BacklogApiError("not-found"));
  return {
    create(token, projectId, { title, description = "", acceptance_criteria = "", priority = "medium" }, { signal } = {}) {
      if (!validIds(projectId)) return rejected();
      return request(collection(projectId), token, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description, acceptance_criteria, priority }) }, s => isStory(s, projectId), signal);
    },
    list(token, projectId, { limit = 20, offset = 0, signal } = {}) {
      if (!validIds(projectId)) return rejected();
      if (!Number.isSafeInteger(limit) || limit < 1 || limit > 100 || !Number.isSafeInteger(offset) || offset < 0)
        return Promise.reject(new BacklogApiError("validation"));
      return request(`${collection(projectId)}?${new URLSearchParams({ limit, offset })}`, token,
        { method: "GET" }, p => isPage(p, projectId, limit, offset), signal);
    },
    get(token, projectId, storyId, { signal } = {}) {
      if (!validIds(projectId, storyId)) return rejected();
      return request(`${collection(projectId)}/${storyId}`, token, { method: "GET" }, s => isStory(s, projectId, storyId), signal);
    },
    update(token, projectId, storyId, change, { signal } = {}) {
      if (!validIds(projectId, storyId)) return rejected();
      return request(`${collection(projectId)}/${storyId}`, token, { method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(change) }, s => isStory(s, projectId, storyId), signal);
    },
  };
}
