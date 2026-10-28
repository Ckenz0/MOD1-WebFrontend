const byId = (id) => document.getElementById(id);
const count = (value) => Array.from(value).length;

export function createFormValidation(formId, rules) {
  const touched = new Set();
  function validate(id) {
    const input = byId(id);
    const error = rules[id](input);
    const note = byId(`${id}-error`);
    input.setAttribute("aria-invalid", String(Boolean(error)));
    note.textContent = error;
    note.hidden = !error;
    return !error;
  }
  for (const id of Object.keys(rules)) {
    byId(id).addEventListener("blur", (event) => {
      touched.add(id);
      // Let submit validate everything without moving its button during pointerdown.
      if (event.relatedTarget?.form === byId(formId) && event.relatedTarget.type === "submit") return;
      validate(id);
    });
    byId(id).addEventListener("input", () => {
      if (touched.has(id)) validate(id);
      if (id === "register-password" && touched.has("register-confirm")) validate("register-confirm");
    });
  }
  return {
    enable() { byId(formId).noValidate = true; },
    validate() {
      let firstInvalid;
      for (const id of Object.keys(rules)) {
        touched.add(id);
        if (!validate(id) && !firstInvalid) firstInvalid = byId(id);
      }
      firstInvalid?.focus();
      return !firstInvalid;
    },
    clear() {
      touched.clear();
      for (const id of Object.keys(rules)) {
        byId(id).removeAttribute("aria-invalid");
        byId(`${id}-error`).hidden = true;
        byId(`${id}-error`).textContent = "";
      }
    },
  };
}

export function emailError(input) {
  if (!input.value.trim()) return "Informe seu e-mail.";
  const domain = input.value.trim().split("@").at(-1) || "";
  if (input.validity.typeMismatch || !domain.includes(".") || domain.endsWith(".")
      || count(input.value.trim()) > 320) return "Informe um e-mail válido, como voce@exemplo.com.";
  return "";
}

export function loginPasswordError(input) {
  return input.value ? "" : "Informe sua senha.";
}

export function nameError(input) {
  const length = count(input.value.trim());
  return length >= 1 && length <= 120 ? "" : "Informe um nome de até 120 caracteres.";
}

export function newPasswordError(input, { min_length = 12, max_length = 128 } = {}) {
  const length = count(input.value);
  return length >= min_length && length <= max_length ? "" : `Use uma senha com ${min_length} a ${max_length} caracteres.`;
}

export function confirmationError(input) {
  if (!input.value) return "Confirme sua senha.";
  return input.value === byId("register-password").value ? "" : "As senhas precisam ser iguais, incluindo os espaços.";
}
