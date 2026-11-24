import { PlatformApiError } from "./api-errors.js";

const MAX_BYTES = 10 * 1024 * 1024;

// Binary transport belongs beside the JSON client; no DOM or session storage.
export async function artifactDownload({ base, fetchImpl, path, token, signal, timeout = 35000 }) {
  if (!/^\/projects\/[a-zA-Z0-9-]+\/artifacts\/[1-9][0-9]*\/download\?module3_project_id=[1-9][0-9]*$/.test(path)) {
    throw new TypeError("Invalid artifact download path");
  }
  const controller = new AbortController();
  const cancel = () => controller.abort();
  let timedOut = false, reader;
  if (signal?.aborted) cancel();
  signal?.addEventListener("abort", cancel, { once: true });
  const timer = setTimeout(() => { timedOut = true; cancel(); }, timeout);
  const check = () => {
    if (controller.signal.aborted) throw new PlatformApiError(timedOut ? "timeout" : "cancelled");
  };
  try {
    check();
    const response = await fetchImpl(base + path, { method: "GET", signal: controller.signal,
      headers: { Authorization: `Bearer ${token}`, Accept: "application/octet-stream" },
      credentials: "omit", cache: "no-store", redirect: "error" });
    check();
    if (!response.ok) throw new PlatformApiError(({ 401: "unauthorized", 403: "forbidden", 404: "not-found", 409: "conflict" })[response.status] || "unavailable");
    const length = response.headers.get("Content-Length");
    if (response.headers.get("Content-Type")?.split(";")[0].trim().toLowerCase() !== "application/octet-stream"
        || (length !== null && (!/^[0-9]+$/.test(length) || Number(length) > MAX_BYTES)) || !response.body) {
      await response.body?.cancel();
      throw new PlatformApiError("invalid-response");
    }
    reader = response.body.getReader();
    const chunks = []; let size = 0;
    while (true) {
      check();
      const { done, value } = await reader.read();
      check();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_BYTES) throw new PlatformApiError("invalid-response");
      chunks.push(value);
    }
    return new Blob(chunks, { type: "application/octet-stream" });
  } catch (error) {
    check();
    if (error instanceof PlatformApiError) throw error;
    throw new PlatformApiError("network");
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", cancel);
    try { await reader?.cancel(); } catch { /* A cancelled transport is already closed. */ }
  }
}
