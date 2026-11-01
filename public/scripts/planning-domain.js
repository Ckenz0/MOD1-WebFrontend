import { isId } from "./project-domain.js";

export const PROJECT_STATUSES = Object.freeze({ planned: "Planejado", active: "Ativo", suspended: "Suspenso", completed: "Concluído" });
export const MOSCOW = Object.freeze({ must: "Must · essencial", should: "Should · importante", could: "Could · desejável", wont: "Won't · fora desta entrega" });
export const ITEM_KINDS = Object.freeze({ story: "História", task: "Tarefa", epic: "Épico" });
export const ITEM_STATUSES = Object.freeze({ todo: "A fazer", in_progress: "Em andamento", done: "Concluído" });

export function listValues(value = "") {
  const values = Array.isArray(value) ? value : String(value).split(/[,\n]/);
  const seen = new Set();
  return values.map(item => item.normalize("NFC").trim()).filter(item => {
    const key = item.toLocaleLowerCase("pt-BR");
    if (!item || seen.has(key)) return false;
    seen.add(key); return true;
  });
}

export function decimalValue(value, label = "Valor") {
  if (value === undefined || value === null || value === "") return null;
  const text = String(value).trim().replace(",", ".");
  if (!/^\d{1,15}(?:\.\d{1,4})?$/.test(text)) throw new TypeError(`${label}: informe um número não negativo, sem separador de milhar.`);
  return text;
}

function dateValue(value) {
  if (!value) return null;
  const parsed = new Date(value + "T00:00:00Z");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(parsed.valueOf()) || parsed.toISOString().slice(0, 10) !== value) throw new TypeError("Informe uma data válida.");
  return value;
}

export function projectDetails(values) {
  const start = dateValue(values.planned_start), end = dateValue(values.planned_end);
  if (start && end && end < start) throw new TypeError("A data de término não pode ser anterior ao início.");
  const amount = decimalValue(values.budget_amount, "Orçamento");
  if (amount !== null && !/^\d+(?:\.\d{1,2})?$/.test(amount)) throw new TypeError("Informe o orçamento com até duas casas decimais.");
  return { scope: values.scope || "", budget_amount: amount, budget_currency: (values.budget_currency || "BRL").toUpperCase(),
    tags: listValues(values.tags), planned_start: start, planned_end: end, technology_stack: listValues(values.technology_stack),
    technical_requirements: listValues(values.technical_requirements), soft_skills: listValues(values.soft_skills), constraints: values.constraints || "" };
}

export function itemDraft(values) {
  const title = (values.title || "").trim();
  if (!title || Array.from(title).length > 120) throw new TypeError("Informe um título com até 120 caracteres.");
  const kind = values.kind || "story";
  if (!Object.hasOwn(ITEM_KINDS, kind)) throw new TypeError("Selecione o tipo do item.");
  const guided = [values.persona, values.action, values.benefit].some(value => Boolean(value?.trim()));
  if (guided && ![values.persona, values.action, values.benefit].every(value => Boolean(value?.trim()))) throw new TypeError("Preencha persona, ação e objetivo para usar o formato orientado.");
  if (values.is_blocked && !values.blocked_reason?.trim()) throw new TypeError("Informe o motivo do bloqueio.");
  const result = { kind, title, description: values.description || "", acceptance_criteria: values.acceptance_criteria || "",
    priority: values.priority || "medium", status: values.status || "todo", guided, persona: values.persona || "", action: values.action || "", benefit: values.benefit || "",
    moscow_priority: values.moscow_priority || null, estimate_value: decimalValue(values.estimate_value, "Estimativa"), estimate_unit: values.estimate_unit || null,
    is_blocked: Boolean(values.is_blocked), blocked_reason: values.is_blocked ? values.blocked_reason.trim() : "" };
  if (result.estimate_value !== null && !["points", "hours"].includes(result.estimate_unit)) throw new TypeError("Escolha pontos ou horas para a estimativa.");
  if (result.moscow_priority !== null && !Object.hasOwn(MOSCOW, result.moscow_priority)) throw new TypeError("Selecione uma prioridade MoSCoW válida.");
  for (const field of ["assignee_id", "epic_id", "parent_story_id"]) {
    const id = values[field]?.trim() || null;
    if (id && !isId(id)) throw new TypeError("Informe um ID de conta ou item válido.");
    result[field] = id;
  }
  return result;
}
