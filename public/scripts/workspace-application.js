import { permissionsFor } from "./permissions.js";

// Composite reads are use cases; screens keep only rendering and view lifecycle.
export function createWorkspaceApplication({ projects, backlog }) {
  return {
    async loadBacklog(token, projectId, userId, options = {}) {
      const [project, page] = await Promise.all([
        projects.get(token, projectId, { signal: options.signal }),
        backlog.list(token, projectId, options),
      ]);
      return { project, page, permissions: permissionsFor(project, userId) };
    },
    async loadMembers(token, projectId, userId, options = {}) {
      const [project, roles, members] = await Promise.all([
        projects.get(token, projectId, { signal: options.signal }),
        projects.roles(token, projectId, { signal: options.signal }),
        projects.members(token, projectId, options),
      ]);
      return { project: { ...project, permissions: permissionsFor(project, userId) }, roles: roles.items, members };
    },
  };
}
