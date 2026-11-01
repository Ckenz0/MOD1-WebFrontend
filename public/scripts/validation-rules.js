// Pure value validation; field elements and browser validity belong to the view adapter.
const count = value => Array.from(value).length;

export function emailValueError(value, typeMismatch = !/^[^\s@]+@[^\s@]+$/.test(value.trim())) {
  if (!value.trim()) return "Informe seu e-mail.";
  const domain = value.trim().split("@").at(-1) || "";
  return typeMismatch || !domain.includes(".") || domain.endsWith(".") || count(value.trim()) > 320
    ? "Informe um e-mail válido, como voce@exemplo.com." : "";
}

export const loginPasswordValueError = value => value ? "" : "Informe sua senha.";
export function nameValueError(value) {
  const length = count(value.trim());
  return length >= 1 && length <= 120 ? "" : "Informe um nome de até 120 caracteres.";
}

export function newPasswordValueError(value, { min_length = 12, max_length = 128 } = {}) {
  const length = count(value);
  return length >= min_length && length <= max_length ? "" : `Use uma senha com ${min_length} a ${max_length} caracteres.`;
}

export function confirmationValueError(value, expected) {
  if (!value) return "Confirme sua senha.";
  return value === expected ? "" : "As senhas precisam ser iguais, incluindo os espaços.";
}
