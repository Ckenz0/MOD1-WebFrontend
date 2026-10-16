export class ReadinessError extends Error {
  constructor(kind) { super(kind); this.name = "ReadinessError"; this.kind = kind; }
}

const aborted = signal => new ReadinessError(signal.reason === "timeout" ? "timeout" : "cancelled");

function abortable(promise, signal) {
  if (signal.aborted) return Promise.reject(aborted(signal));
  return new Promise((resolve, reject) => {
    const cancel = () => reject(aborted(signal));
    signal.addEventListener("abort", cancel, { once: true });
    Promise.resolve(promise).then(resolve, reject).finally(() => signal.removeEventListener("abort", cancel));
  });
}

function pause(milliseconds, signal) {
  let timer;
  const pending = new Promise(resolve => { timer = setTimeout(resolve, milliseconds); });
  return abortable(pending, signal).finally(() => clearTimeout(timer));
}

export function createServiceReadiness({ baseUrls, fetchImpl = fetch, timeoutMs = 90000,
  requestTimeoutMs = 30000, retryDelayMs = 2000, cacheMs = 60000, onWaiting = () => {} }) {
  const urls = [...new Set(baseUrls)].map(base => {
    const url = new URL(base);
    if (!["http:", "https:"].includes(url.protocol) || url.username || url.password
        || url.search || url.hash || !["", "/"].includes(url.pathname)) {
      throw new TypeError("Configure uma origem HTTP(S) válida para preparar o acesso.");
    }
    return url.origin + "/health/ready";
  });
  if (!urls.length || [timeoutMs, requestTimeoutMs, retryDelayMs, cacheMs]
    .some(value => !Number.isFinite(value) || value <= 0)) throw new TypeError("Invalid readiness limits");
  let readyUntil = 0, active = null;

  async function run(controller) {
    const { signal } = controller;
    const deadline = performance.now() + timeoutMs;
    const totalTimer = setTimeout(() => controller.abort("timeout"), timeoutMs);
    async function probe(url) {
      while (!signal.aborted) {
        const remaining = deadline - performance.now();
        if (remaining <= 0) { controller.abort("timeout"); break; }
        const attempt = new AbortController();
        const cancel = () => attempt.abort(signal.reason);
        signal.addEventListener("abort", cancel, { once: true });
        const timer = setTimeout(() => attempt.abort("attempt-timeout"), Math.min(requestTimeoutMs, remaining));
        try {
          const response = await abortable(fetchImpl(url, {
            method: "GET", signal: attempt.signal, credentials: "omit", cache: "no-store", redirect: "error",
          }), attempt.signal);
          response.body?.cancel().catch(() => {});
          if (signal.aborted) throw aborted(signal);
          if (response.ok) return;
        } catch {
          if (signal.aborted) throw aborted(signal);
        } finally {
          clearTimeout(timer); signal.removeEventListener("abort", cancel);
        }
        await pause(Math.max(0, Math.min(retryDelayMs, deadline - performance.now())), signal);
      }
      throw aborted(signal);
    }
    try { await Promise.all(urls.map(probe)); }
    catch (error) { controller.abort(error.kind); throw error; }
    finally { clearTimeout(totalTimer); }
  }

  function prepare({ signal } = {}) {
    if (signal?.aborted) return Promise.reject(new ReadinessError("cancelled"));
    if (performance.now() < readyUntil) return Promise.resolve();
    if (!active || active.controller.signal.aborted) {
      const task = { controller: new AbortController(), users: 0, promise: null };
      active = task;
      task.promise = run(task.controller).then(() => {
        if (active === task) readyUntil = performance.now() + cacheMs;
      }).finally(() => { if (active === task) active = null; });
      task.promise.catch(() => {});
      onWaiting();
    }
    const task = active;
    task.users++;
    return new Promise((resolve, reject) => {
      let finished = false;
      const finish = error => {
        if (finished) return;
        finished = true;
        signal?.removeEventListener("abort", cancel);
        task.users--;
        if (!task.users && active === task) task.controller.abort("cancelled");
        if (error) reject(error); else resolve();
      };
      const cancel = () => finish(new ReadinessError("cancelled"));
      signal?.addEventListener("abort", cancel, { once: true });
      task.promise.then(() => finish(), finish);
    });
  }

  return { prepare, invalidate: () => { readyUntil = 0; } };
}
