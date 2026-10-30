import { ProjectsApiError } from "./projects-api.js";
import { PERMISSIONS, PERMISSION_NAMES, ROLE_NAMES, permissionsFor } from "./permissions.js";

const byId = id => document.getElementById(id);
const roleKeys = ["product_owner", "project_manager", "developer"];
const uuid = /^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i;
function message(id, text = "", error = false) {
  const node = byId(id); node.textContent = text; node.hidden = !text; node.dataset.tone = error ? "error" : "notice";
}
function checkedRoles(prefix) { return roleKeys.filter(role => byId(`${prefix}-${role}`).checked); }
function fillRoles(prefix, roles) { roleKeys.forEach(role => { byId(`${prefix}-${role}`).checked = roles.includes(role); }); }
function expiry(input) {
  if (!input.value) return null;
  const date = new Date(input.value);
  if (!Number.isFinite(date.valueOf()) || date.valueOf() <= Date.now()) throw new Error("Informe uma data de expiração futura ou deixe o campo vazio.");
  return date.toISOString();
}
function localDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  return new Date(date.valueOf() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

export function createInvitationsController({ api, getToken, onUnauthorized }) {
  let generation = 0, controller = null, busy = false;
  const form = byId("invitation-action-form");
  function setBusy(value) {
    busy = value; form.setAttribute("aria-busy", String(value));
    for (const element of form.elements) element.disabled = value;
  }
  function clear() {
    generation += 1; controller?.abort(); controller = null; form.reset(); setBusy(false); message("invitation-status");
  }
  async function consume(accept) {
    if (busy) return;
    const code = byId("invitation-code").value.trim(), token = getToken();
    if (!token) { clear(); onUnauthorized(); return; }
    if (!code || code.length > 512) { message("invitation-status", "Informe o código recebido do gestor do projeto.", true); return; }
    const current = ++generation; controller = new AbortController();
    const valid = () => current === generation && token === getToken() && !byId("profile-view").hidden;
    setBusy(true); message("invitation-status", "Conferindo convite…");
    try {
      if (accept) await api.acceptInvitation(token, code, { signal: controller.signal });
      else await api.declineInvitation(token, code, { signal: controller.signal });
      if (!valid()) return;
      form.reset(); message("invitation-status", accept ? "Convite aceito. Abra Meus projetos para acessar o trabalho compartilhado." : "Convite recusado. Nenhum acesso foi concedido.");
    } catch (error) {
      if (!valid() || error.kind === "cancelled") return;
      if (error.kind === "unauthorized") { clear(); onUnauthorized(); return; }
      const text = error.kind === "not-found" ? "Este convite não está disponível para sua conta. Ele pode ter expirado ou já ter sido utilizado."
        : error instanceof ProjectsApiError ? error.message : "Não foi possível conferir o convite. Tente novamente.";
      message("invitation-status", text, true);
    } finally { if (current === generation) { controller = null; setBusy(false); } }
  }
  form.addEventListener("submit", event => { event.preventDefault(); consume(true); });
  byId("invitation-decline").addEventListener("click", () => consume(false));
  return { clear };
}

export function createMembersController({ api, getToken, getUserId, onUnauthorized, onSelfChange, onAccessChange }) {
  let generation = 0, controller = null, busy = false, project = null, selected = null;
  let page = { items: [], total: 0, limit: 20, offset: 0 }, manage = false;
  let catalog = [];
  const inviteForm = byId("project-invite-form"), editForm = byId("member-edit-form");
  function setBusy(value) {
    busy = value;
    for (const form of [inviteForm, editForm]) {
      form.setAttribute("aria-busy", String(value));
      for (const element of form.elements) element.disabled = value || !manage;
    }
    byId("members-refresh").disabled = value;
    byId("members-previous").disabled = value || page.offset === 0;
    byId("members-next").disabled = value || page.offset + page.limit >= page.total;
    for (const button of byId("members-list").querySelectorAll("button")) button.disabled = value;
  }
  function clear() {
    generation += 1; controller?.abort(); controller = null; project = null; selected = null; manage = false;
    catalog = [];
    page = { items: [], total: 0, limit: 20, offset: 0 };
    inviteForm.reset(); editForm.reset(); editForm.hidden = true; byId("members-panel").hidden = true;
    byId("generated-invite-code").value = ""; byId("generated-invite").hidden = true;
    byId("members-list").replaceChildren(); byId("members-count").textContent = ""; message("members-status"); setBusy(false);
  }
  function render(value) {
    page = value; const list = byId("members-list"); list.replaceChildren();
    for (const member of value.items) {
      const row = document.createElement("li"), id = document.createElement("strong"), roles = document.createElement("p"), until = document.createElement("p");
      id.textContent = member.user_id;
      roles.textContent = member.roles.length ? member.roles.map(key => ROLE_NAMES[key] || key).join(" · ") : "Sem papéis — sem acesso";
      until.className = "field-hint";
      const expired = member.expires_at !== null && Date.parse(member.expires_at) <= Date.now();
      until.textContent = member.is_owner ? "Responsável protegido" : member.expires_at
        ? `${expired ? "Acesso expirado em" : "Acesso até"} ${new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(member.expires_at))}` : "Sem data de expiração";
      row.append(id, roles, until);
      const actions = member.is_owner ? PERMISSIONS : expired ? [] : [...new Set(member.roles.flatMap(key => catalog.find(role => role.key === key)?.permissions || []))];
      const permissions = document.createElement("p"); permissions.className = "field-hint";
      permissions.textContent = actions.length ? `Permissões: ${actions.map(key => PERMISSION_NAMES[key]).join(" · ")}` : "Sem permissões neste projeto.";
      row.append(permissions);
      if (manage && !member.is_owner) {
        const button = document.createElement("button"); button.type = "button"; button.className = "text-button"; button.textContent = "Editar acessos";
        button.setAttribute("aria-label", `Editar acessos de ${member.user_id}`);
        button.addEventListener("click", () => {
          if (busy) return;
          selected = member; fillRoles("member-role", member.roles);
          byId("member-expiry").value = localDate(member.expires_at);
          byId("member-edit-user").textContent = member.user_id; editForm.hidden = false; byId("member-edit-title").focus();
        });
        row.append(button);
      }
      list.append(row);
    }
    byId("members-count").textContent = `${value.total} integrante${value.total === 1 ? "" : "s"}`;
  }
  async function run(action, onSuccess, confirmed = () => "") {
    const token = getToken(), projectId = project?.id;
    if (!token) { clear(); onUnauthorized(); return; }
    if (!projectId) return;
    const current = ++generation; controller?.abort(); controller = new AbortController();
    const { signal } = controller;
    const valid = () => current === generation && token === getToken() && projectId === project?.id && !byId("projects-view").hidden;
    setBusy(true); message("members-status", "Conferindo acessos…");
    try {
      const result = await action(token, projectId, signal);
      if (valid()) { message("members-status"); await onSuccess(result, { token, projectId, signal, valid }); }
    } catch (error) {
      if (!valid() || error.kind === "cancelled") return;
      if (error.kind === "unauthorized") { const notice = confirmed(); clear(); onUnauthorized(notice); return; }
      if (error.kind === "forbidden" || error.kind === "not-found") {
        manage = false; selected = null; inviteForm.hidden = true; editForm.hidden = true; editForm.reset();
        byId("generated-invite-code").value = ""; byId("generated-invite").hidden = true;
        page = { items: [], total: 0, limit: 20, offset: 0 }; render(page); onAccessChange?.([]);
      }
      message("members-status", confirmed() + (error instanceof ProjectsApiError ? error.message : "Não foi possível carregar os acessos. Tente novamente."), true);
    } finally { if (current === generation) { controller = null; setBusy(false); } }
  }
  function load(offset = 0) {
    return run((token, id, signal) => Promise.all([api.get(token, id, { signal }), api.roles(token, id, { signal }),
      api.members(token, id, { offset, signal })]), ([currentProject, roles, members]) => {
      project = { ...currentProject, permissions: permissionsFor(currentProject, getUserId()) };
      manage = project.permissions.includes("project:members:manage"); inviteForm.hidden = !manage;
      if (!manage) {
        selected = null; editForm.hidden = true; editForm.reset();
        byId("generated-invite-code").value = ""; byId("generated-invite").hidden = true;
      }
      onAccessChange?.(project.permissions);
      catalog = roles.items; render(members);
    });
  }
  inviteForm.addEventListener("submit", event => {
    event.preventDefault(); if (busy || !manage) return;
    byId("generated-invite-code").value = ""; byId("generated-invite").hidden = true;
    const user_id = byId("invite-user-id").value.trim(), roles = checkedRoles("invite-role");
    if (!uuid.test(user_id) || !roles.length) { message("members-status", "Informe um ID de conta válido e selecione ao menos um papel.", true); return; }
    let expires_at;
    try { expires_at = expiry(byId("invite-member-expiry")); } catch (error) { message("members-status", error.message, true); return; }
    run((token, id, signal) => api.invite(token, id, { user_id, roles, expires_at }, { signal }), invitation => {
      byId("generated-invite-code").value = invitation.code; byId("generated-invite").hidden = false;
      const deadline = Math.min(Date.parse(invitation.code_expires_at), invitation.expires_at ? Date.parse(invitation.expires_at) : Infinity);
      byId("generated-invite-expiry").textContent = `Aceite disponível até ${new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(deadline))}. Compartilhe somente com a pessoa convidada.`;
      message("members-status", "Convite criado. Compartilhe o código com a conta indicada.");
    });
  });
  editForm.addEventListener("submit", event => {
    event.preventDefault(); if (busy || !manage || !selected) return;
    const change = { roles: checkedRoles("member-role") };
    if (byId("member-expiry").value !== localDate(selected.expires_at)) {
      try { change.expires_at = expiry(byId("member-expiry")); } catch (error) { message("members-status", error.message, true); return; }
    }
    const target = selected.user_id; let saved = false;
    run((token, id, signal) => api.updateMember(token, id, target, change, { signal }), async (_, ctx) => {
      saved = true; selected = null; editForm.hidden = true; editForm.reset();
      if (onSelfChange && await onSelfChange(target)) return;
      const list = await api.members(ctx.token, ctx.projectId, { signal: ctx.signal });
      if (ctx.valid()) { render(list); message("members-status", "Acessos atualizados. As novas permissões já se aplicam às próximas operações."); }
    }, () => saved ? "Acessos atualizados. " : "");
  });
  byId("member-remove").addEventListener("click", () => {
    if (busy || !manage || !selected || !window.confirm("Remover este integrante do projeto? As próximas operações perderão o acesso.")) return;
    const target = selected.user_id; let removed = false;
    run((token, id, signal) => api.removeMember(token, id, target, { signal }), async (_, ctx) => {
      removed = true; selected = null; editForm.hidden = true; editForm.reset();
      if (onSelfChange && await onSelfChange(target)) return;
      const list = await api.members(ctx.token, ctx.projectId, { signal: ctx.signal });
      if (ctx.valid()) { render(list); message("members-status", "Integrante removido. O acesso foi revogado para as próximas operações."); }
    }, () => removed ? "Integrante removido. " : "");
  });
  byId("member-edit-cancel").addEventListener("click", () => { if (!busy) { editForm.hidden = true; editForm.reset(); selected = null; } });
  byId("members-close").addEventListener("click", () => { clear(); byId("project-members").focus(); });
  byId("members-refresh").addEventListener("click", () => { if (!busy) load(page.offset); });
  byId("members-previous").addEventListener("click", () => { if (!busy) load(Math.max(0, page.offset - 20)); });
  byId("members-next").addEventListener("click", () => { if (!busy) load(page.offset + 20); });
  return { clear, open(value) {
    clear(); project = value;
    inviteForm.hidden = !manage; byId("members-panel").hidden = false; byId("members-title").focus();
    fillRoles("invite-role", ["developer"]); return load(0);
  } };
}
