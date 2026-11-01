import { isPermissions, ROLE_NAMES } from "./permissions.js";

const uuid = /^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i;
export function isProject(p) {
  return p !== null && typeof p === "object" && typeof p.id === "string" && uuid.test(p.id)
    && typeof p.owner_id === "string" && uuid.test(p.owner_id)
    && typeof p.name === "string" && p.name.trim().length > 0 && Array.from(p.name).length <= 120
    && typeof p.description === "string" && Array.from(p.description).length <= 2000
    && (p.objective === undefined || (typeof p.objective === "string" && Array.from(p.objective).length <= 2000))
    && (p.permissions === undefined || isPermissions(p.permissions))
    && typeof p.created_at === "string" && Number.isFinite(Date.parse(p.created_at));
}
export const isId = value => typeof value === "string" && uuid.test(value);
export const isDate = value => typeof value === "string" && Number.isFinite(Date.parse(value));
export const isRoleKey = role => typeof role === "string" && (Object.hasOwn(ROLE_NAMES, role) || (role.startsWith("custom:") && isId(role.slice(7))));
export const rolesValid = (roles, owner = false) => Array.isArray(roles) && new Set(roles).size === roles.length
  && roles.every(role => isRoleKey(role) && (owner || role !== "owner"));
export const isMember = value => value && isId(value.user_id) && typeof value.is_owner === "boolean"
  && rolesValid(value.roles, value.is_owner) && (value.expires_at === null || isDate(value.expires_at));
export const isAccess = (value, projectId) => value && value.project_id === projectId && isId(value.user_id)
  && typeof value.is_owner === "boolean" && rolesValid(value.roles, value.is_owner) && isPermissions(value.permissions);
export function isPage(p) {
  return p !== null && typeof p === "object" && Array.isArray(p.items) && p.items.every(isProject)
    && Number.isSafeInteger(p.total) && p.total >= 0 && Number.isSafeInteger(p.limit)
    && p.limit >= 1 && p.limit <= 100 && Number.isSafeInteger(p.offset) && p.offset >= 0
    && p.items.length <= p.limit && p.items.length <= p.total;
}

export const isRolesPage = value => value && Array.isArray(value.items)
  && value.items.length >= 3 && new Set(value.items.map(role => role.key)).size === value.items.length
  && ["product_owner", "project_manager", "developer"].every(key => value.items.some(role => role.key === key))
  && value.items.every(role => isRoleKey(role.key) && role.key !== "owner"
    && typeof role.name === "string" && isPermissions(role.permissions));

export const isMemberPage = (value, limit, offset) => value && Array.isArray(value.items)
  && value.items.every(isMember) && value.limit === limit && value.offset === offset
  && Number.isInteger(value.total) && value.total >= 0
  && value.items.length <= Math.min(limit, Math.max(0, value.total - offset));

export const isInvitationCreated = (value, projectId, draft) => value && isId(value.id)
  && value.project_id === projectId && value.user_id === draft.user_id && rolesValid(value.roles)
  && typeof value.code === "string" && /^[\w-]{32,200}$/.test(value.code)
  && isDate(value.code_expires_at) && (value.expires_at === null || isDate(value.expires_at));
