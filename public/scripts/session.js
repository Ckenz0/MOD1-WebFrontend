import { isTokenResponse } from "./api.js";

export function createSession({ now = Date.now } = {}) {
  let token = null;
  let expiresAt = 0;

  function clear() {
    token = null;
    expiresAt = 0;
  }

  function isActive() {
    if (!token || now() >= expiresAt) {
      clear();
      return false;
    }
    return true;
  }

  return {
    start(response) {
      if (!isTokenResponse(response)) throw new TypeError("Invalid authentication response");
      token = response.access_token;
      expiresAt = now() + response.expires_in * 1000;
    },
    isActive,
    getToken: () => isActive() ? token : null,
    clear,
  };
}
