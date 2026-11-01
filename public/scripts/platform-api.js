import { PlatformApiError } from "./api-errors.js";

export function createPlatformClient({ baseUrl, fetchImpl = fetch, timeoutMs = 10000 }) {
  const url = new URL(baseUrl);
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
    throw new TypeError("Configure um endereço HTTP(S) válido para o serviço.");
  }
  const base = url.href.replace(/\/$/, "");
  return {
    async request(method, path, token, body, { signal, timeout = timeoutMs, validate = value => value !== null && typeof value === "object" } = {}) {
      const decoded = decodeURIComponent(path.split("?")[0]);
      if (!path.startsWith("/") || path.startsWith("//") || decoded.includes("\\")
          || decoded.split("/").some(part => part === ".." || part === ".")
          || !["GET", "POST", "PATCH", "PUT", "DELETE"].includes(method)) throw new TypeError("Invalid service request");
      const controller = new AbortController();
      const cancel = () => controller.abort();
      if (signal?.aborted) cancel();
      signal?.addEventListener("abort", cancel, { once: true });
      let timedOut = false;
      const timer = setTimeout(() => { timedOut = true; cancel(); }, timeout);
      try {
        if (controller.signal.aborted) throw new PlatformApiError("cancelled");
        const response = await fetchImpl(base + path, { method,
          headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(body !== undefined ? { "Content-Type": "application/json" } : {}) },
          body: body !== undefined ? JSON.stringify(body) : undefined, signal: controller.signal,
          credentials: "omit", redirect: "error", cache: "no-store" });
        if (controller.signal.aborted) throw new PlatformApiError(timedOut ? "timeout" : "cancelled");
        if (!response.ok) throw new PlatformApiError(({ 401: "unauthorized", 403: "forbidden", 404: "not-found", 409: "conflict", 422: "validation" })[response.status] || "unavailable");
        if (response.status === 204 && method !== "GET") return null;
        let result;
        try { result = await response.json(); } catch { throw new PlatformApiError("invalid-response"); }
        if (controller.signal.aborted) throw new PlatformApiError(timedOut ? "timeout" : "cancelled");
        if (!validate(result)) throw new PlatformApiError("invalid-response");
        return result;
      } catch (error) {
        if (controller.signal.aborted) throw new PlatformApiError(timedOut ? "timeout" : "cancelled");
        if (error instanceof PlatformApiError) throw error;
        throw new PlatformApiError("network");
      } finally { clearTimeout(timer); signal?.removeEventListener("abort", cancel); }
    },
  };
}
