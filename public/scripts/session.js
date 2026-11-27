import { isTokenResponse } from "./auth-domain.js";

export function createSession({ now = Date.now, store = null } = {}) {
  let token = null;
  let expiresAt = 0;
  let refreshToken = null, sessionId = null;
  let idleExpiresAt = Infinity, absoluteExpiresAt = Infinity;

  function clear() {
    token = null;
    expiresAt = 0;
    refreshToken = sessionId = null;
    idleExpiresAt = absoluteExpiresAt = Infinity;
    store?.clear();
  }

  function persist() {
    store?.save({ version: 1, token, refreshToken, sessionId, accessExpiresAt: expiresAt,
      idleExpiresAt: Number.isFinite(idleExpiresAt) ? idleExpiresAt : null,
      absoluteExpiresAt: Number.isFinite(absoluteExpiresAt) ? absoluteExpiresAt : null });
  }

  function restore() {
    const saved = store?.load();
    if (saved === null || saved === undefined) return;
    const credential = value => typeof value === "string" && value.trim().length > 0;
    const timestamp = value => typeof value === "number" && Number.isFinite(value) && value >= 0;
    const optionalDeadline = value => value === null || timestamp(value);
    if (!saved || saved.version !== 1 || !credential(saved.token)
        || !(saved.refreshToken === null || credential(saved.refreshToken))
        || !(saved.sessionId === null || credential(saved.sessionId))
        || !timestamp(saved.accessExpiresAt) || !optionalDeadline(saved.idleExpiresAt)
        || !optionalDeadline(saved.absoluteExpiresAt)) { clear(); return; }
    token = saved.token;
    refreshToken = saved.refreshToken;
    sessionId = saved.sessionId;
    expiresAt = saved.accessExpiresAt;
    absoluteExpiresAt = saved.absoluteExpiresAt === null ? Infinity : saved.absoluteExpiresAt;
    idleExpiresAt = Math.min(saved.idleExpiresAt === null ? Infinity : saved.idleExpiresAt, absoluteExpiresAt);
    isSessionAlive();
  }

  function isSessionAlive() {
    if (!token || now() >= idleExpiresAt || now() >= absoluteExpiresAt || (!refreshToken && now() >= expiresAt)) {
      clear();
      return false;
    }
    return true;
  }

  const isActive = () => isSessionAlive() && now() < expiresAt;
  function deadline(value) {
    if (value === undefined) return Infinity;
    const parsed = Date.parse(value);
    if (!Number.isFinite(parsed)) throw new TypeError("Invalid session deadline");
    return parsed;
  }

  restore();

  return {
    start(response) {
      if (!isTokenResponse(response)) throw new TypeError("Invalid authentication response");
      const idle = deadline(response.idle_expires_at), absolute = deadline(response.absolute_expires_at);
      if (response.refresh_token !== undefined && (typeof response.refresh_token !== "string" || !response.refresh_token.trim())) {
        throw new TypeError("Invalid refresh response");
      }
      token = response.access_token;
      expiresAt = now() + response.expires_in * 1000;
      refreshToken = response.refresh_token || null;
      sessionId = response.session_id || null;
      absoluteExpiresAt = absolute;
      idleExpiresAt = Math.min(idle, absolute);
      persist();
    },
    isActive,
    isSessionAlive,
    shouldRefresh: (leadMs = 60000) => isSessionAlive() && Boolean(refreshToken) && expiresAt - now() <= leadMs,
    getRefreshToken: () => isSessionAlive() ? refreshToken : null,
    getSessionId: () => isSessionAlive() ? sessionId : null,
    getRequestToken: () => isSessionAlive() ? token : null,
    getToken: () => isActive() ? token : null,
    deadlines: () => ({ access: expiresAt, idle: idleExpiresAt, absolute: absoluteExpiresAt }),
    updateActivity(response) {
      if (!isSessionAlive()) return;
      absoluteExpiresAt = Math.min(absoluteExpiresAt, deadline(response.absolute_expires_at));
      idleExpiresAt = Math.min(deadline(response.idle_expires_at), absoluteExpiresAt);
      persist();
    },
    clear,
  };
}
