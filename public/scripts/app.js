import { API_BASE_URL, PROJECTS_API_BASE_URL } from "../config.js";
import { ApiError, createApiClient } from "./api.js";
import { createSession } from "./session.js";
import { createProjectsApiClient } from "./projects-api.js";
import { createProjectsController } from "./projects.js";
import { createFormValidation, emailError, loginPasswordError, nameError,
  newPasswordError, confirmationError } from "./validation.js";

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
let projects;
let projectsConfigurationFailed = false;
try {
  projects = createProjectsController({ api: createProjectsApiClient({ baseUrl: PROJECTS_API_BASE_URL }),
    getToken: () => session.getToken(),
    onUnauthorized: () => endSession("Sua sessão terminou. Entre novamente para continuar."),
    onBack: () => { byId("profile-view").hidden = false; byId("profile-title").focus(); },
  });
} catch { projectsConfigurationFailed = true; }
const loginValidation = createFormValidation("login-form", {
  email: emailError, password: loginPasswordError,
});
const registerValidation = createFormValidation("register-form", {
  "register-name": nameError, "register-email": emailError,
  "register-password": newPasswordError, "register-confirm": confirmationError,
});

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
  for (const id of ["login-button", "refresh-button", "register-button", "access-button", "open-register", "back-login", "open-projects"]) byId(id).disabled = value;
  byId("login-label").textContent = value && view === "login" ? "Entrando…" : "Entrar";
  byId("login-form").setAttribute("aria-busy", String(value && view === "login"));
  byId("login-progress").textContent = value && view === "login" ? "Confirmando seu acesso." : "";
  byId("refresh-button").textContent = value && view === "profile" ? "Atualizando…" : "Atualizar dados";
  if (value && view === "profile") byId("profile-progress").textContent = "Atualizando os dados da sua conta.";
  byId("register-button").textContent = value && view === "register" ? "Cadastrando…" : "Cadastrar";
  byId("register-form").setAttribute("aria-busy", String(value && view === "register"));
  byId("register-progress").textContent = value && view === "register" ? "Preparando sua conta." : "";
  byId("access-button").textContent = value && view === "access" ? "Verificando…" : "Verificar acesso";
}

function accessResult(state, title, detail) {
  byId("access-result").dataset.state = state;
  byId("access-state").textContent = title;
  byId("access-detail").textContent = detail;
}

function clearRegistrationSecrets() {
  byId("register-password").value = "";
  byId("register-confirm").value = "";
  byId("register-password").type = "password";
  byId("register-password-toggle").textContent = "Mostrar";
  byId("register-password-toggle").setAttribute("aria-pressed", "false");
  byId("register-password-toggle").setAttribute("aria-label", "Mostrar senha de cadastro");
}

function showLogin() {
  byId("register-view").hidden = true;
  byId("profile-view").hidden = true;
  byId("login-view").hidden = false;
  clearRegistrationSecrets();
  registerValidation.clear();
  byId("login-title").focus();
}

byId("open-register").addEventListener("click", () => {
  if (busy) return;
  byId("password").value = "";
  passwordHidden();
  message("register");
  registerValidation.clear();
  byId("login-view").hidden = true;
  byId("register-view").hidden = false;
  byId("register-title").focus();
});
byId("back-login").addEventListener("click", () => { if (!busy) showLogin(); });
byId("register-password-toggle").addEventListener("click", () => {
  const reveal = byId("register-password").type === "password";
  byId("register-password").type = reveal ? "text" : "password";
  byId("register-password-toggle").textContent = reveal ? "Ocultar" : "Mostrar";
  byId("register-password-toggle").setAttribute("aria-pressed", String(reveal));
  byId("register-password-toggle").setAttribute("aria-label", `${reveal ? "Ocultar" : "Mostrar"} senha de cadastro`);
});

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
  projects?.clear();
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
  byId("register-view").hidden = true;
  clearRegistrationSecrets();
  accessResult("idle", "Acesso ainda não verificado", "Sua sessão foi encerrada. Verifique novamente para conferir o bloqueio.");
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
  projects?.close();
  identity = user;
  byId("profile-title").textContent = `Olá, ${user.display_name}`;
  byId("profile-email").textContent = user.email;
  byId("profile-created").textContent = new Intl.DateTimeFormat("pt-BR", { dateStyle: "long" }).format(new Date(user.created_at));
  byId("avatar").textContent = user.display_name.trim().split(/\s+/).slice(0, 2).map((part) => Array.from(part)[0]).join("").toLocaleUpperCase("pt-BR");
  byId("login-view").hidden = true;
  byId("profile-view").hidden = false;
  byId("register-view").hidden = true;
  accessResult("allowed", "Acesso permitido", "Sua identidade foi confirmada. Você pode consultar os dados da sua conta.");
}

