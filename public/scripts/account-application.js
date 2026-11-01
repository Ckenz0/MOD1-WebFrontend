// Account use cases depend on injected adapters, never on HTTP or the DOM.
export class AccountError extends Error {
  constructor(kind) {
    super(kind === "cancelled" ? "A solicitação foi cancelada."
      : "Sua sessão terminou. Entre novamente para continuar.");
    this.name = "AccountError";
    this.kind = kind;
  }
}

export function createAccountApplication({ api, session }) {
  let generation = 0;
  let authenticating = false;
  let refreshPromise = null, challenge = null;

  function ensure(current, signal, requireSession = false) {
    if (current !== generation || signal?.aborted) throw new AccountError("cancelled");
    if (requireSession && !session.isActive()) throw new AccountError("unauthorized");
  }

  function logout() {
    const previousToken = session.getRequestToken();
    generation += 1;
    authenticating = false;
    challenge = null;
    refreshPromise = null;
    session.clear();
    // Revocation is best effort; local secrets are already gone even if HTTP fails.
    if (previousToken && api?.logout) Promise.resolve().then(() => api.logout(previousToken)).catch(() => {});
  }

  async function completeLogin(response, current, signal) {
    ensure(current, signal);
    session.start(response);
    authenticating = true;
    ensure(current, signal, true);
    const user = await api.getMe(session.getToken(), { signal });
    ensure(current, signal, true);
    authenticating = false;
    challenge = null;
    return user;
  }

  function refresh({ signal } = {}) {
    if (signal?.aborted) return Promise.reject(new AccountError("cancelled"));
    if (refreshPromise) return refreshPromise;
    const current = generation, credential = session.getRefreshToken();
    if (!credential) return Promise.reject(new AccountError("unauthorized"));
    const pending = (async () => {
      try {
        // Rotation belongs to the account, not the first requesting view.
        // Once the server consumes a refresh, navigation must keep its successor.
        ensure(current);
        const response = await api.refresh(credential);
        ensure(current);
        if (!session.isSessionAlive()) throw new AccountError("unauthorized");
        session.start(response);
        return response;
      } catch (error) {
        if (current === generation && error.kind === "unauthorized") logout();
        throw error;
      }
    })();
    refreshPromise = pending;
    const release = () => { if (refreshPromise === pending) refreshPromise = null; };
    pending.then(release, release);
    return pending;
  }

  async function accessToken({ signal } = {}) {
    const current = generation;
    ensure(current, signal);
    if (session.shouldRefresh()) await refresh({ signal });
    ensure(current, signal);
    const token = session.getToken();
    if (!token) throw new AccountError("unauthorized");
    return token;
  }

  return {
    logout,
    refresh,
    accessToken,
    async recordActivity({ signal } = {}) {
      const current = generation;
      const token = await accessToken({ signal });
      const result = await api.activity(token, { signal });
      ensure(current, signal);
      session.updateActivity(result);
      return result;
    },
    isAuthenticating: () => authenticating,
    async login(email, password, { signal } = {}) {
      const current = ++generation;
      authenticating = false;
      challenge = null;
      session.clear();
      try {
        ensure(current, signal);
        const response = await api.login(email, password, { signal });
        ensure(current, signal);
        if (response.mfa_required === true) {
          challenge = { token: response.challenge_token, generation: current };
          return response;
        }
        return await completeLogin(response, current, signal);
      } catch (error) {
        if (current === generation) {
          authenticating = false;
          session.clear();
        }
        throw error;
      }
    },
    async verifyMfa(code, { recovery = false, signal } = {}) {
      const pending = challenge;
      if (!pending) throw new AccountError("unauthorized");
      ensure(pending.generation, signal);
      const response = await api.verifyMfa(pending.token, code, { recovery, signal });
      return completeLogin(response, pending.generation, signal);
    },
    async currentUser({ signal } = {}) {
      const current = generation;
      ensure(current, signal);
      // A null token intentionally reaches the protected endpoint for the
      // public "Verificar acesso" demonstration.
      if (session.shouldRefresh()) await refresh({ signal });
      const user = await api.getMe(session.getToken(), { signal });
      ensure(current, signal, true);
      return user;
    },
    register(name, email, password, { signal } = {}) {
      return api.register(name, email, password, { signal });
    },
    async changePassword(currentPassword, newPassword, { signal } = {}) {
      const current = generation;
      const token = await accessToken({ signal });
      ensure(current, signal, true);
      await api.changePassword(token, currentPassword, newPassword, { signal });
      ensure(current, signal);
      logout();
    },
  };
}
