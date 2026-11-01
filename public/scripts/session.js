import { isTokenResponse } from "./auth-domain.js";

export function createSession({ now = Date.now } = {}) {
  let token = null;
  let expiresAt = 0;
  let refreshToken = null, sessionId = null;
  let idleExpiresAt = Infinity, absoluteExpiresAt = Infinity;

  function clear() {
    token = null;
    expiresAt = 0;
    refreshToken = sessionId = null;
    idleExpiresAt = absoluteExpiresAt = Infinity;
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
    },
    clear,
  };
}
