// Browser persistence is isolated from the session's validity rules.
export function createSessionStorage({ getStorage = () => globalThis.sessionStorage } = {}) {
  const key = "mod1-session-v1";
  function clear() {
    try { getStorage().removeItem(key); } catch { /* Memory-only login remains available. */ }
  }
  return {
    load() {
      try {
        const raw = getStorage().getItem(key);
        return raw === null ? null : JSON.parse(raw);
      } catch { clear(); return null; }
    },
    save(snapshot) {
      try { getStorage().setItem(key, JSON.stringify(snapshot)); }
      catch { clear(); } // Never leave an older refresh credential behind after rotation.
    },
    clear,
  };
}
