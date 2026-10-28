import { isPermissions, ROLE_NAMES } from "./permissions.js";

const messages = {
  unauthorized: "Sua sessão terminou. Entre novamente para continuar.",
  validation: "Confira o nome e a descrição do projeto e tente novamente.",
  "not-found": "Este projeto não está disponível para sua conta. Volte para a lista.",
  unavailable: "O serviço de projetos está indisponível. Tente novamente em instantes.",
  network: "Não foi possível conectar ao serviço de projetos. Confira a conexão e tente novamente.",
  timeout: "O serviço de projetos demorou para responder. Atualize a lista antes de tentar novamente.",
  "invalid-response": "Não foi possível confirmar os dados do projeto. Tente novamente.",
  cancelled: "A solicitação foi cancelada.",
  forbidden: "Você não tem permissão para esta ação. Atualize os acessos do projeto.",
  conflict: "Não foi possível alterar este vínculo. O proprietário é protegido e contas já vinculadas não precisam de novo convite.",
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
    && (p.permissions === undefined || isPermissions(p.permissions))
    && typeof p.created_at === "string" && Number.isFinite(Date.parse(p.created_at));
}
const isId = value => typeof value === "string" && uuid.test(value);
const isDate = value => typeof value === "string" && Number.isFinite(Date.parse(value));
const rolesValid = (roles, owner = false) => Array.isArray(roles) && new Set(roles).size === roles.length
  && roles.every(role => typeof role === "string" && Object.hasOwn(ROLE_NAMES, role) && (owner || role !== "owner"));
const isMember = value => value && isId(value.user_id) && typeof value.is_owner === "boolean"
  && rolesValid(value.roles, value.is_owner) && (value.expires_at === null || isDate(value.expires_at));
const isAccess = (value, projectId) => value && value.project_id === projectId && isId(value.user_id)
  && typeof value.is_owner === "boolean" && rolesValid(value.roles, value.is_owner) && isPermissions(value.permissions);
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
        : response.status === 403 ? "forbidden" : response.status === 409 ? "conflict"
        : response.status === 404 ? "not-found" : response.status === 422 ? "validation" : "unavailable");
      if (response.status === 204 && options.method === "DELETE") return null;
      if (response.status === 204 && path === "/invitations/decline") return null;
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
    access(token, projectId, { signal } = {}) {
      if (!isId(projectId)) return Promise.reject(new ProjectsApiError("not-found"));
      return request(`/projects/${projectId}/access`, token, { method: "GET" }, value => isAccess(value, projectId), signal);
    },
    roles(token, projectId, { signal } = {}) {
      if (!isId(projectId)) return Promise.reject(new ProjectsApiError("not-found"));
      return request(`/projects/${projectId}/roles`, token, { method: "GET" }, value => value && Array.isArray(value.items)
        && value.items.length === 3 && new Set(value.items.map(r => r.key)).size === 3
        && value.items.every(r => Object.hasOwn(ROLE_NAMES, r.key) && r.key !== "owner"
          && typeof r.name === "string" && isPermissions(r.permissions)), signal);
    },
    members(token, projectId, { limit = 20, offset = 0, signal } = {}) {
      if (!isId(projectId)) return Promise.reject(new ProjectsApiError("not-found"));
      return request(`/projects/${projectId}/members?${new URLSearchParams({ limit, offset })}`, token,
        { method: "GET" }, value => value && Array.isArray(value.items) && value.items.every(isMember)
          && value.limit === limit && value.offset === offset && Number.isInteger(value.total) && value.total >= 0
          && value.items.length <= Math.min(limit, Math.max(0, value.total - offset)), signal);
    },
    updateMember(token, projectId, userId, change, { signal } = {}) {
      if (!isId(projectId) || !isId(userId)) return Promise.reject(new ProjectsApiError("not-found"));
      return request(`/projects/${projectId}/members/${userId}`, token, { method: "PATCH",
        headers: { "Content-Type": "application/json" }, body: JSON.stringify(change) },
        value => isMember(value) && value.user_id === userId, signal);
    },
    removeMember(token, projectId, userId, { signal } = {}) {
      if (!isId(projectId) || !isId(userId)) return Promise.reject(new ProjectsApiError("not-found"));
      return request(`/projects/${projectId}/members/${userId}`, token, { method: "DELETE" }, () => false, signal);
    },
    invite(token, projectId, draft, { signal } = {}) {
      if (!isId(projectId)) return Promise.reject(new ProjectsApiError("not-found"));
      return request(`/projects/${projectId}/invitations`, token, { method: "POST",
        headers: { "Content-Type": "application/json" }, body: JSON.stringify(draft) }, value => value
        && isId(value.id) && value.project_id === projectId && value.user_id === draft.user_id
        && rolesValid(value.roles) && typeof value.code === "string" && /^[\w-]{32,200}$/.test(value.code)
        && isDate(value.code_expires_at) && (value.expires_at === null || isDate(value.expires_at)), signal);
    },
    acceptInvitation(token, code, { signal } = {}) {
      return request("/invitations/accept", token, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }) }, value => isAccess(value, value?.project_id) && isId(value.project_id), signal);
    },
    declineInvitation(token, code, { signal } = {}) {
      return request("/invitations/decline", token, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }) }, () => false, signal);
    },
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
