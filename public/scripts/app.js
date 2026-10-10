import { API_BASE_URL } from "../config.js";
import { ApiError, createApiClient } from "./api.js";
import { createSession } from "./session.js";

const byId = (id) => document.getElementById(id);
const session = createSession();
let api;
let apiConfigurationFailed = false;
try { api = createApiClient({ baseUrl: API_BASE_URL }); }
catch { apiConfigurationFailed = true; }
let epoch = 0;
let controller = null;
let identity = null;
let busy = false;
let authenticating = false;

const themePreference = matchMedia("(prefers-color-scheme: dark)");
let explicitTheme = false;
export function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  byId("theme-toggle").setAttribute("aria-label", `Ativar tema ${theme === "dark" ? "claro" : "escuro"}`);
  byId("theme-label").textContent = theme === "dark" ? "Tema claro" : "Tema escuro";
}
let savedTheme;
try { savedTheme = localStorage.getItem("mod1-theme"); } catch { /* Theme also works without storage. */ }
explicitTheme = ["light", "dark"].includes(savedTheme);
applyTheme(explicitTheme ? savedTheme : themePreference.matches ? "dark" : "light");
byId("theme-toggle").addEventListener("click", () => {
  const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  explicitTheme = true;
  applyTheme(theme);
  try { localStorage.setItem("mod1-theme", theme); } catch { /* Keep current-tab preference. */ }
});
themePreference.addEventListener("change", (event) => {
  if (!explicitTheme) applyTheme(event.matches ? "dark" : "light");
});

function message(view, text = "", tone = "error") {
  const element = byId(`${view}-message`);
  element.textContent = text;
  element.dataset.tone = tone;
  element.hidden = !text;
}

function setBusy(value, view) {
  busy = value;
  const login = byId("login-button");
  login.disabled = value && view === "login";
  byId("login-label").textContent = login.disabled ? "Entrando…" : "Entrar";
  byId("login-form").setAttribute("aria-busy", String(login.disabled));
  byId("login-progress").textContent = login.disabled ? "Confirmando seu acesso." : "";
  const refresh = byId("refresh-button");
  refresh.disabled = value && view === "profile";
  refresh.textContent = refresh.disabled ? "Atualizando…" : "Atualizar dados";
  if (refresh.disabled) byId("profile-progress").textContent = "Atualizando os dados da sua conta.";
}

function passwordHidden() {
  byId("password").type = "password";
  byId("password-toggle").textContent = "Mostrar";
  byId("password-toggle").setAttribute("aria-label", "Mostrar senha");
  byId("password-toggle").setAttribute("aria-pressed", "false");
}
byId("password-toggle").addEventListener("click", () => {
  if (byId("password").type === "text") return passwordHidden();
  byId("password").type = "text";
  byId("password-toggle").textContent = "Ocultar";
  byId("password-toggle").setAttribute("aria-label", "Ocultar senha");
  byId("password-toggle").setAttribute("aria-pressed", "true");
});

function endSession(text = "", tone = "notice") {
  epoch += 1;
  controller?.abort();
  controller = null;
  session.clear();
  identity = null;
  authenticating = false;
  byId("profile-title").textContent = "";
  byId("profile-email").textContent = "";
  byId("profile-created").textContent = "";
  byId("avatar").textContent = "";
  byId("password").value = "";
  passwordHidden();
  setBusy(false, "login");
  byId("profile-view").hidden = true;
  byId("login-view").hidden = false;
  message("profile");
  byId("profile-progress").textContent = "";
  message("login", text, tone);
  byId("login-title").focus();
}

function checkExpiry() {
  if ((identity || authenticating) && !session.isActive()) {
    endSession("Sua sessão terminou. Entre novamente para continuar.");
    return false;
  }
  return true;
}
document.addEventListener("visibilitychange", checkExpiry);
window.addEventListener("focus", checkExpiry);
window.addEventListener("pageshow", checkExpiry);
setInterval(checkExpiry, 1000);

function renderIdentity(user) {
  identity = user;
  byId("profile-title").textContent = `Olá, ${user.display_name}`;
  byId("profile-email").textContent = user.email;
  byId("profile-created").textContent = new Intl.DateTimeFormat("pt-BR", { dateStyle: "long" }).format(new Date(user.created_at));
  byId("avatar").textContent = user.display_name.trim().split(/\s+/).slice(0, 2).map((part) => Array.from(part)[0]).join("").toLocaleUpperCase("pt-BR");
  byId("login-view").hidden = true;
  byId("profile-view").hidden = false;
}

byId("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  if (apiConfigurationFailed) {
    message("login", "O serviço não está configurado. Informe o responsável do módulo.");
    return;
  }
  const current = ++epoch;
  controller?.abort();
  controller = new AbortController();
  const { signal } = controller;
  message("login");
  setBusy(true, "login");
  try {
    const response = await api.login(byId("email").value, byId("password").value, { signal });
    if (current !== epoch) return;
    session.start(response);
    authenticating = true;
    const user = await api.getMe(session.getToken(), { signal });
    if (current !== epoch || !checkExpiry()) return;
    authenticating = false;
    renderIdentity(user);
    byId("password").value = "";
    passwordHidden();
    message("profile");
    byId("profile-title").focus();
  } catch (error) {
    if (current !== epoch) return;
    session.clear();
    authenticating = false;
    if (error.kind !== "cancelled") message("login", error instanceof ApiError ? error.message : "Não foi possível entrar. Tente novamente.");
  } finally {
    if (current === epoch) { controller = null; setBusy(false, "login"); }
  }
});

byId("refresh-button").addEventListener("click", async () => {
  if (!checkExpiry() || busy || !identity) return;
  const current = ++epoch;
  controller = new AbortController();
  message("profile");
  setBusy(true, "profile");
  try {
    const user = await api.getMe(session.getToken(), { signal: controller.signal });
    if (current !== epoch || !checkExpiry()) return;
    renderIdentity(user);
    byId("profile-progress").textContent = "Dados atualizados.";
  } catch (error) {
    if (current !== epoch) return;
    if (error.kind === "unauthorized") return endSession(error.message);
    if (!checkExpiry()) return;
    byId("profile-progress").textContent = "";
    if (error.kind !== "cancelled") message("profile", error instanceof ApiError ? error.message : "Não foi possível atualizar os dados. Tente novamente.");
  } finally {
    if (current === epoch) { controller = null; setBusy(false, "profile"); }
  }
});
byId("logout-button").addEventListener("click", () => endSession("Você saiu da sua conta."));

// Credentials stay inert until all handlers have initialized successfully.
for (const id of ["email", "password", "password-toggle", "login-button"]) {
  byId(id).disabled = false;
}
byId("initialization-message").hidden = true;
