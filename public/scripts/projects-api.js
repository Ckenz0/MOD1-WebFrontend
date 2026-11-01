import { ProjectsApiError } from "./api-errors.js";
export { ProjectsApiError } from "./api-errors.js";

import { isProject, isPage, isId, isMember, isAccess, isRolesPage, isMemberPage, isInvitationCreated } from "./project-domain.js";

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
      return request(`/projects/${projectId}/roles`, token, { method: "GET" }, isRolesPage, signal);
    },
    members(token, projectId, { limit = 20, offset = 0, signal } = {}) {
      if (!isId(projectId)) return Promise.reject(new ProjectsApiError("not-found"));
      return request(`/projects/${projectId}/members?${new URLSearchParams({ limit, offset })}`, token,
        { method: "GET" }, value => isMemberPage(value, limit, offset), signal);
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
        headers: { "Content-Type": "application/json" }, body: JSON.stringify(draft) },
        value => isInvitationCreated(value, projectId, draft), signal);
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
    list(token, { limit = 20, offset = 0, q = "", status = "", tag = "", archived = false, signal } = {}) {
      const params = new URLSearchParams({ limit, offset });
      if (q.trim()) params.set("q", q.trim());
      if (status) params.set("status", status);
      if (tag.trim()) params.set("tag", tag.trim());
      if (archived) params.set("archived", "true");
      return request(`/projects?${params}`, token, { method: "GET" }, isPage, signal);
    },
    update(token, projectId, change, { signal } = {}) {
      if (!isId(projectId)) return Promise.reject(new ProjectsApiError("not-found"));
      return request(`/projects/${projectId}`, token, { method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(change) }, p => isProject(p) && p.id === projectId, signal);
    },
    get(token, projectId, { signal } = {}) {
      if (!isId(projectId)) return Promise.reject(new ProjectsApiError("not-found"));
      return request(`/projects/${projectId}`, token, { method: "GET" }, isProject, signal);
    },
  };
}
