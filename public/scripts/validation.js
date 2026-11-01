import { emailValueError, loginPasswordValueError, nameValueError, newPasswordValueError, confirmationValueError } from "./validation-rules.js";

const byId = (id) => document.getElementById(id);


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

// Existing field-based exports remain adapters for the presentation layer.
export const emailError = input => emailValueError(input.value, input.validity.typeMismatch);
export const loginPasswordError = input => loginPasswordValueError(input.value);
export const nameError = input => nameValueError(input.value);
export const newPasswordError = (input, policy) => newPasswordValueError(input.value, policy);
export const confirmationError = input => confirmationValueError(input.value, byId("register-password").value);
