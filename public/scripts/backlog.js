import { BacklogApiError, trimStoryTitle } from "./backlog-api.js";
import { createFormValidation } from "./validation.js";

const byId = id => document.getElementById(id);
const priorities = { high: "Alta", medium: "Média", low: "Baixa" };
const statuses = { todo: "A fazer", in_progress: "Em andamento", done: "Concluído" };
const date = value => new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
const emptyPage = () => ({ items: [], total: 0, limit: 20, offset: 0 });

export function createBacklogController({ api, getToken, onUnauthorized, onBack }) {
  let generation = 0, controller = null, busy = false, project = null, selected = null;
  let page = emptyPage();
  let filters = {};
  let permissions = new Set();
  const form = byId("backlog-form"), updateForm = byId("story-update-form");
  const searchForm = byId("backlog-search-form");
  const titleError = input => { const length = Array.from(trimStoryTitle(input.value)).length;
    return length >= 1 && length <= 120 ? "" : "Informe um título de até 120 caracteres."; };
  const longText = input => Array.from(input.value).length <= 2000 ? "" : "Use até 2000 caracteres.";
  const validation = createFormValidation("backlog-form", {
    "story-title": input => { const length = Array.from(trimStoryTitle(input.value)).length;
      return length >= 1 && length <= 120 ? "" : "Informe um título de até 120 caracteres."; },
    "story-description": input => Array.from(input.value).length <= 2000 ? "" : "Use até 2000 caracteres na descrição.",
    "story-criteria": input => Array.from(input.value).length <= 2000 ? "" : "Use até 2000 caracteres nos critérios de aceite.",
  });
  validation.enable();
  const updateValidation = createFormValidation("story-update-form", {
    "story-update-title": titleError, "story-update-description": longText, "story-update-criteria": longText,
  });
  updateValidation.enable();
  function status(text = "", tone = "notice") {
    const node = byId("backlog-status"); node.textContent = text; node.dataset.tone = tone; node.hidden = !text;
  }
  function setBusy(value) {
    busy = value;
    for (const f of [form, updateForm, searchForm]) {
      f.setAttribute("aria-busy", String(value));
      for (const element of f.elements) element.disabled = value;
    }
    const create = permissions.has("backlog:create"), update = permissions.has("backlog:update");
    const changeStatus = permissions.has("backlog:update_status");
    byId("story-create-panel").hidden = !create;
    for (const element of form.elements) element.disabled = value || !create;
    for (const element of updateForm.elements) element.disabled = value || !update;
    byId("story-update-status").disabled = value || !changeStatus;
    byId("story-save").disabled = value || !(update || changeStatus);
    byId("story-edit-cancel").disabled = value || !(update || changeStatus);
    updateForm.hidden = !(update || changeStatus);
    byId("story-submit").textContent = value ? "Aguarde…" : "Criar história";
    byId("story-save").textContent = value ? "Aguarde…" : "Salvar alterações";
    byId("backlog-refresh").disabled = value;
    byId("backlog-previous").disabled = value || page.offset === 0;
    byId("backlog-next").disabled = value || page.offset + page.limit >= page.total;
    byId("backlog-list").setAttribute("aria-busy", String(value));
    for (const button of byId("backlog-list").querySelectorAll("button")) button.disabled = value;
  }
  function hideDetail() {
    selected = null; byId("story-detail").hidden = true;
    for (const id of ["story-detail-title", "story-detail-description", "story-detail-criteria", "story-detail-date"]) byId(id).textContent = "";
    updateForm.reset(); updateValidation.clear();
  }
  function renderDetail(story) {
    selected = story;
    byId("story-detail-title").textContent = story.title;
    byId("story-detail-description").textContent = story.description || "Sem descrição.";
    byId("story-detail-criteria").textContent = story.acceptance_criteria || "Sem critérios de aceite.";
    byId("story-detail-date").textContent = `Criada em ${date(story.created_at)} · Atualizada em ${date(story.updated_at)}`;
    byId("story-update-priority").value = story.priority; byId("story-update-status").value = story.status;
    byId("story-update-title").value = story.title;
    byId("story-update-description").value = story.description;
    byId("story-update-criteria").value = story.acceptance_criteria;
    updateValidation.clear();
    byId("story-detail").hidden = false; byId("story-detail-title").focus();
  }
  function renderPage(value) {
    page = value;
    const list = byId("backlog-list"); list.replaceChildren();
    if (!value.items.length) {
      const p = document.createElement("p"); p.className = "projects-empty";
      p.textContent = value.total === 0 && Object.values(filters).some(Boolean)
        ? "Nenhuma história encontrada. Ajuste ou limpe os filtros para tentar novamente."
        : value.total === 0 ? "Ainda não há histórias. Crie a primeira para definir o que o projeto precisa entregar."
        : "Não há histórias nesta página. Volte para a página anterior.";
      list.append(p);
    } else {
      const ul = document.createElement("ul");
      for (const story of value.items) {
        const li = document.createElement("li"), button = document.createElement("button"), meta = document.createElement("span");
        button.type = "button"; button.textContent = story.title;
        button.addEventListener("click", () => {
          if (busy) return;
          hideDetail(); run((token, id, signal) => api.get(token, id, story.id, { signal }), renderDetail);
        });
        meta.className = "story-meta"; meta.textContent = `${priorities[story.priority]} · ${statuses[story.status]}`;
        li.append(button, meta); ul.append(li);
      }
      list.append(ul);
    }
    byId("backlog-count").textContent = value.items.length ? `${value.offset + 1}–${value.offset + value.items.length} de ${value.total} histórias` : "";
  }
  async function run(action, onSuccess, errorPrefix = () => "", confirmedNotice = () => "") {
    const token = getToken(), projectId = project?.id;
    if (!token) { clear(); onUnauthorized(); return; }
    if (!projectId) return;
    const current = ++generation;
    controller?.abort(); controller = new AbortController(); const { signal } = controller;
    const valid = () => current === generation && token === getToken() && projectId === project?.id && !byId("backlog-view").hidden;
    status("Carregando histórias…"); setBusy(true);
    try {
      const result = await action(token, projectId, signal);
      if (!valid()) return;
      status(); await onSuccess(result, { token, projectId, signal, valid });
    } catch (error) {
      if (!valid() || error.kind === "cancelled") return;
      if (error.kind === "unauthorized") { const notice = confirmedNotice(); clear(); onUnauthorized(notice); return; }
      if (error.kind === "forbidden" || error.kind === "not-found") permissions = new Set(["backlog:read"]);
      status(errorPrefix() + (error instanceof BacklogApiError ? error.message : "Não foi possível carregar o backlog. Tente novamente."), "error");
    } finally {
      if (valid()) { controller = null; setBusy(false); }
    }
  }
  function load(offset = 0) {
    return run((token, id, signal) => api.list(token, id, { offset, limit: 20, ...filters, signal }), value => {
      hideDetail(); renderPage(value);
    });
  }
  function close() {
    generation += 1; controller?.abort(); controller = null;
    setBusy(false); byId("backlog-view").hidden = true;
  }
  function clear() {
    close(); project = null; page = emptyPage(); form.reset(); validation.clear(); hideDetail(); status();
    permissions = new Set();
    filters = {}; searchForm.reset();
    byId("backlog-list").replaceChildren(); byId("backlog-count").textContent = ""; byId("backlog-project-name").textContent = "";
    setBusy(false);
  }
  form.addEventListener("submit", event => {
    event.preventDefault(); if (busy || !project || !permissions.has("backlog:create")) return;
    if (!validation.validate()) { status("Confira os campos destacados para criar a história.", "error"); return; }
    const draft = { title: trimStoryTitle(byId("story-title").value), description: byId("story-description").value,
      acceptance_criteria: byId("story-criteria").value, priority: byId("story-priority").value };
    let created = false;
    run((token, id, signal) => api.create(token, id, draft, { signal }), async (story, ctx) => {
      created = true; form.reset(); validation.clear(); renderDetail(story);
      filters = {}; searchForm.reset();
      const list = await api.list(ctx.token, ctx.projectId, { limit: 20, offset: 0, signal: ctx.signal });
      if (!ctx.valid()) return;
      renderPage(list); status("História criada. Ela já está salva no projeto.");
    }, () => created ? "História criada. Atualize a lista para encontrá-la. " : "",
    () => created ? "História criada. " : "");
  });
  updateForm.addEventListener("submit", event => {
    event.preventDefault(); if (busy || !selected) return;
    const canUpdate = permissions.has("backlog:update"), canStatus = permissions.has("backlog:update_status");
    if (!canUpdate && !canStatus) return;
    if (canUpdate && !updateValidation.validate()) { status("Confira os campos destacados para salvar a história.", "error"); return; }
    const storyId = selected.id;
    const change = { status: byId("story-update-status").value };
    if (canUpdate) change.priority = byId("story-update-priority").value;
    for (const [field, input] of canUpdate ? [["title", "story-update-title"], ["description", "story-update-description"], ["acceptance_criteria", "story-update-criteria"]] : []) {
      const value = field === "title" ? trimStoryTitle(byId(input).value) : byId(input).value;
      if (value !== selected[field]) change[field] = value;
    }
    let saved = false;
    run((token, id, signal) => api.update(token, id, storyId, change, { signal }), async (story, ctx) => {
      saved = true; renderDetail(story);
      const list = await api.list(ctx.token, ctx.projectId, { limit: 20, offset: 0, ...filters, signal: ctx.signal });
      if (!ctx.valid()) return;
      renderPage(list); status("Alterações salvas. O progresso da história foi atualizado.");
    }, () => saved ? "Alterações salvas. Atualize a lista para conferir a ordem e o progresso. " : "",
    () => saved ? "Alterações salvas. " : "");
  });
  byId("story-edit-cancel").addEventListener("click", () => { if (!busy && selected) renderDetail(selected); });
  searchForm.addEventListener("submit", event => {
    event.preventDefault(); if (busy) return;
    filters = { q: byId("backlog-search").value.trim(), status: byId("backlog-filter-status").value,
      priority: byId("backlog-filter-priority").value }; load(0);
  });
  byId("backlog-refresh").addEventListener("click", () => { if (!busy) load(page.offset); });
  byId("backlog-previous").addEventListener("click", () => { if (!busy) load(Math.max(0, page.offset - 20)); });
  byId("backlog-next").addEventListener("click", () => { if (!busy) load(page.offset + 20); });
  byId("backlog-back").addEventListener("click", () => { clear(); onBack(); });
  setBusy(false);
  return { async open(value) {
    clear(); project = { id: value.id, name: value.name };
    permissions = new Set(value.permissions || []);
    byId("backlog-project-name").textContent = project.name;
    byId("backlog-view").hidden = false; byId("backlog-title").focus(); await load(0);
  }, close, clear };
}
