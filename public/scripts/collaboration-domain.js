export const ROLE_KEYS = Object.freeze(["product_owner", "project_manager", "developer"]);

export function membershipExpiry(value, now = Date.now()) {
  if (!value) return null;
  const date = new Date(value);
  if (!Number.isFinite(date.valueOf()) || date.valueOf() <= now) {
    throw new Error("Informe uma data de expiração futura ou deixe o campo vazio.");
  }
  return date.toISOString();
}

export const invitationDeadline = (codeExpiresAt, memberExpiresAt) =>
  Math.min(Date.parse(codeExpiresAt), memberExpiresAt ? Date.parse(memberExpiresAt) : Infinity);
