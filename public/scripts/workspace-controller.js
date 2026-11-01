import { PlatformApiError } from "./api-errors.js";
import { PERMISSIONS, PERMISSION_NAMES, ROLE_NAMES } from "./permissions.js";
import { projectDetails, itemDraft, listValues, decimalValue, PROJECT_STATUSES, MOSCOW, ITEM_KINDS, ITEM_STATUSES } from "./planning-domain.js";
import { el, action, section, form, rows, details, secret, textDate } from "./workspace-view.js";

const roleOptions = { product_owner: "Product Owner", project_manager: "PM/Scrum Master", developer: "Desenvolvedor" };
const pageItems = value => Array.isArray(value) ? value : value?.items || [];
const identityLabel = value => value.display_name || value.user_id || value.id;
const roleLabel = key => ROLE_NAMES[key] || key;

export function createWorkspaceController({ clients, account, session, getIdentity, onEnter, onBack, onUnauthorized }) {
  const root = el("section", null, { id: "workspace-view", class: "workspace-panel", hidden: true, "aria-labelledby": "workspace-title" });
  const header = el("div", null, { class: "projects-heading" }), titles = el("div");
  const heading = el("h1", "", { id: "workspace-title", tabindex: "-1" }), scope = el("p", "", { class: "intro" });
  const back = action("Voltar para minha conta", () => { const target = project; clear(); onBack(target); });
  titles.append(heading, scope); header.append(titles, back);
  const navigation = el("nav", null, { class: "workspace-nav", "aria-label": "Seções do espaço de trabalho" });
  const notice = el("p", "", { id: "workspace-status", class: "message", role: "status", "aria-live": "polite", hidden: true });
  const content = el("div", null, { id: "workspace-content" });
  root.append(header, navigation, notice, content); document.getElementById("main").append(root);
  let generation = 0, controller = null, busy = false, mode = "", tab = "", project = null, selectedTeam = null, selectedItem = null;
  let roleCatalog = [], itemPage = [], boardVersion = 0, itemQuery = {}, adminQuery = "", teamQuery = "";
  const key = () => session.getSessionId() || session.getRequestToken();
  const own = () => Boolean(project && project.owner_id === getIdentity()?.id);
  const can = permission => Boolean(project?.permissions?.includes(permission) || own());
  const writable = () => !project?.archived && ["active", "planned", undefined].includes(project?.status);
  const canWrite = permission => writable() && can(permission);

  function status(text = "", error = false) { notice.textContent = text; notice.hidden = !text; notice.dataset.tone = error ? "error" : "notice"; }
  function setBusy(value) { busy = value; root.setAttribute("aria-busy", String(value)); for (const button of root.querySelectorAll("button")) button.disabled = value; }
  function invalidate() { generation += 1; controller?.abort(); controller = null; busy = false; }
  function clear() {
    invalidate(); root.hidden = true; content.replaceChildren(); navigation.replaceChildren();
    project = selectedTeam = selectedItem = null; roleCatalog = []; itemPage = []; status();
  }
  async function run(work, successText = "") {
    if (busy || root.hidden) return;
    const current = generation, sessionKey = key();
    controller = new AbortController(); const signal = controller.signal;
    const valid = () => current === generation && !root.hidden && key() === sessionKey;
    setBusy(true); status("Carregando…");
    async function request(service, method, path, body, options = {}) {
      const token = await account.accessToken({ signal });
      const value = await clients[service].request(method, path, token, body, { signal, ...options });
      if (!valid()) throw new PlatformApiError("cancelled");
      return value;
    }
    try { await work(request); if (valid()) status(successText); }
    catch (error) {
      if (!valid() || error.kind === "cancelled") return;
      if (error.kind === "unauthorized") { clear(); onUnauthorized(); return; }
      status(error instanceof Error ? error.message : "Não foi possível concluir. Tente novamente.", true);
    } finally { if (valid()) { controller = null; setBusy(false); } }
  }
  function show(title, description, tabs, active) {
    heading.textContent = title; scope.textContent = description;
    navigation.replaceChildren();
    for (const [name, label, callback] of tabs) {
      const button = action(label, callback); button.className = "workspace-tab";
      if (name === active) button.setAttribute("aria-current", "page");
      navigation.append(button);
    }
  }
  function go(next, loader) { invalidate(); tab = next; status(); return loader(); }
  function pagination(page, loader) {
    const list = el("div", null, { class: "projects-pagination" });
    const offset = page.offset || 0, limit = page.limit || 20, total = page.total ?? pageItems(page).length;
    list.append(el("span", total ? `${offset + 1}–${Math.min(total, offset + limit)} de ${total}` : "Nenhum registro"));
    if (offset > 0) list.append(action("Página anterior", () => loader(Math.max(0, offset - limit))));
    if (offset + limit < total) list.append(action("Próxima página", () => loader(offset + limit)));
    return list;
  }
  function auditRows(value) {
    return rows(pageItems(value), [{ label: "Quando", value: row => textDate(row.created_at || row.occurred_at) },
      { label: "Ação", value: row => row.action || row.event_type || row.kind },
      { label: "Responsável", value: row => row.actor_id || row.user_id || "Sistema" },
      { label: "Alteração", value: row => row.summary || row.reason || row.result || formatChanges(row.changes || row.details) }],
      { empty: "Ainda não há eventos registrados neste histórico.", caption: "Histórico de alterações" });
  }
  function formatChanges(changes) {
    if (!changes || typeof changes !== "object") return "Evento registrado";
    return Object.entries(changes).map(([field, change]) => {
      if (change && typeof change === "object" && ("before" in change || "after" in change)) return `${field}: ${String(change.before ?? "vazio")} → ${String(change.after ?? "vazio")}`;
      return `${field}: ${typeof change === "object" ? "atualizado" : String(change)}`;
    }).join("; ");
  }

  function securityNavigation(active) {
    show("Segurança da conta", "Controle os acessos e os fatores de autenticação da sua conta.", [
      ["sessions", "Sessões", () => go("sessions", renderSessions)], ["mfa", "Segundo fator", () => go("mfa", renderMfa)],
      ["email", "E-mail", () => go("email", renderEmail)], ["access-audit", "Histórico de acesso", () => go("access-audit", renderOwnAudit)],
    ], active);
  }
  function renderSessions() {
    securityNavigation("sessions");
    return run(async request => {
      const page = await request("identity", "GET", "/auth/sessions");
      const panel = section("Sessões ativas", "Encerre acessos que você não reconhece. Revogar a sessão atual também encerra este acesso.");
      panel.append(rows(pageItems(page).filter(row => !row.revoked_at), [
        { label: "Dispositivo", value: row => `${row.client_label || "Navegador"}${row.is_current ? " · atual" : ""}` },
        { label: "Iniciada em", value: row => textDate(row.created_at) }, { label: "Última atividade", value: row => textDate(row.last_activity_at) },
      ], { empty: "Nenhuma sessão ativa.", caption: "Sessões da sua conta", actions: row => [action("Revogar", () => run(async req => {
        await req("identity", "DELETE", `/auth/sessions/${row.id}`);
        if (row.is_current || row.id === session.getSessionId()) { clear(); onUnauthorized("Sessão encerrada."); return; }
        const next = await req("identity", "GET", "/auth/sessions");
        // Render the refreshed result after this mutation without starting a nested operation.
        panel.replaceWith(sessionPanel(next));
      }, "Sessão revogada."), { label: `Revogar sessão de ${row.client_label || "Navegador"}` })] }));
      panel.append(action("Encerrar todas as sessões", () => {
        if (confirm("Encerrar todos os acessos da sua conta, incluindo este?")) run(async req => { await req("identity", "POST", "/auth/sessions/revoke-all", {}); clear(); onUnauthorized("Todas as sessões foram encerradas."); });
      }));
      content.replaceChildren(panel);
    });
  }
  function sessionPanel(page) {
    const panel = section("Sessões ativas", "A lista reflete as sessões ainda válidas.");
    panel.append(rows(pageItems(page).filter(row => !row.revoked_at), [{ label: "Dispositivo", value: row => row.client_label || "Navegador" },
      { label: "Última atividade", value: row => textDate(row.last_activity_at) }], { caption: "Sessões ativas", actions: row => [action("Revogar", () => run(async req => {
        await req("identity", "DELETE", `/auth/sessions/${row.id}`);
        if (row.is_current || row.id === session.getSessionId()) { clear(); onUnauthorized(); return; }
        panel.replaceWith(sessionPanel(await req("identity", "GET", "/auth/sessions")));
      }, "Sessão revogada."), { label: `Revogar sessão de ${row.client_label || "Navegador"}` })] })); return panel;
  }
  function renderMfa() {
    securityNavigation("mfa");
    return run(async request => {
      const state = await request("identity", "GET", "/auth/mfa");
      const panel = section("Autenticação em duas etapas", state.enabled ? "O segundo fator está ativo na sua conta." : "Proteja sua conta com um aplicativo autenticador compatível com códigos temporários.");
      if (!state.enabled) {
        const setup = form("mfa-setup", [{ name: "password", label: "Senha atual para configurar o segundo fator", type: "password", required: true, autocomplete: "current-password" }], "Configurar segundo fator", values => run(async req => {
          const enrollment = await req("identity", "POST", "/auth/mfa/setup", values); setup.reset();
          const information = secret(enrollment.secret, "Chave de configuração");
          const enable = form("mfa-enable", [{ name: "code", label: "Código do aplicativo autenticador", required: true, autocomplete: "one-time-code", hint: "Digite os seis números exibidos no aplicativo." }], "Ativar segundo fator", data => run(async next => {
            const reply = await next("identity", "POST", "/auth/mfa/enable", data);
            content.replaceChildren(secret(reply.recovery_codes, "Códigos de recuperação"));
          }, "Segundo fator ativado. Guarde os códigos de recuperação."));
          panel.append(information, enable.node);
        }, "Adicione a chave ao autenticador e confirme o primeiro código.")); panel.append(setup.node);
      } else {
        const fields = [{ name: "password", label: "Senha atual para gerenciar o segundo fator", type: "password", required: true },
          { name: "code", label: "Código do segundo fator", required: true, autocomplete: "one-time-code" }];
        const recovery = form("mfa-recovery", fields, "Gerar novos códigos de recuperação", values => run(async req => {
          const reply = await req("identity", "POST", "/auth/mfa/recovery-codes", values); recovery.reset();
          panel.append(secret(reply.recovery_codes, "Novos códigos de recuperação"));
        }, "Os códigos anteriores foram substituídos."));
        panel.append(recovery.node, action("Desativar segundo fator", () => {
          if (confirm("Desativar a proteção por segundo fator?")) run(async req => { await req("identity", "POST", "/auth/mfa/disable", recovery.values()); recovery.reset(); content.replaceChildren(section("Segundo fator desativado", "Você pode configurar um novo aplicativo quando desejar.")); });
        }));
      }
      content.replaceChildren(panel);
    });
  }
  function renderEmail() {
    securityNavigation("email");
    const user = getIdentity();
    const panel = section("Confirmação de e-mail", user?.email_verified ? "Seu endereço de e-mail está confirmado." : "Confirme que você tem acesso à caixa de entrada informada no cadastro.");
    panel.append(details({ "Endereço da conta": user?.email, "Situação": user?.email_verified ? "Confirmado" : "Aguardando confirmação" }));
    if (!user?.email_verified) panel.append(action("Enviar link de confirmação", () => run(async request => { await request("identity", "POST", "/auth/email/request", {}); }, "Se houver um envio disponível, confira a caixa de entrada e a pasta de spam.")));
    content.replaceChildren(panel); return Promise.resolve();
  }
  function renderOwnAudit(offset = 0) {
    securityNavigation("access-audit");
    return run(async request => { const page = await request("identity", "GET", `/auth/audit?limit=20&offset=${offset}`);
      const panel = section("Histórico de acesso", "Eventos de autenticação e segurança da sua conta."); panel.append(auditRows(page), pagination(page, renderOwnAudit)); content.replaceChildren(panel); });
  }

  function adminNavigation(active) {
    show("Administração", "Operações restritas à administração do sistema. Papéis de projeto não concedem esse acesso.", [
      ["users", "Contas", () => go("users", renderAdmin)], ["audit", "Auditoria", () => go("audit", renderAdminAudit)],
      ["mailbox", "Caixa postal local", () => go("mailbox", renderMailbox)], ["anomalies", "Análise de acessos", () => go("anomalies", () => renderRecommendations("identity"))],
    ], active);
  }
  function renderAdmin(offset = 0) {
    adminNavigation("users");
    return run(async request => {
      const page = await request("identity", "GET", `/admin/users?limit=20&offset=${offset}&q=${encodeURIComponent(adminQuery)}`);
      const panel = section("Contas da plataforma", "Bloqueios temporários, situação das contas e sessões são controles independentes.");
      const search = form("admin-search", [{ name: "q", label: "Buscar contas", value: adminQuery }], "Buscar contas", values => { adminQuery = values.q; go("users", renderAdmin); });
      panel.append(search.node, rows(pageItems(page), [{ label: "Pessoa", value: identityLabel }, { label: "E-mail", key: "email" },
        { label: "Situação", value: row => row.is_active ? "Ativa" : "Desativada" }], { caption: "Contas", actions: row => [
          action("Desbloquear", () => run(async req => { await req("identity", "POST", `/admin/users/${row.id}/unlock`, {}); }, "Bloqueio temporário removido.")),
          action("Revogar sessões", () => run(async req => { await req("identity", "POST", `/admin/users/${row.id}/revoke-sessions`, {}); }, "Sessões revogadas.")),
          action(row.is_active ? "Desativar conta" : "Reativar conta", () => {
            if (confirm(`${row.is_active ? "Desativar" : "Reativar"} esta conta?`)) run(async req => { await req("identity", "PATCH", `/admin/users/${row.id}`, { is_active: !row.is_active });
              row.is_active = !row.is_active; if (row.id === getIdentity()?.id && !row.is_active) { clear(); onUnauthorized(); } }, "Situação da conta atualizada. Atualize a lista para conferir.");
          }),
        ] }), pagination(page, renderAdmin));
      const create = form("admin-create", [{ name: "display_name", label: "Nome do colaborador", required: true }, { name: "email", label: "E-mail do colaborador", type: "email", required: true }], "Convidar colaborador", values => run(async req => {
        await req("identity", "POST", "/admin/users", values); create.reset();
      }, "Solicitação registrada. O colaborador define a própria senha pelo convite."));
      const revoke = form("admin-token", [{ name: "jti", label: "Identificador do token comprometido", required: true, hint: "Informe o identificador jti, nunca o token completo." }], "Revogar token", values => run(async req => { await req("identity", "POST", "/admin/tokens/revoke", values); revoke.reset(); }, "Token revogado."));
      panel.append(section("Convidar novo colaborador"), create.node, section("Token comprometido"), revoke.node); content.replaceChildren(panel);
    });
  }
  function renderAdminAudit(offset = 0) { adminNavigation("audit"); return run(async request => {
    const page = await request("identity", "GET", `/admin/audit?limit=20&offset=${offset}`); const panel = section("Auditoria de segurança");
    panel.append(auditRows(page), pagination(page, renderAdminAudit)); content.replaceChildren(panel);
  }); }
  function renderMailbox() { adminNavigation("mailbox"); return run(async request => {
    const page = await request("identity", "GET", "/admin/mailbox");
    const panel = section("Caixa postal local", "Disponível somente no ambiente local habilitado para testes. Estas mensagens não foram enviadas a caixas externas.");
    for (const message of pageItems(page)) {
      const entry = section(message.subject, `${message.to} · ${textDate(message.created_at)}`);
      entry.append(el("p", message.body, { class: "preserve-lines" }));
      const links = String(message.body).match(/https?:\/\/[^\s<>]+/g) || [];
      for (const link of links) {
        try { const target = new URL(link); if (target.origin === location.origin && /^#(?:recovery|verify-email)=/.test(target.hash)) entry.append(el("a", "Abrir link da mensagem", { href: target.href, class: "text-button" })); } catch { /* A malformed message never creates a link. */ }
      }
      panel.append(entry);
    }
    if (!pageItems(page).length) panel.append(el("p", "Nenhuma mensagem local recebida.")); content.replaceChildren(panel);
  }); }

  function teamsNavigation(active) {
    show("Equipes e alocação", "Organize os grupos de trabalho e acompanhe sua capacidade semanal.", [
      ["teams", "Minhas equipes", () => go("teams", renderTeams)], ["allocation", "Minha alocação", () => go("allocation", renderAllocation)],
    ], active);
  }
  function renderNotifications(offset = 0) {
    show("Notificações", "Mensagens sobre sua participação em equipes e projetos.", [], "notifications");
    return run(async request => {
      const page = await request("projects", "GET", `/notifications?limit=20&offset=${offset}`);
      const panel = section("Minha caixa de entrada");
      panel.append(rows(pageItems(page), [{ label: "Quando", value: row => textDate(row.created_at) },
        { label: "Assunto", key: "title" }, { label: "Mensagem", key: "message" },
        { label: "Situação", value: row => row.read_at ? "Lida" : "Não lida" }], { caption: "Minhas notificações",
        actions: row => row.read_at ? [] : [action("Marcar como lida", () => run(async req => {
          await req("projects", "POST", `/notifications/${row.id}/read`, {});
        }, "Mensagem marcada como lida. Atualize para conferir."))] }), pagination(page, renderNotifications),
        action("Atualizar notificações", () => go("notifications", () => renderNotifications(offset))));
      content.replaceChildren(panel);
    });
  }
  function renderTeams(offset = 0) { teamsNavigation("teams"); return run(async request => {
    const page = await request("projects", "GET", `/teams?limit=20&offset=${offset}&q=${encodeURIComponent(teamQuery)}`);
    const panel = section("Minhas equipes", "As equipes são independentes dos projetos. Cada vínculo tem sua própria autorização.");
    panel.append(rows(pageItems(page), [{ label: "Equipe", value: row => action(row.name, () => openTeam(row)) }, { label: "Centro de custo", key: "cost_center" }, { label: "Descrição", key: "description" }], { caption: "Equipes", empty: "Você ainda não participa de uma equipe. Crie uma ou aceite um convite." }), pagination(page, renderTeams));
    const create = form("team-create", [{ name: "name", label: "Nome da equipe", required: true, maxLength: 120 }, { name: "description", label: "Descrição da equipe", type: "textarea" }, { name: "cost_center", label: "Centro de custo" }], "Criar equipe", values => run(async req => {
      const team = await req("projects", "POST", "/teams", values); create.reset();
      const list = panel.querySelector(".workspace-list");
      const updated = await req("projects", "GET", "/teams?limit=20&offset=0");
      list.replaceWith(rows(pageItems(updated), [{ label: "Equipe", value: row => action(row.name, () => openTeam(row)) }, { label: "Centro de custo", key: "cost_center" }], { caption: "Equipes" }));
      selectedTeam = team;
    }, "Equipe criada."));
    const invitation = form("team-invitation", [{ name: "code", label: "Código de convite de equipe", required: true }], "Aceitar convite de equipe", values => run(async req => {
      await req("projects", "POST", "/team-invitations/accept", values); invitation.reset();
    }, "Convite de equipe aceito. Atualize suas equipes para acessar o grupo."), { secondaryLabel: "Recusar convite de equipe", onSecondary: values => run(async req => {
      await req("projects", "POST", "/team-invitations/decline", values); invitation.reset();
    }, "Convite de equipe recusado.") });
    panel.append(section("Criar equipe"), create.node, section("Convite de equipe", "Este código vincula você à equipe, não apenas a um projeto."), invitation.node);
    content.replaceChildren(panel);
  }); }
  function openTeam(team) { selectedTeam = team; return go("team-detail", renderTeam); }
  function renderTeam() { teamsNavigation("teams"); return run(async request => {
    const team = await request("projects", "GET", `/teams/${selectedTeam.id}`);
    const memberPage = await request("projects", "GET", `/teams/${team.id}/members?limit=100&offset=0`);
    selectedTeam = team;
    const manager = team.owner_id === getIdentity()?.id || pageItems(memberPage).some(row => row.user_id === getIdentity()?.id && row.is_manager);
    const panel = section(team.name, team.description);
    panel.append(details({ "ID da equipe": team.id, "Centro de custo": team.cost_center }), rows(pageItems(memberPage), [{ label: "Integrante", value: identityLabel },
      { label: "Responsabilidade", value: row => row.is_manager || row.user_id === team.owner_id ? "Gestão" : "Integrante" }], { caption: "Integrantes da equipe", actions: manager ? row => row.user_id === team.owner_id ? [] : [action("Remover da equipe", () => {
        if (confirm("Remover esta pessoa da equipe e dos acessos herdados por ela?")) run(async req => { await req("projects", "DELETE", `/teams/${team.id}/members/${row.user_id}`); }, "Integrante removido. Atualize para conferir.");
      })] : undefined }));
    if (manager) {
      const edit = form("team-edit", [{ name: "name", label: "Nome da equipe para edição", value: team.name, required: true }, { name: "description", label: "Descrição da equipe para edição", type: "textarea", value: team.description }, { name: "cost_center", label: "Centro de custo da equipe", value: team.cost_center }], "Salvar equipe", values => run(async req => { selectedTeam = await req("projects", "PATCH", `/teams/${team.id}`, values); }, "Equipe atualizada."));
      const member = form("team-member", [{ name: "user_id", label: "ID da conta para adicionar à equipe", required: true }, { name: "is_manager", label: "Permitir gestão da equipe", type: "checkbox" }], "Adicionar integrante à equipe", values => run(async req => { await req("projects", "POST", `/teams/${team.id}/members`, values); member.reset(); }, "Integrante adicionado. Atualize para conferir."));
      const invite = form("team-invite", [{ name: "user_id", label: "ID da conta convidada para a equipe", required: true }, { name: "is_manager", label: "Convidar para gestão da equipe", type: "checkbox" }], "Gerar convite de equipe", values => run(async req => {
        const result = await req("projects", "POST", `/teams/${team.id}/invitations`, values); invite.reset(); panel.append(secret(result.code, "Código para compartilhar com a pessoa convidada"));
      }, "Convite criado para a conta indicada."));
      panel.append(section("Dados da equipe"), edit.node, section("Adicionar integrante"), member.node, section("Convidar integrante"), invite.node);
    }
    panel.append(action("Atualizar equipe", () => go("team-detail", renderTeam)), action("Voltar para minhas equipes", () => go("teams", renderTeams))); content.replaceChildren(panel);
  }); }
  function renderAllocation() { teamsNavigation("allocation"); return run(async request => {
    const data = await request("projects", "GET", "/allocations/me");
    const panel = section("Minha alocação", "Horas declaradas e vínculos ativos. A quantidade de projetos não representa carga horária.");
    panel.append(details({ "Disponibilidade semanal": data.weekly_availability_hours !== undefined ? `${data.weekly_availability_hours} h` : "Não informada", "Horas alocadas": data.total_allocated_hours !== undefined ? `${data.total_allocated_hours} h` : "Não informadas" }),
      rows(data.projects || [], [{ label: "Projeto", value: row => row.name || row.project_name || row.project_id }, { label: "Horas por semana", value: row => row.weekly_hours, numeric: true }], { caption: "Alocação em projetos" }),
      rows(data.teams || [], [{ label: "Equipe", value: row => row.name || row.team_name || row.team_id }], { caption: "Vínculos com equipes" })); content.replaceChildren(panel);
  }); }

  function projectNavigation(active) {
    const tabs = [["context", "Contexto", () => go("context", renderProject)], ["board", "Quadro e itens", () => go("board", renderBoard)],
      ["project-teams", "Equipes", () => go("project-teams", renderProjectTeams)]];
    if (can("project:members:read")) tabs.push(["roles", "Papéis e acessos", () => go("roles", renderRoles)]);
    tabs.push(["history", "Histórico", () => go("history", renderProjectHistory)], ["recommendations", "Recomendações", () => go("recommendations", () => renderRecommendations("projects"))]);
    show(project?.name || "Projeto", "Contexto, planejamento e colaboração do projeto.", tabs, active);
  }
  async function refreshProject(request) { project = await request("projects", "GET", `/projects/${project.id}`); return project; }
  function renderProject() { projectNavigation("context"); return run(async request => {
    await refreshProject(request); projectNavigation("context");
    const panel = section("Contexto do projeto", project.description);
    panel.append(details({ "Objetivo": project.objective, "Situação": `${PROJECT_STATUSES[project.status] || "Ativo"}${project.archived ? " · arquivado" : ""}`,
      "Orçamento": project.budget_amount !== null && project.budget_amount !== undefined ? `${project.budget_currency || "BRL"} ${project.budget_amount}` : "Não informado",
      "Etiquetas": project.tags?.join(", "), "Stack": project.technology_stack?.join(", "), "Início previsto": project.planned_start, "Término previsto": project.planned_end }));
    const summary = await request("projects", "GET", `/projects/${project.id}/summary`);
    panel.append(section("Equipe e backlog"), rows(summary.teams || [], [
      { label: "Equipe", value: team => team.name || team.team_name || team.team_id },
      { label: "Papéis", value: team => team.roles?.map(roleLabel).join(", ") },
    ], { caption: "Equipes vinculadas", empty: "Nenhuma equipe vinculada ao projeto." }));
    panel.append(summary.backlog_available && summary.backlog
      ? details({ "Histórias": summary.backlog.stories, "Épicos": summary.backlog.epics, "Tarefas": summary.backlog.tasks })
      : el("p", "O resumo do backlog está indisponível. Tente atualizar o contexto.", { class: "field-hint" }));
    if (can("project:update") && !project.archived && ["planned", "active", undefined].includes(project.status)) {
      const editor = form("project-details", [
        { name: "scope", label: "Escopo detalhado", type: "textarea", value: project.scope, wide: true },
        { name: "budget_amount", label: "Orçamento disponível", value: project.budget_amount, hint: "Valor decimal, sem separador de milhar." },
        { name: "budget_currency", label: "Moeda do orçamento", type: "select", value: project.budget_currency || "BRL", options: { BRL: "Real · BRL", USD: "Dólar · USD", EUR: "Euro · EUR" } },
        { name: "tags", label: "Etiquetas", value: project.tags?.join(", "), hint: "Separe por vírgula." },
        { name: "technology_stack", label: "Stack tecnológica", value: project.technology_stack?.join(", ") },
        { name: "planned_start", label: "Data prevista de início", type: "date", value: project.planned_start }, { name: "planned_end", label: "Data prevista de término", type: "date", value: project.planned_end },
        { name: "technical_requirements", label: "Requisitos técnicos", type: "textarea", value: project.technical_requirements?.join("\n"), hint: "Um requisito por linha." },
        { name: "soft_skills", label: "Competências comportamentais", type: "textarea", value: project.soft_skills?.join("\n") },
        { name: "constraints", label: "Restrições gerais", type: "textarea", value: project.constraints, wide: true },
      ], "Salvar contexto do projeto", values => run(async req => { project = await req("projects", "PATCH", `/projects/${project.id}`, projectDetails(values)); }, "Contexto atualizado."));
      panel.append(editor.node);
    }
    if (can("project:lifecycle:manage")) {
      const lifecycle = form("project-lifecycle", [{ name: "status", label: "Nova situação do projeto", type: "select", value: project.status || "active", options: PROJECT_STATUSES }], "Alterar situação do projeto", values => run(async req => {
        project = await req("projects", "POST", `/projects/${project.id}/lifecycle`, { ...values, expected_version: project.version });
      }, "Situação atualizada. Atualize o contexto para conferir as ações disponíveis."));
      panel.append(section("Ciclo de vida", "Projetos suspensos, concluídos ou arquivados preservam consultas e restringem alterações."), lifecycle.node,
        action(project.archived ? "Restaurar projeto" : "Arquivar projeto concluído", () => run(async req => {
          project = await req("projects", "POST", `/projects/${project.id}/${project.archived ? "restore" : "archive"}`, { expected_version: project.version });
        }, "Estado de arquivamento atualizado.")));
    }
    if (own()) {
      const transfer = form("project-transfer", [{ name: "user_id", label: "ID do novo responsável pelo projeto", required: true, hint: "A pessoa precisa estar ativa e já autorizada no projeto." }], "Transferir responsabilidade", values => {
        if (confirm("Transferir a propriedade? Você permanecerá como PM e poderá perder esse acesso depois.")) run(async req => { project = await req("projects", "POST", `/projects/${project.id}/transfer`, { ...values, expected_version: project.version }); }, "Responsabilidade transferida.");
      }); panel.append(section("Responsabilidade"), transfer.node,
        action("Excluir cadastro vazio", () => { if (confirm("Excluir definitivamente este cadastro? A operação será recusada se houver dados relevantes.")) run(async req => {
          await req("projects", "DELETE", `/projects/${project.id}`); clear(); onBack({ deleted: true });
        }); }));
    }
    panel.append(action("Atualizar contexto", () => go("context", renderProject))); content.replaceChildren(panel);
  }); }
  function renderProjectHistory(offset = 0) { projectNavigation("history"); return run(async request => {
    const page = await request("projects", "GET", `/projects/${project.id}/history?limit=20&offset=${offset}`);
    const panel = section("Histórico do projeto", "Eventos registrados a partir da habilitação do histórico. O passado não é reconstruído artificialmente.");
    panel.append(auditRows(page), pagination(page, renderProjectHistory));
    if (can("project:audit:read")) panel.append(action("Consultar alterações de acesso", () => run(async req => {
      const audit = await req("projects", "GET", `/projects/${project.id}/audit?limit=100&offset=0`); panel.append(section("Alterações de acesso"), auditRows(audit));
    })));
    content.replaceChildren(panel);
  }); }
  function renderProjectTeams() { projectNavigation("project-teams"); return run(async request => {
    const linked = await request("projects", "GET", `/projects/${project.id}/teams`);
    const panel = section("Equipes vinculadas", "O vínculo concede papéis aos membros ativos da equipe. Remover o vínculo elimina apenas essa origem de acesso.");
    panel.append(rows(pageItems(linked), [{ label: "Equipe", value: row => row.team_name || row.name || row.team_id }, { label: "Papéis herdados", value: row => row.roles?.map(roleLabel).join(", ") }],
      { caption: "Equipes do projeto", actions: can("project:teams:manage") || can("project:members:manage") ? row => [action("Desvincular equipe", () => {
        if (confirm("Remover os acessos herdados por esta equipe neste projeto?")) run(async req => { await req("projects", "DELETE", `/projects/${project.id}/teams/${row.team_id || row.id}`); }, "Equipe desvinculada. Atualize para conferir.");
      })] : undefined }));
    if (can("project:teams:manage") || can("project:members:manage")) {
      const teams = pageItems(await request("projects", "GET", "/teams?limit=100&offset=0"));
      const link = form("project-team-link", [{ name: "team_id", label: "Equipe para vincular", type: "select", options: teams.map(team => ({ value: team.id, label: team.name })), required: true },
        { name: "roles", label: "Papéis da equipe no projeto", type: "multiselect", options: roleOptions, value: ["developer"], required: true },
        { name: "expires_at", label: "Expiração do vínculo da equipe", type: "datetime-local" }], "Vincular equipe", values => run(async req => {
          await req("projects", "POST", `/projects/${project.id}/teams`, { ...values, expires_at: values.expires_at ? new Date(values.expires_at).toISOString() : null });
        }, "Equipe vinculada. Atualize os acessos para conferir.")); panel.append(link.node);
      const allocation = form("project-allocation", [{ name: "user_id", label: "ID da pessoa para alocação", required: true },
        { name: "weekly_hours", label: "Horas semanais no projeto", type: "number", min: 0, max: 168, step: "0.5", required: true },
        { name: "hourly_rate", label: "Custo por hora informado", hint: "Opcional; não é inferido pela senioridade." }, { name: "currency", label: "Moeda do custo", value: "BRL" }], "Salvar alocação", values => run(async req => {
          const rate = decimalValue(values.hourly_rate);
          await req("projects", "PUT", `/projects/${project.id}/allocations`, { ...values, weekly_hours: decimalValue(values.weekly_hours), hourly_rate: rate, currency: rate === null ? null : values.currency });
        }, "Alocação salva.")); panel.append(section("Alocação de capacidade"), allocation.node);
    }
    const allocations = await request("projects", "GET", `/projects/${project.id}/allocations`);
    panel.append(rows(pageItems(allocations), [{ label: "Pessoa", value: identityLabel }, { label: "Horas semanais", key: "weekly_hours", numeric: true }, { label: "Custo por hora", value: row => row.hourly_rate !== null && row.hourly_rate !== undefined ? `${row.currency || ""} ${row.hourly_rate}` : "Não informado", numeric: true }], { caption: "Alocações do projeto" }));
    content.replaceChildren(panel);
  }); }

  function renderRoles() { projectNavigation("roles"); return run(async request => {
    roleCatalog = pageItems(await request("projects", "GET", `/projects/${project.id}/roles`));
    const members = pageItems(await request("projects", "GET", `/projects/${project.id}/members?limit=100&offset=0`));
    const panel = section("Papéis e acessos", "Papéis fixos são protegidos. Os personalizados usam permissões conhecidas e não concedem propriedade nem administração global.");
    panel.append(rows(roleCatalog, [{ label: "Papel", key: "name" }, { label: "Permissões", value: row => row.permissions.map(permission => PERMISSION_NAMES[permission] || permission).join(", ") }], { caption: "Catálogo de papéis", actions: can("project:roles:manage") ? row => row.key.startsWith("custom:") ? [
      action("Editar papel", () => roleEditor(row)), action("Excluir papel sem vínculos", () => run(async req => { await req("projects", "DELETE", `/projects/${project.id}/roles/${encodeURIComponent(row.key)}`); }, "Papel excluído. Atualize para conferir.")),
    ] : [] : undefined }));
    if (can("project:roles:manage")) panel.append(action("Criar papel personalizado", () => roleEditor()));
    panel.append(section("Integrantes e concessões"), rows(members, [{ label: "Integrante", value: identityLabel }, { label: "Papéis efetivos", value: row => row.roles?.map(roleLabel).join(", ") }, { label: "Origem", value: row => row.is_owner ? "Proprietário" : row.origins?.join(", ") || "Direta" }],
      { caption: "Acessos do projeto", actions: can("project:members:manage") ? row => row.is_owner ? [] : [action("Editar concessões", () => memberEditor(row))] : undefined }));
    if (can("project:members:manage")) {
      const member = form("project-manual-member", [{ name: "user_id", label: "ID da conta para adicionar ao projeto", required: true }, { name: "roles", label: "Papéis iniciais no projeto", type: "multiselect", value: ["developer"], options: roleCatalog.filter(role => role.key !== "owner").map(role => ({ value: role.key, label: role.name })), required: true }], "Adicionar membro ao projeto", values => run(async req => { await req("projects", "POST", `/projects/${project.id}/members`, values); member.reset(); }, "Membro adicionado.")); panel.append(member.node);
    }
    content.replaceChildren(panel);
  }); }
  function roleEditor(role = null) {
    const panel = section(role ? "Editar papel personalizado" : "Criar papel personalizado");
    const descriptors = [{ name: "name", label: "Nome do papel personalizado", value: role?.name || "", required: true }];
    for (const permission of PERMISSIONS.filter(key => !["project:delete", "project:roles:manage"].includes(key))) descriptors.push({ name: permission, label: PERMISSION_NAMES[permission] || permission, type: "checkbox", value: role?.permissions.includes(permission) });
    const editor = form("custom-role", descriptors, "Salvar papel personalizado", values => run(async request => {
      const draft = { name: values.name, permissions: PERMISSIONS.filter(permission => values[permission]) };
      await request("projects", role ? "PATCH" : "POST", `/projects/${project.id}/roles${role ? "/" + encodeURIComponent(role.key) : ""}`, draft);
      panel.remove();
    }, "Papel salvo. Atualize o catálogo para conferir.")); panel.append(editor.node); content.prepend(panel); editor.inputs.name.focus();
  }
  function memberEditor(member) {
    const panel = section("Concessões do integrante", "A expiração é aplicada a cada papel. Um campo vazio mantém a concessão sem prazo.");
    const descriptors = [];
    for (const role of roleCatalog.filter(role => role.key !== "owner")) {
      descriptors.push({ name: role.key, label: `Conceder ${role.name}`, type: "checkbox", value: member.roles.includes(role.key) });
      const grant = member.role_grants?.find(entry => entry.role === role.key);
      const expiry = grant?.expires_at || member.expires_at;
      descriptors.push({ name: `expires:${role.key}`, label: `Expiração de ${role.name}`, type: "datetime-local", value: expiry ? new Date(Date.parse(expiry) - new Date(expiry).getTimezoneOffset() * 60000).toISOString().slice(0, 16) : "" });
    }
    const editor = form("member-grants", descriptors, "Salvar concessões", values => run(async request => {
      const roles = roleCatalog.filter(role => values[role.key]).map(role => role.key);
      const role_grants = roles.map(role => ({ role, expires_at: values[`expires:${role}`] ? new Date(values[`expires:${role}`]).toISOString() : null }));
      await request("projects", "PATCH", `/projects/${project.id}/members/${member.user_id}`, { roles, role_grants }); panel.remove();
    }, "Concessões atualizadas."));
    panel.append(editor.node, action("Remover acesso deste projeto", () => {
      if (confirm("Revogar o acesso desta pessoa ao projeto, inclusive o herdado por equipes?")) run(async request => { await request("projects", "DELETE", `/projects/${project.id}/members/${member.user_id}`); panel.remove(); }, "Acesso removido.");
    })); content.prepend(panel);
  }

  function renderBoard() { projectNavigation("board"); return run(async request => {
    await refreshProject(request); projectNavigation("board");
    const data = await request("backlog", "GET", `/projects/${project.id}/board`);
    boardVersion = data.version;
    const list = await request("backlog", "GET", `/projects/${project.id}/items?limit=100&offset=0${Object.entries(itemQuery).filter(([, value]) => value).map(([key, value]) => `&${key}=${encodeURIComponent(value)}`).join("")}`);
    itemPage = pageItems(list);
    const panel = section("Quadro do projeto", "A prioridade MoSCoW e a posição manual são informações distintas. Você também pode mover itens pelos botões.");
    const search = form("item-search", [{ name: "q", label: "Buscar itens por ID, título ou descrição", value: itemQuery.q }, { name: "kind", label: "Tipo de item", type: "select", value: itemQuery.kind || "", options: { "": "Todos", ...ITEM_KINDS } }, { name: "moscow_priority", label: "Filtrar prioridade MoSCoW", type: "select", value: itemQuery.moscow_priority || "", options: { "": "Todas", ...MOSCOW } }], "Filtrar itens", values => { itemQuery = values; go("board", renderBoard); });
    panel.append(search.node);
    const board = el("div", null, { class: "workspace-board" });
    const columns = data.columns || {};
    for (const [state, label] of Object.entries(ITEM_STATUSES)) {
      const column = el("section", null, { class: "board-column", "aria-label": label });
      const group = Array.isArray(columns) ? columns.find(entry => entry.status === state)?.items || [] : columns[state] || [];
      column.append(el("h3", `${label} · ${group.length}`));
      column.addEventListener("dragover", event => { if (canWrite("backlog:update_status")) event.preventDefault(); });
      column.addEventListener("drop", event => {
        event.preventDefault(); const id = event.dataTransfer.getData("text/plain");
        const item = Object.values(columns).flat().find(entry => entry.id === id);
        if (item && canWrite("backlog:update_status") && item.status !== state) changeItemStatus(item, state);
      });
      for (const item of group) {
        const row = el("article", null, { class: "board-item" });
        row.draggable = canWrite("backlog:update_status") || canWrite("backlog:reorder");
        row.addEventListener("dragstart", event => event.dataTransfer.setData("text/plain", item.id));
        row.addEventListener("dragover", event => { if (canWrite("backlog:reorder")) event.preventDefault(); });
        row.addEventListener("drop", event => {
          if (!canWrite("backlog:reorder")) return;
          event.preventDefault(); event.stopPropagation();
          const source = Object.values(columns).flat().find(entry => entry.id === event.dataTransfer.getData("text/plain"));
          if (!source || source.id === item.id) return;
          if (source.status !== item.status) { if (canWrite("backlog:update_status")) changeItemStatus(source, item.status); }
          else reorderBefore(source.id, item.id);
        });
        row.append(action(item.title, () => openItem(item)), el("p", `${ITEM_KINDS[item.kind] || "História"} · ${MOSCOW[item.moscow_priority] || "MoSCoW não definida"}`, { class: "field-hint" }));
        if (item.is_blocked) row.append(el("p", `Bloqueado: ${item.blocked_reason}`, { class: "board-blocked" }));
        const pending = data.unresolved_dependencies?.[item.id] || [];
        if (pending.length) row.append(el("p", `${pending.length} dependência(s) ainda não concluída(s).`, { class: "field-hint" }));
        if (item.assignee_available === false) row.append(el("p", "Responsável indisponível; a atribuição histórica foi preservada.", { class: "field-hint" }));
        column.append(row);
      }
      if (!group.length) column.append(el("p", "Nenhum item nesta coluna.", { class: "field-hint" }));
      board.append(column);
    }
    panel.append(board, section("Itens do backlog"), rows(itemPage, [{ label: "Título", value: item => action(item.title, () => openItem(item)) }, { label: "Tipo", value: item => ITEM_KINDS[item.kind] || "História" }, { label: "MoSCoW", value: item => MOSCOW[item.moscow_priority] || "Não definida" }, { label: "Situação", value: item => ITEM_STATUSES[item.status] }], { caption: "Itens do projeto", empty: "Nenhum item encontrado com estes filtros.", actions: canWrite("backlog:reorder") && !Object.values(itemQuery).some(Boolean) ? item => [
      action("Subir", () => reorderItem(item, -1), { label: `Subir ${item.title}` }), action("Descer", () => reorderItem(item, 1), { label: `Descer ${item.title}` }),
    ] : undefined }));
    if (can("backlog:create") && !project.archived && ["active", "planned", undefined].includes(project.status)) panel.append(action("Novo item de backlog", () => itemEditor()));
    panel.append(action("Atualizar quadro", () => go("board", renderBoard)), action("Sugerir backlog inicial", () => go("recommendations", () => renderRecommendations("backlog"))));
    content.replaceChildren(panel);
  }); }
  function changeItemStatus(item, state) { return run(async request => {
    await request("backlog", "PATCH", `/projects/${project.id}/items/${item.id}`, { status: state, expected_version: item.version });
  }, "Situação atualizada. Atualize o quadro para conferir."); }
  function reorderItem(item, delta) {
    return run(async request => {
      const all = await request("backlog", "GET", `/projects/${project.id}/items?limit=100&offset=0`);
      if (all.total > pageItems(all).length) throw new TypeError("A ordem exige o grupo completo. Use os filtros de grupo antes de reorganizar.");
      const ids = pageItems(all).map(row => row.id), index = ids.indexOf(item.id), next = index + delta;
      if (index < 0 || next < 0 || next >= ids.length) return;
      [ids[index], ids[next]] = [ids[next], ids[index]];
      const reply = await request("backlog", "POST", `/projects/${project.id}/items/reorder`, { item_ids: ids, expected_version: boardVersion });
      boardVersion = reply.version;
    }, "Ordem salva. Atualize o quadro para conferir.");
  }
  function reorderBefore(source, target) {
    return run(async request => {
      const all = await request("backlog", "GET", `/projects/${project.id}/items?limit=100&offset=0`);
      if (all.total > pageItems(all).length) throw new TypeError("A ordem exige o grupo completo. Este quadro excede o limite de ordenação de 100 itens.");
      const ids = pageItems(all).map(item => item.id);
      if (!ids.includes(source) || !ids.includes(target)) throw new TypeError("O quadro mudou. Atualize antes de reorganizar.");
      ids.splice(ids.indexOf(source), 1); ids.splice(ids.indexOf(target), 0, source);
      const reply = await request("backlog", "POST", `/projects/${project.id}/items/reorder`, { item_ids: ids, expected_version: boardVersion });
      boardVersion = reply.version;
    }, "Ordem salva. Atualize o quadro para conferir.");
  }
  function openItem(item) { selectedItem = item; return go("item-detail", renderItem); }
  function renderItem() { projectNavigation("board"); return run(async request => {
    selectedItem = await request("backlog", "GET", `/projects/${project.id}/items/${selectedItem.id}`);
    const item = selectedItem, panel = section(item.title, item.description);
    panel.append(details({ "ID do item": item.id, "Tipo": ITEM_KINDS[item.kind], "Critérios de aceitação": item.acceptance_criteria,
      "Persona": item.persona, "Ação": item.action, "Objetivo": item.benefit, "MoSCoW": MOSCOW[item.moscow_priority],
      "Estimativa": item.estimate_value !== null && item.estimate_value !== undefined ? `${item.estimate_value} ${item.estimate_unit === "hours" ? "horas" : "pontos"}` : "Não informada",
      "Responsável": item.assignee_available === false ? `${item.assignee_id} · indisponível` : item.assignee_id, "Autor": item.created_by, "Épico": item.epic_id, "História vinculada": item.parent_story_id,
      "Situação": ITEM_STATUSES[item.status], "Bloqueio": item.is_blocked ? item.blocked_reason : "Sem bloqueio", "Criado em": textDate(item.created_at), "Atualizado em": textDate(item.updated_at) }));
    if (can("backlog:update") && !project.archived && ["active", "planned", undefined].includes(project.status)) panel.append(action("Editar item", () => itemEditor(item)));
    if (canWrite("backlog:update_status")) {
      const statusForm = form("item-status", [{ name: "status", label: "Nova situação do item", type: "select", options: ITEM_STATUSES, value: item.status }], "Atualizar situação do item", values => changeItemStatus(item, values.status)); panel.append(statusForm.node);
    }
    const dependencies = await request("backlog", "GET", `/projects/${project.id}/items/${item.id}/dependencies`);
    panel.append(section("Dependências", "Este item depende dos itens listados abaixo. Ciclos e referências a outro projeto são recusados."), rows(pageItems(dependencies), [{ label: "Item necessário", value: row => row.title || row.depends_on_id || row.id }], { caption: "Dependências", actions: can("backlog:update") ? row => [action("Remover dependência", () => run(async req => { await req("backlog", "DELETE", `/projects/${project.id}/items/${item.id}/dependencies/${row.depends_on_id || row.id}`); }, "Dependência removida."))] : undefined }));
    if (canWrite("backlog:update")) {
      const dependency = form("item-dependency", [{ name: "depends_on_id", label: "ID do item necessário", required: true }], "Adicionar dependência", values => run(async req => { await req("backlog", "POST", `/projects/${project.id}/items/${item.id}/dependencies`, values); dependency.reset(); }, "Dependência registrada.")); panel.append(dependency.node);
    }
    const history = await request("backlog", "GET", `/projects/${project.id}/items/${item.id}/history?limit=100&offset=0`);
    panel.append(section("Histórico do item"), auditRows(history), action("Voltar para o quadro", () => go("board", renderBoard))); content.replaceChildren(panel);
  }); }
  function itemEditor(item = null) {
    const panel = section(item ? "Editar item de backlog" : "Novo item de backlog", "Use o formato orientado quando quiser registrar persona, ação e objetivo separadamente.");
    const values = item || {};
    const descriptors = [
      { name: "kind", label: "Tipo do novo item", type: "select", options: ITEM_KINDS, value: values.kind || "story" },
      { name: "title", label: "Título do item", required: true, maxLength: 120, value: values.title },
      { name: "description", label: "Descrição do item", type: "textarea", wide: true, value: values.description },
      { name: "acceptance_criteria", label: "Critérios de aceitação do item", type: "textarea", wide: true, value: values.acceptance_criteria },
      { name: "persona", label: "Persona da história", value: values.persona }, { name: "action", label: "Ação desejada", value: values.action },
      { name: "benefit", label: "Objetivo ou benefício", value: values.benefit },
      { name: "moscow_priority", label: "Prioridade MoSCoW do item", type: "select", value: values.moscow_priority || "", options: { "": "Não definida", ...MOSCOW } },
      { name: "priority", label: "Prioridade compatível", type: "select", value: values.priority || "medium", options: { high: "Alta", medium: "Média", low: "Baixa" } },
      { name: "status", label: "Situação inicial", type: "select", value: values.status || "todo", options: ITEM_STATUSES },
      { name: "estimate_value", label: "Estimativa de esforço", value: values.estimate_value }, { name: "estimate_unit", label: "Unidade da estimativa", type: "select", value: values.estimate_unit || "", options: { "": "Não definida", points: "Pontos", hours: "Horas" } },
      { name: "assignee_id", label: "ID do responsável pelo item", value: values.assignee_id, hint: "A conta deve estar ativa e autorizada neste projeto." },
      { name: "epic_id", label: "ID do épico", value: values.epic_id }, { name: "parent_story_id", label: "ID da história vinculada à tarefa", value: values.parent_story_id },
      { name: "is_blocked", label: "Item bloqueado", type: "checkbox", value: values.is_blocked }, { name: "blocked_reason", label: "Motivo do bloqueio", type: "textarea", value: values.blocked_reason },
    ];
    const editor = form("item-editor", item ? descriptors : descriptors.filter(field => field.name !== "status"), item ? "Salvar item de backlog" : "Criar item de backlog", data => run(async request => {
      const draft = itemDraft(data);
      if (item) { delete draft.kind; draft.expected_version = item.version; }
      else delete draft.status;
      const saved = await request("backlog", item ? "PATCH" : "POST", `/projects/${project.id}/items${item ? "/" + item.id : ""}`, draft);
      selectedItem = saved; panel.remove();
    }, item ? "Item atualizado. Abra novamente para conferir os detalhes." : "Item criado. Atualize o quadro para conferir."));
    if (item) editor.inputs.kind.disabled = true;
    panel.append(editor.node, action("Cancelar edição do item", () => panel.remove())); content.prepend(panel); editor.inputs.title.focus();
  }

  function renderRecommendations(service) {
    if (service === "identity") adminNavigation("anomalies"); else projectNavigation("recommendations");
    return run(async request => {
      const base = service === "identity" ? "/admin/recommendations" : `/projects/${project.id}/recommendations`;
      const page = await request(service, "GET", base + "?limit=20&offset=0");
      const panel = section("Recomendações com aprovação humana", "Sugestões não alteram acessos nem criam entregas automaticamente. Confira a justificativa, os dados usados e o contexto antes de aprovar.");
      const kinds = service === "identity" ? { access_anomalies: "Análise de acessos" } : service === "backlog" ? { initial_backlog: "Backlog inicial" } : { roles: "Papéis e menor privilégio", access_revocation: "Acessos não utilizados", teams: "Formação de equipe", skills_map: "Mapa de competências", training: "Lacunas e treinamentos" };
      const generate = form("recommendation-create", [{ name: "kind", label: "Tipo de recomendação", type: "select", options: kinds },
        { name: "preference", label: "Foco da formação de equipe", type: "select", options: { availability: "Disponibilidade", cost: "Custo informado", seniority: "Senioridade" } },
        { name: "unused_days", label: "Dias sem atividade autorizada observada", type: "number", required: true, min: 1, max: 3650, step: 1, value: "30", hint: "Somente acessos observados durante toda a janela podem ser considerados inativos. Histórico desconhecido não é inatividade." }], "Solicitar recomendação", values => run(async req => {
          const constraints = values.kind === "teams" ? { preference: values.preference }
            : values.kind === "access_revocation" ? { unused_days: Number(values.unused_days) } : {};
          const proposal = await req(service, "POST", base, { kind: values.kind, constraints }, { timeout: 35000 });
          panel.append(recommendationCard(proposal, service, base));
        }, "Recomendação recebida para análise. Nenhuma alteração foi aplicada."));
      function scopeFields() {
        for (const [name, kind] of [["preference", "teams"], ["unused_days", "access_revocation"]]) {
          const visible = generate.inputs.kind.value === kind;
          generate.inputs[name].disabled = !visible; generate.inputs[name].closest(".field").hidden = !visible;
        }
      }
      generate.inputs.kind.addEventListener("change", scopeFields); scopeFields();
      panel.append(generate.node);
      for (const proposal of pageItems(page)) panel.append(recommendationCard(proposal, service, base));
      if (!pageItems(page).length) panel.append(el("p", "Nenhuma recomendação registrada. O serviço de IA precisa estar configurado para gerar sugestões."));
      content.replaceChildren(panel);
    });
  }
  function recommendationCard(proposal, service, base) {
    const panel = section(proposal.summary || "Recomendação", proposal.justification);
    panel.append(details({ "Situação": ({ pending: "Aguardando decisão", approved: "Aprovada", rejected: "Rejeitada", expired: "Contexto expirado" })[proposal.status] || proposal.status,
      "Origem": proposal.simulated ? "Simulação local · não é uma avaliação de IA real" : proposal.provider || "Provedor configurado", "Modelo": proposal.model, "Criada em": textDate(proposal.created_at) }));
    for (const suggestion of proposal.suggestions || []) {
      const fields = {};
      const labels = { user_id: "Pessoa", team_id: "Equipe", name: "Nome", roles: "Papéis", reason: "Motivo", title: "História sugerida", description: "Descrição", topics: "Tópicos de estudo", skill: "Competência", gap: "Lacuna", user_ids: "Integrantes", action: "Ação sugerida", acceptance_criteria: "Critérios de aceitação" };
      for (const [key, value] of Object.entries(suggestion)) if (labels[key]) fields[labels[key]] = Array.isArray(value) ? value.map(item => typeof item === "string" ? item : item.name || "Sugestão estruturada").join(", ") : value;
      panel.append(details(fields));
    }
    if (proposal.evidence?.length) panel.append(el("p", `Dados consultados: ${proposal.evidence.join(", ")}`, { class: "field-hint" }));
    if (proposal.status === "pending") {
      const decisions = el("div", null, { class: "form-actions" });
      for (const [choice, label] of [["approve", "Aprovar recomendação"], ["reject", "Rejeitar recomendação"]]) decisions.append(action(label, () => run(async request => {
        const result = await request(service, "POST", `${base}/${proposal.id}/${choice}`, { expected_version: proposal.version });
        panel.replaceWith(recommendationCard(result || { ...proposal, status: choice === "approve" ? "approved" : "rejected" }, service, base));
      }, choice === "approve" ? "Recomendação aprovada com as permissões atuais." : "Recomendação rejeitada. Nenhuma alteração aplicada.")));
      panel.append(decisions);
    }
    return panel;
  }

  function enter(nextMode) {
    invalidate(); mode = nextMode; selectedTeam = selectedItem = null; status(); root.hidden = false;
    back.textContent = nextMode === "project" ? "Voltar para projetos" : "Voltar para minha conta";
    back.setAttribute("aria-label", back.textContent); onEnter();
  }
  return {
    clear,
    openSecurity() { project = null; enter("security"); const result = renderSessions(); heading.focus(); return result; },
    openTeams() { project = null; enter("teams"); const result = renderTeams(); heading.focus(); return result; },
    openNotifications() { project = null; enter("notifications"); const result = renderNotifications(); heading.focus(); return result; },
    openAdmin() { if (!getIdentity()?.is_admin) return; project = null; enter("admin"); const result = renderAdmin(); heading.focus(); return result; },
    openProject(value, initial = "context") { project = value; itemQuery = {}; enter("project"); const result = initial === "board" ? renderBoard() : renderProject(); heading.focus(); return result; },
  };
}
