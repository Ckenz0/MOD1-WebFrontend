import { ProjectsApiError } from "./api-errors.js";
import { createFormValidation, nameError } from "./validation.js";
import { permissionsFor } from "./permissions.js";
import { createMembersController } from "./collaboration.js";

const byId = (id) => document.getElementById(id);
const date = (value) => new Intl.DateTimeFormat("pt-BR", { dateStyle: "long" }).format(new Date(value));

// The list opens a project page; its overview and members panels are tabs that the workspace hosts.
export function createProjectsController({ api, getToken, getSessionKey = getToken, getUserId = () => null, onUnauthorized,
  onOpenProject = () => {}, onProjectChange = () => {}, onShowList = () => {}, onAccessDenied = onShowList }) {
  let generation = 0;
  let controller = null;
  let busy = false;
  let selectedProject = null;
  let query = "";
  let filters = {};
  const members = createMembersController({ api, getToken, getSessionKey, getUserId, onUnauthorized, onAccessChange: permissions => {
    if (!selectedProject) return;
    selectedProject = { ...selectedProject, permissions };
    byId("project-edit").hidden = !permissions.includes("project:update");
    if (!permissions.includes("project:update")) editForm.hidden = true;
    onProjectChange({ id: selectedProject.id, permissions });
  }, onSelfChange: async target => {
    if (target !== getUserId()) return false;
    const sessionKey = getSessionKey(); await onShowList();
    if (sessionKey === getSessionKey() && !byId("projects-view").hidden) status("Seus acessos foram atualizados. A lista agora reflete suas permissões.");
    return true;
  } });
  let page = { items: [], total: 0, limit: 20, offset: 0 };
  const form = byId("project-form");
  const editForm = byId("project-edit-form");
  const searchForm = byId("project-search-form");
  const longText = input => Array.from(input.value).length <= 2000 ? "" : "Use até 2000 caracteres.";
  const validation = createFormValidation("project-form", {
    "project-name": nameError,
    "project-description": (input) => Array.from(input.value).length <= 2000 ? "" : "Use uma descrição de até 2000 caracteres.",
    "project-objective": longText,
  });
  const editValidation = createFormValidation("project-edit-form", {
    "project-edit-name": nameError, "project-edit-description": longText, "project-edit-objective": longText,
  });
  validation.enable();
  editValidation.enable();

  // The list and the overview tab each have their own status line; write to the one on screen.
  const onOverview = () => !byId("project-detail").hidden;
  const active = () => !byId("projects-view").hidden || onOverview();
  function status(text = "", tone = "notice") {
    for (const id of ["projects-status", "project-detail-status"]) { const other = byId(id); other.textContent = ""; other.hidden = true; }
    const node = byId(onOverview() ? "project-detail-status" : "projects-status");
    node.textContent = text;
    node.dataset.tone = tone;
    node.hidden = !text;
  }
  function setBusy(value) {
    busy = value;
    form.setAttribute("aria-busy", String(value));
    for (const element of form.elements) element.disabled = value;
    for (const f of [editForm, searchForm]) {
      f.setAttribute("aria-busy", String(value));
      for (const element of f.elements) element.disabled = value;
    }
    byId("project-edit").disabled = value;
    byId("project-submit").textContent = value ? "Aguarde…" : "Criar projeto";
    byId("projects-refresh").disabled = value;
    byId("projects-previous").disabled = value || page.offset === 0;
    byId("projects-next").disabled = value || page.offset + page.limit >= page.total;
    byId("projects-list").setAttribute("aria-busy", String(value));
    for (const button of byId("projects-list").querySelectorAll("button")) button.disabled = value;
  }
  function hideDetail() {
    members.clear();
    selectedProject = null;
    byId("project-detail").hidden = true;
    editForm.hidden = true; editForm.reset(); editValidation.clear();
    for (const id of ["project-detail-description", "project-detail-date", "project-detail-objective", "project-access-note"]) byId(id).textContent = "";
  }
  function renderDetail(project, { focus = false } = {}) {
    members.clear();
    selectedProject = { ...project, permissions: permissionsFor(project, getUserId()) };
    byId("project-detail-description").textContent = project.description || "Sem descrição.";
    byId("project-detail-objective").textContent = project.objective || "Sem objetivo registrado.";
    editForm.hidden = true; editForm.reset(); editValidation.clear();
    byId("project-edit").hidden = !selectedProject.permissions.includes("project:update");
    byId("project-access-note").textContent = project.owner_id === getUserId()
      ? "Você é o proprietário deste projeto."
      : selectedProject.permissions.includes("project:update") ? "Você pode consultar e editar este projeto."
      : "Você tem acesso de consulta. As ações disponíveis seguem seus papéis no projeto.";
    byId("project-detail-date").textContent = date(project.created_at);
    byId("project-detail").hidden = false;
    if (focus) byId("project-detail-title").focus();
  }
  function renderPage(value) {
    page = value;
    const list = byId("projects-list");
    list.replaceChildren();
    if (value.items.length === 0) {
      const empty = document.createElement("p");
      empty.className = "projects-empty";
      empty.textContent = value.total === 0 && query ? "Nenhum projeto encontrado. Tente outro nome ou limpe a busca."
        : value.total === 0 ? "Você ainda não tem projetos. Crie o primeiro para organizar seu trabalho."
        : "Não há projetos nesta página. Volte para a página anterior.";
      list.append(empty);
    } else {
      const ul = document.createElement("ul");
      for (const project of value.items) {
        const li = document.createElement("li");
        // Project tile with the name's initials, as in an issue tracker's project list.
        const tile = document.createElement("span");
        tile.className = "project-tile"; tile.setAttribute("aria-hidden", "true");
        tile.textContent = project.name.trim().split(/\s+/).slice(0, 2).map(part => Array.from(part)[0] || "").join("").toLocaleUpperCase("pt-BR");
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = project.name;
        button.setAttribute("aria-label", project.name);
        button.addEventListener("click", () => { if (!busy) onOpenProject(project); });
        const summary = document.createElement("span");
        summary.className = "project-summary";
        summary.textContent = project.description || "Sem descrição.";
        const time = document.createElement("time");
        time.dateTime = project.created_at;
        time.textContent = date(project.created_at);
        li.append(tile, button, summary, time); ul.append(li);
      }
      list.append(ul);
    }
    byId("projects-count").textContent = value.total === 0 ? "" : `${value.offset + 1}–${value.offset + value.items.length} de ${value.total} projetos`;
  }
  async function run(action, onSuccess, errorPrefix = () => "", confirmedNotice = () => "") {
    const token = getToken(), sessionKey = getSessionKey();
    if (!token) { clear(); onUnauthorized(); return; }
    const current = ++generation;
    controller?.abort(); controller = new AbortController();
    const { signal } = controller;
    const valid = () => current === generation && sessionKey === getSessionKey() && active();
    status(onOverview() ? "Carregando projeto…" : "Carregando projetos…"); setBusy(true);
    try {
      const result = await action(token, signal);
      if (!valid()) return;
      status();
      await onSuccess(result, { token, signal, valid });
    } catch (error) {
      if (!valid() || error.kind === "cancelled") return;
      if (error.kind === "unauthorized") { const notice = confirmedNotice(); clear(); onUnauthorized(notice); return; }
      if (onOverview() && ["forbidden", "not-found"].includes(error.kind)) {
        const id = selectedProject?.id;
        hideDetail(); setBusy(false);
        await onAccessDenied(id);
        if (sessionKey === getSessionKey() && !byId("projects-view").hidden) status(error.message, "error");
        return;
      }
      status(errorPrefix() + (error instanceof ProjectsApiError ? error.message : "Não foi possível carregar os projetos. Tente novamente."), "error");
    } finally {
      if (valid()) { controller = null; setBusy(false); }
    }
  }
  async function load(offset = 0) {
    return run((token, signal) => api.list(token, { offset, limit: 20, q: query, ...filters, signal }), value => {
      hideDetail(); renderPage(value);
    });
  }
  function close() {
    members.clear();
    generation += 1; controller?.abort(); controller = null;
    setBusy(false); byId("projects-view").hidden = true;
  }
  function clear() {
    close(); page = { items: [], total: 0, limit: 20, offset: 0 };
    query = ""; filters = {}; searchForm.reset();
    form.reset(); validation.clear(); byId("projects-list").replaceChildren();
    byId("projects-count").textContent = ""; hideDetail(); status(); setBusy(false);
  }
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (busy) return;
    if (!validation.validate()) { status("Confira os campos destacados para criar o projeto.", "error"); return; }
    const draft = { name: byId("project-name").value.trim(), description: byId("project-description").value,
      ...(byId("project-objective").value ? { objective: byId("project-objective").value } : {}) };
    let created = false;
    run((token, signal) => api.create(token, draft, { signal }), async project => {
      created = true; form.reset(); validation.clear();
      query = ""; searchForm.reset();
      onOpenProject(project, "Projeto criado. Ele já está salvo na sua conta.");
    }, () => created ? "Projeto criado. Atualize a lista para encontrá-lo. " : "",
    () => created ? "Projeto criado. " : "");
  });
  byId("project-edit").addEventListener("click", () => {
    if (busy || !selectedProject?.permissions.includes("project:update")) return;
    byId("project-edit-name").value = selectedProject.name;
    byId("project-edit-description").value = selectedProject.description;
    byId("project-edit-objective").value = selectedProject.objective || "";
    editValidation.clear(); editForm.hidden = false; byId("project-edit").hidden = true;
    byId("project-edit-name").focus();
  });
  byId("project-edit-cancel").addEventListener("click", () => {
    if (!busy && selectedProject) renderDetail(selectedProject);
  });
  editForm.addEventListener("submit", event => {
    event.preventDefault(); if (busy || !selectedProject?.permissions.includes("project:update")) return;
    if (!editValidation.validate()) { status("Confira os campos destacados para salvar o projeto.", "error"); return; }
    const projectId = selectedProject.id;
    const change = { name: byId("project-edit-name").value.trim(),
      description: byId("project-edit-description").value, objective: byId("project-edit-objective").value };
    let saved = false;
    run((token, signal) => api.update(token, projectId, change, { signal }), async project => {
      saved = true; renderDetail(project, { focus: true }); onProjectChange(project);
      status("Projeto atualizado. As alterações já estão salvas.");
    }, () => saved ? "Projeto atualizado. Atualize a lista para conferir. " : "",
    () => saved ? "Projeto atualizado. " : "");
  });
  searchForm.addEventListener("submit", event => {
    event.preventDefault(); if (busy) return;
    query = byId("project-search").value.trim();
    filters = { status: byId("project-filter-status").value, tag: byId("project-filter-tag").value,
      archived: byId("project-filter-archived").checked }; load(0);
  });
  byId("projects-refresh").addEventListener("click", () => { if (!busy) load(page.offset); });
  byId("projects-previous").addEventListener("click", () => { if (!busy) load(Math.max(0, page.offset - 20)); });
  byId("projects-next").addEventListener("click", () => { if (!busy) load(page.offset + 20); });
  setBusy(false);
  return {
    async open() {
      byId("projects-view").hidden = false;
      byId("projects-list").replaceChildren();
      byId("projects-title").focus();
      await load(0);
    }, close, clear,
    // Overview tab: shows what is already known at once, then the current record from the API.
    openOverview(project) {
      generation += 1; controller?.abort(); controller = null; setBusy(false);
      renderDetail(project); status();
      return run((token, signal) => api.get(token, project.id, { signal }), value => {
        renderDetail(value); onProjectChange(value);
      });
    },
    closeOverview() { generation += 1; controller?.abort(); controller = null; setBusy(false); status(); hideDetail(); },
    openMembers(project) {
      selectedProject = { ...project, permissions: permissionsFor(project, getUserId()) };
      return members.open(selectedProject);
    },
    closeMembers() { members.clear(); },
  };
}
