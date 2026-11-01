// DOM adapters shared by the workspace screens; no transport or business rules.
export function el(tag, text, attributes = {}) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = String(text);
  for (const [key, value] of Object.entries(attributes)) {
    if (key === "class") node.className = value;
    else if (key === "hidden") node.hidden = Boolean(value);
    else node.setAttribute(key, String(value));
  }
  return node;
}

export function action(text, callback, { primary = false, label = text } = {}) {
  const button = el("button", text, { type: "button", class: `button ${primary ? "button-primary" : "button-secondary"}`, "aria-label": label });
  button.addEventListener("click", callback);
  return button;
}

export const textDate = value => value && Number.isFinite(Date.parse(value))
  ? new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value)) : "Não informado";

export function section(title, description) {
  const node = el("section", null, { class: "workspace-section" });
  node.append(el("h2", title));
  if (description) node.append(el("p", description, { class: "intro" }));
  return node;
}

export function form(prefix, descriptors, submitLabel, onSubmit, { secondaryLabel, onSecondary } = {}) {
  const node = el("form", null, { class: "workspace-form", method: "post" });
  const inputs = {};
  for (const descriptor of descriptors) {
    const { name, label, type = "text", value = "", hint, required = false, options = {}, wide = false } = descriptor;
    const id = `${prefix}-${name}`;
    const container = el("div", null, { class: `field${wide ? " field-wide" : ""}${type === "checkbox" ? " check-field" : ""}` });
    let input;
    if (type === "textarea") { input = el("textarea", null, { rows: descriptor.rows || 3 }); }
    else if (type === "select" || type === "multiselect") {
      input = el("select");
      if (type === "multiselect") input.multiple = true;
      const entries = Array.isArray(options) ? options.map(item => typeof item === "string" ? [item, item] : [item.value, item.label]) : Object.entries(options);
      for (const [key, caption] of entries) input.append(el("option", caption, { value: key }));
    } else input = el("input", null, { type });
    input.id = id; input.name = name; input.required = required;
    if (type === "checkbox") input.checked = Boolean(value);
    else if (type === "multiselect") for (const option of input.options) option.selected = (value || []).includes(option.value);
    else input.value = value ?? "";
    if (descriptor.min !== undefined) input.min = descriptor.min;
    if (descriptor.max !== undefined) input.max = descriptor.max;
    if (descriptor.step !== undefined) input.step = descriptor.step;
    if (descriptor.maxLength !== undefined) input.maxLength = descriptor.maxLength;
    if (descriptor.minLength !== undefined) input.minLength = descriptor.minLength;
    if (descriptor.autocomplete) input.autocomplete = descriptor.autocomplete;
    if (descriptor.readOnly) input.readOnly = true;
    const labelNode = el("label", label, { for: id });
    if (type === "checkbox") container.append(input, labelNode);
    else container.append(labelNode, input);
    if (hint) {
      const help = el("p", hint, { id: `${id}-hint`, class: "field-hint" });
      input.setAttribute("aria-describedby", help.id); container.append(help);
    }
    inputs[name] = input; node.append(container);
  }
  const buttons = el("div", null, { class: "form-actions field-wide" });
  const submit = el("button", submitLabel, { type: "submit", class: "button button-primary" });
  buttons.append(submit);
  if (secondaryLabel) buttons.append(action(secondaryLabel, () => onSecondary?.(values())));
  node.append(buttons);
  function values() {
    return Object.fromEntries(Object.entries(inputs).map(([key, input]) => [key,
      input.type === "checkbox" ? input.checked : input.multiple ? [...input.selectedOptions].map(option => option.value) : input.value]));
  }
  node.addEventListener("submit", event => { event.preventDefault(); if (node.checkValidity()) onSubmit(values(), result); });
  const result = { node, inputs, values, reset: () => node.reset(),
    busy(value) { for (const control of node.elements) control.disabled = value; node.setAttribute("aria-busy", String(value)); } };
  return result;
}

export function rows(items, columns, { empty = "Ainda não há registros para exibir.", caption = "Registros", actions } = {}) {
  const container = el("div", null, { class: "workspace-list" });
  if (!items.length) { container.append(el("p", empty, { class: "projects-empty" })); return container; }
  const table = el("table", null, { class: "workspace-table" });
  container.tabIndex = 0; container.setAttribute("role", "region");
  container.setAttribute("aria-label", `${caption}; role horizontalmente em telas pequenas`);
  table.append(el("caption", caption, { class: "visually-hidden" }));
  const head = el("thead"), header = el("tr");
  for (const column of columns) header.append(el("th", column.label, { scope: "col" }));
  if (actions) header.append(el("th", "Ações", { scope: "col" }));
  head.append(header); table.append(head);
  const body = el("tbody");
  for (const item of items) {
    const row = el("tr");
    for (const column of columns) {
      const cell = el("td"), value = typeof column.value === "function" ? column.value(item) : item[column.key];
      if (value instanceof Node) cell.append(value); else cell.textContent = value === undefined || value === null || value === "" ? "Não informado" : String(value);
      if (column.numeric) cell.className = "numeric";
      row.append(cell);
    }
    if (actions) {
      const cell = el("td", null, { class: "row-actions" });
      for (const control of actions(item) || []) if (control) cell.append(control);
      row.append(cell);
    }
    body.append(row);
  }
  table.append(body); container.append(table);
  return container;
}

export function details(values) {
  const list = el("dl", null, { class: "workspace-details" });
  for (const [label, value] of Object.entries(values)) {
    const group = el("div"); group.append(el("dt", label), el("dd", value === undefined || value === null || value === "" ? "Não informado" : String(value))); list.append(group);
  }
  return list;
}

export function secret(text, label, onDismiss) {
  const area = section(label, "Guarde em um local seguro. Esta informação será ocultada ao sair desta tela.");
  const input = el("textarea", null, { rows: 4, "aria-label": label, readonly: "" });
  input.value = Array.isArray(text) ? text.join("\n") : text;
  area.append(input, action("Ocultar informação sensível", () => { input.value = ""; area.remove(); onDismiss?.(); }));
  return area;
}
