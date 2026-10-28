import { ApiError } from "./api.js";

const byId = id => document.getElementById(id);
const seniorities = ["not_informed", "junior", "mid", "senior", "lead"];
const levels = ["Conhecimento básico", "Iniciante", "Intermediário", "Avançado", "Especialista"];

export function createProfessionalProfile({ api, getToken, getUserId, onUnauthorized }) {
  let epoch = 0, controller = null, busy = false, saved = null;
  const form = byId("professional-profile-form");
  function status(text = "", error = false) {
    const node = byId("professional-profile-status");
    node.textContent = text; node.dataset.tone = error ? "error" : "notice"; node.hidden = !text;
  }
  function setBusy(value) {
    busy = value; form.setAttribute("aria-busy", String(value));
    for (const element of form.elements) element.disabled = value;
    byId("open-professional-profile").disabled = value;
    byId("profile-save").textContent = value ? "Aguarde…" : "Salvar perfil";
  }
  function addSkill(skill = { name: "", level: 1 }) {
    const list = byId("profile-skills");
    if (list.children.length >= 30) { status("Você pode informar até 30 competências.", true); return; }
    const row = document.createElement("div"); row.className = "skill-row";
    const nameField = document.createElement("div"), levelField = document.createElement("div");
    nameField.className = levelField.className = "field";
    const nameLabel = document.createElement("label"), name = document.createElement("input");
    name.type = "text"; name.value = skill.name; name.dataset.skillName = "";
    const levelLabel = document.createElement("label"), level = document.createElement("select");
    level.dataset.skillLevel = "";
    for (const [index, text] of levels.entries()) {
      const option = document.createElement("option"); option.value = String(index + 1); option.textContent = `${index + 1} — ${text}`; level.append(option);
    }
    level.value = String(skill.level);
    const remove = document.createElement("button"); remove.type = "button"; remove.className = "text-button"; remove.textContent = "Remover";
    remove.addEventListener("click", () => { if (!busy) { row.remove(); relabel(); byId("profile-add-skill").focus(); } });
    nameField.append(nameLabel, name); levelField.append(levelLabel, level); row.append(nameField, levelField, remove); list.append(row);
    relabel();
  }
  function relabel() {
    [...byId("profile-skills").children].forEach((row, index) => {
      const fields = row.querySelectorAll("input, select"), labels = row.querySelectorAll("label");
      fields[0].id = `profile-skill-name-${index}`; fields[1].id = `profile-skill-level-${index}`;
      labels[0].htmlFor = fields[0].id; labels[0].textContent = `Competência ${index + 1}`;
      labels[1].htmlFor = fields[1].id; labels[1].textContent = `Domínio da competência ${index + 1}`;
      row.querySelector("button").setAttribute("aria-label", `Remover competência ${index + 1}`);
    });
  }
  function render(profile) {
    saved = profile;
    byId("profile-summary").value = profile.summary;
    byId("profile-seniority").value = profile.seniority;
    byId("profile-availability").value = String(profile.weekly_availability_hours);
    byId("profile-skills").replaceChildren(); profile.skills.forEach(addSkill);
  }
  async function run(action, onSuccess) {
    const token = getToken(), userId = getUserId();
    if (!token || !userId) { clear(); onUnauthorized(); return; }
    const current = ++epoch; controller?.abort(); controller = new AbortController();
    const valid = () => current === epoch && token === getToken() && userId === getUserId() && !byId("profile-view").hidden;
    setBusy(true); status("Carregando perfil…");
    try {
      const result = await action(token, userId, controller.signal);
      if (valid()) { status(); onSuccess(result); }
    } catch (error) {
      if (!valid() || error.kind === "cancelled") return;
      if (error.kind === "unauthorized") { clear(); onUnauthorized(); return; }
      status(error instanceof ApiError ? error.message : "Não foi possível carregar o perfil. Tente novamente.", true);
    } finally { if (current === epoch) { controller = null; setBusy(false); } }
  }
  function clear() {
    epoch += 1; controller?.abort(); controller = null; saved = null;
    form.reset(); byId("profile-skills").replaceChildren(); status();
    byId("professional-profile").hidden = true; byId("open-professional-profile").hidden = false; setBusy(false);
  }
  byId("open-professional-profile").addEventListener("click", () => {
    if (busy) return;
    byId("professional-profile").hidden = false; byId("open-professional-profile").hidden = true;
    byId("professional-profile-title").focus();
    run((token, id, signal) => api.getProfile(token, id, { signal }), render);
  });
  byId("profile-add-skill").addEventListener("click", () => {
    if (!busy) { addSkill(); byId("profile-skills").lastElementChild?.querySelector("input").focus(); }
  });
  byId("profile-cancel").addEventListener("click", () => { if (!busy) { clear(); byId("open-professional-profile").focus(); } });
  form.addEventListener("submit", event => {
    event.preventDefault(); if (busy || !saved) return;
    const summary = byId("profile-summary").value, seniority = byId("profile-seniority").value;
    const hours = byId("profile-availability").value, availability = Number(hours);
    if (Array.from(summary).length > 2000 || !seniorities.includes(seniority) || hours === ""
        || !Number.isInteger(availability) || availability < 0 || availability > 168) {
      status("Confira o resumo (até 2000 caracteres) e a disponibilidade (0 a 168 horas inteiras).", true); return;
    }
    const skills = [], names = new Set();
    for (const row of byId("profile-skills").children) {
      const nameInput = row.querySelector("input"), name = nameInput.value.normalize("NFC").trim();
      const level = Number(row.querySelector("select").value), normalized = name.toLowerCase();
      if (!name || Array.from(name).length > 80 || names.has(normalized) || !Number.isInteger(level) || level < 1 || level > 5) {
        nameInput.focus(); status("Informe competências distintas com nome de até 80 caracteres e domínio de 1 a 5.", true); return;
      }
      names.add(normalized); skills.push({ name, level });
    }
    run((token, id, signal) => api.updateProfile(token, id, { summary, seniority,
      weekly_availability_hours: availability, skills }, { signal }), result => { render(result); status("Perfil atualizado. Suas informações foram salvas."); });
  });
  return { clear };
}