byId("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  if (!loginValidation.validate()) {
    message("login", "Confira os campos destacados para continuar.");
    return;
  }
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
byId("projects-logout").addEventListener("click", () => endSession("Você saiu da sua conta."));
byId("open-projects").addEventListener("click", () => {
  if (!checkExpiry() || busy || !identity) return;
  if (projectsConfigurationFailed) {
    message("profile", "O serviço de projetos não está configurado. Informe o responsável do módulo.");
    return;
  }
  byId("profile-view").hidden = true;
  projects.open();
});

byId("register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  if (!registerValidation.validate()) {
    message("register", "Confira os campos destacados para criar sua conta.");
    return;
  }
  if (apiConfigurationFailed) {
    message("register", "O serviço não está configurado. Informe o responsável do módulo.");
    return;
  }
  const current = ++epoch;
  controller = new AbortController();
  const email = byId("register-email").value;
  message("register");
  setBusy(true, "register");
  try {
    await api.register(byId("register-name").value, email, byId("register-password").value, { signal: controller.signal });
    if (current !== epoch) return;
    byId("email").value = email;
    loginValidation.clear();
    byId("register-form").reset();
    showLogin();
    message("login", "Cadastro recebido. Se o e-mail estava disponível, sua conta já está pronta. Entre para continuar.", "notice");
  } catch (error) {
    if (current !== epoch) return;
    if (error.kind !== "cancelled") message("register", error instanceof ApiError ? error.message : "Não foi possível cadastrar. Tente novamente.");
  } finally {
    if (current === epoch) { controller = null; setBusy(false, "register"); }
  }
});

byId("access-button").addEventListener("click", async () => {
  if (busy) return;
  checkExpiry();
  if (apiConfigurationFailed) {
    accessResult("unavailable", "Não foi possível verificar", "O serviço não está configurado. Informe o responsável do módulo.");
    return;
  }
  const current = ++epoch;
  controller = new AbortController();
  setBusy(true, "access");
  accessResult("checking", "Verificando seu acesso…", "Aguardando a confirmação do serviço.");
  try {
    await api.getMe(session.getToken(), { signal: controller.signal });
    if (current !== epoch || !checkExpiry()) return;
    accessResult("allowed", "Acesso permitido", "Sua sessão foi confirmada. Você pode consultar os dados protegidos.");
  } catch (error) {
    if (current !== epoch || error.kind === "cancelled") return;
    if (error.kind === "unauthorized") {
      if (identity) endSession("Sua sessão não permite continuar. Entre novamente.");
      accessResult("blocked", "Acesso bloqueado", "Você precisa entrar com uma conta válida para consultar seus dados.");
    } else {
      accessResult("unavailable", "Não foi possível verificar", error instanceof ApiError ? error.message : "Tente novamente em instantes.");
    }
  } finally {
    if (current === epoch) { controller = null; setBusy(false, "access"); }
  }
});

// Credentials stay inert until all handlers have initialized successfully.
loginValidation.enable();
registerValidation.enable();
for (const id of ["email", "password", "password-toggle", "login-button", "open-register", "back-login", "register-name", "register-email", "register-password", "register-confirm", "register-password-toggle", "register-button", "access-button"]) {
  byId(id).disabled = false;
}
byId("initialization-message").hidden = true;
