const messages = {
  credentials: "E-mail ou senha inválidos. Confira os dados e tente novamente.",
  unauthorized: "Sua sessão terminou. Entre novamente para continuar.",
  validation: "Confira os dados informados e tente novamente.",
  unavailable: "O serviço está indisponível no momento. Tente novamente em instantes.",
  network: "Não foi possível conectar ao serviço. Confira a conexão e tente novamente.",
  timeout: "O serviço demorou para responder. Tente novamente.",
  "invalid-response": "Não foi possível confirmar os dados recebidos. Tente novamente.",
  cancelled: "A solicitação foi cancelada.",
  "password-rejected": "Não foi possível alterar a senha. Confira a senha atual e escolha uma nova senha diferente.",
};

export class ApiError extends Error {
  constructor(kind) {
    super(messages[kind]);
    this.name = "ApiError";
    this.kind = kind;
  }
}

export function isTokenResponse(value) {
  return value !== null && typeof value === "object"
    && typeof value.access_token === "string" && value.access_token.trim().length > 0
    && value.token_type === "bearer" && typeof value.expires_in === "number"
    && Number.isFinite(value.expires_in) && value.expires_in > 0
    && value.expires_in <= Number.MAX_SAFE_INTEGER / 1000;
}

function isIdentity(value) {
  const uuid = /^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i;
  return value !== null && typeof value === "object"
    && typeof value.id === "string" && uuid.test(value.id)
    && typeof value.email === "string" && value.email.trim().length > 0
    && typeof value.display_name === "string" && value.display_name.trim().length > 0
    && value.is_active === true && typeof value.created_at === "string"
    && Number.isFinite(Date.parse(value.created_at));
}

function isProfile(value, userId) {
  if (!value || typeof value !== "object" || value.user_id !== userId
      || typeof value.summary !== "string" || Array.from(value.summary).length > 2000
      || !["not_informed", "junior", "mid", "senior", "lead"].includes(value.seniority)
      || !Number.isInteger(value.weekly_availability_hours) || value.weekly_availability_hours < 0
      || value.weekly_availability_hours > 168 || !Array.isArray(value.skills) || value.skills.length > 30) return false;
  const names = new Set();
  return value.skills.every(skill => {
    if (!skill || typeof skill.name !== "string" || !skill.name.trim() || Array.from(skill.name).length > 80
        || !Number.isInteger(skill.level) || skill.level < 1 || skill.level > 5) return false;
    const name = skill.name.normalize("NFC").trim().toLowerCase();
    if (names.has(name)) return false;
    names.add(name); return true;
  });
}

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
      if (path === "/auth/password" && response.status === 204) return null;
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
      return request("/auth/password-policy", { method: "GET" }, value => value !== null
        && typeof value === "object" && Number.isInteger(value.min_length)
        && value.min_length >= 12 && value.min_length <= 128 && value.max_length === 128, signal);
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
      }, (value) => value !== null && typeof value === "object"
        && typeof value.message === "string" && value.message.length > 0, signal);
    },
    login(email, password, { signal } = {}) {
      return request("/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email, password }),
      }, isTokenResponse, signal);
    },
    getMe(token, { signal } = {}) {
      return request("/auth/me", {
        method: "GET", headers: token ? { Authorization: `Bearer ${token}` } : {},
      }, isIdentity, signal);
    },
  };
}
