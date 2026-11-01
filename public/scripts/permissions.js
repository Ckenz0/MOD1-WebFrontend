export const PERMISSIONS = Object.freeze([
  "project:read", "project:update", "project:delete", "project:members:read", "project:members:manage",
  "backlog:read", "backlog:create", "backlog:update", "backlog:update_status",
  "project:lifecycle:manage", "project:audit:read", "project:roles:manage", "project:teams:manage", "backlog:reorder",
]);
export const ROLE_NAMES = Object.freeze({
  product_owner: "Product Owner", project_manager: "PM/Scrum Master", developer: "Desenvolvedor", owner: "Proprietário",
});
export const PERMISSION_NAMES = Object.freeze({
  "project:read": "Consultar projeto", "project:update": "Editar projeto", "project:delete": "Excluir projeto",
  "project:members:read": "Consultar integrantes", "project:members:manage": "Gerenciar integrantes",
  "backlog:read": "Consultar backlog", "backlog:create": "Criar histórias", "backlog:update": "Refinar histórias",
  "backlog:update_status": "Atualizar andamento",
  "project:lifecycle:manage": "Gerenciar situação do projeto", "project:audit:read": "Consultar auditoria",
  "project:roles:manage": "Gerenciar papéis", "project:teams:manage": "Vincular equipes", "backlog:reorder": "Ordenar backlog",
});
export const isPermissions = value => Array.isArray(value) && new Set(value).size === value.length
  && value.every(p => PERMISSIONS.includes(p));
export function permissionsFor(project, userId) {
  const permissions = project.permissions !== undefined
    ? isPermissions(project.permissions) ? [...project.permissions] : []
    : userId && project.owner_id === userId ? [...PERMISSIONS] : [];
  if (project.archived || ["suspended", "completed"].includes(project.status)) {
    const dataWrites = ["project:update", "backlog:create", "backlog:update", "backlog:update_status", "backlog:reorder"];
    return permissions.filter(permission => !dataWrites.includes(permission));
  }
  return permissions;
}
