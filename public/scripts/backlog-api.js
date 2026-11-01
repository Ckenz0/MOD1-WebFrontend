import { BacklogApiError } from "./api-errors.js";
export { BacklogApiError } from "./api-errors.js";

import { isId, isStory, isPage } from "./story-domain.js";
export { trimStoryTitle } from "./story-domain.js";

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
        : response.status === 403 ? "forbidden" : response.status === 404 ? "not-found" : response.status === 422 ? "validation" : "unavailable");
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
    list(token, projectId, { limit = 20, offset = 0, q = "", status, priority, signal } = {}) {
      if (!validIds(projectId)) return rejected();
      if (!Number.isSafeInteger(limit) || limit < 1 || limit > 100 || !Number.isSafeInteger(offset) || offset < 0)
        return Promise.reject(new BacklogApiError("validation"));
      const params = new URLSearchParams({ limit, offset });
      if (q.trim()) params.set("q", q.trim());
      if (status) params.set("status", status);
      if (priority) params.set("priority", priority);
      return request(`${collection(projectId)}?${params}`, token,
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
