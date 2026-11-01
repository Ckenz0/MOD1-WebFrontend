import { ApiError } from "./api-errors.js";
export { ApiError } from "./api-errors.js";

import { isTokenResponse, isIdentity, isProfile, isPasswordPolicy, isRegistrationResponse, isLoginResponse } from "./auth-domain.js";
export { isTokenResponse } from "./auth-domain.js";

export function createApiClient({ baseUrl, fetchImpl = fetch, timeoutMs = 10000, readiness = null }) {
  const url = new URL(baseUrl);
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password
      || url.search || url.hash) {
    throw new TypeError("Configure um endereço HTTP(S) válido para a API.");
  }
  const base = url.href.replace(/\/$/, "");

  async function request(path, options, validate, signal) {
    try { await readiness?.prepare({ signal }); }
    catch (error) { throw new ApiError(error.kind === "cancelled" ? "cancelled" : "unavailable"); }
    const controller = new AbortController();
    let timedOut = false;
    const cancel = () => controller.abort();
    if (signal?.aborted) cancel();
    signal?.addEventListener("abort", cancel, { once: true });
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, timeoutMs);
    try {
      if (controller.signal.aborted) throw new ApiError("cancelled");
      const response = await fetchImpl(base + path, {
        ...options, signal: controller.signal, credentials: "omit", cache: "no-store",
        redirect: "error",
      });
      if (controller.signal.aborted) throw new ApiError(timedOut ? "timeout" : "cancelled");
      if (!response.ok) {
        const kind = response.status === 401
          ? (path === "/auth/token" ? "credentials" : "unauthorized")
          : response.status === 400 && path === "/auth/password" ? "password-rejected"
          : response.status === 422 ? "validation" : "unavailable";
        throw new ApiError(kind);
      }
      if (["/auth/password", "/auth/logout"].includes(path) && response.status === 204) return null;
      let data;
      try {
        data = await response.json();
      } catch {
        throw new ApiError("invalid-response");
      }
      if (controller.signal.aborted) throw new ApiError(timedOut ? "timeout" : "cancelled");
      if (!validate(data)) throw new ApiError("invalid-response");
      return data;
    } catch (error) {
      if (timedOut) readiness?.invalidate();
      if (controller.signal.aborted) throw new ApiError(timedOut ? "timeout" : "cancelled");
      if (["unavailable", "network", "timeout"].includes(error.kind) || !(error instanceof ApiError)) readiness?.invalidate();
      if (error instanceof ApiError) throw error;
      throw new ApiError("network");
    } finally {
      clearTimeout(timeout);
      signal?.removeEventListener("abort", cancel);
    }
  }

  return {
    refresh(refreshToken, { signal } = {}) {
      return request("/auth/refresh", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }) }, isTokenResponse, signal);
    },
    logout(token, { signal } = {}) {
      return request("/auth/logout", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: "{}" }, () => false, signal);
    },
    activity(token, { signal } = {}) {
      return request("/auth/session/activity", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: "{}" }, value => value && Number.isFinite(Date.parse(value.idle_expires_at))
          && Number.isFinite(Date.parse(value.absolute_expires_at)), signal);
    },
    verifyMfa(challengeToken, code, { recovery = false, signal } = {}) {
      return request("/auth/mfa/verify", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ challenge_token: challengeToken, [recovery ? "recovery_code" : "code"]: code }) }, isTokenResponse, signal);
    },
    getProfile(token, userId, { signal } = {}) {
      return request("/auth/profile", { method: "GET", headers: { Authorization: `Bearer ${token}` } },
        value => isProfile(value, userId), signal);
    },
    updateProfile(token, userId, change, { signal } = {}) {
      return request("/auth/profile", { method: "PATCH", headers: {
        Authorization: `Bearer ${token}`, "Content-Type": "application/json",
      }, body: JSON.stringify(change) }, value => isProfile(value, userId), signal);
    },
    passwordPolicy({ signal } = {}) {
      return request("/auth/password-policy", { method: "GET" }, isPasswordPolicy, signal);
    },
    changePassword(token, currentPassword, newPassword, { signal } = {}) {
      return request("/auth/password", { method: "POST", headers: {
        "Content-Type": "application/json", Authorization: `Bearer ${token}`,
      }, body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }) }, () => false, signal);
    },
    register(displayName, email, password, { signal } = {}) {
      return request("/auth/register", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ display_name: displayName, email, password }),
      }, isRegistrationResponse, signal);
    },
    login(email, password, { signal } = {}) {
      return request("/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email, password }),
      }, isLoginResponse, signal);
    },
    getMe(token, { signal } = {}) {
      return request("/auth/me", {
        method: "GET", headers: token ? { Authorization: `Bearer ${token}` } : {},
      }, isIdentity, signal);
    },
  };
}
