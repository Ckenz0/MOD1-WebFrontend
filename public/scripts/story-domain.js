// Pure story values and HTTP response contracts.
const uuid = /^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i;
// JS whitespace plus Python's NEL and information separators: same rules as StoryDraft.
export const trimStoryTitle = value => value.replace(/^[\s\u0085\u001c-\u001f]+|[\s\u0085\u001c-\u001f]+$/gu, "");
export const isId = value => typeof value === "string" && uuid.test(value);
const text = (value, max) => typeof value === "string" && Array.from(value).length <= max;
export function isStory(s, projectId, storyId) {
  return s !== null && typeof s === "object" && isId(s.id) && isId(s.created_by)
    && s.project_id === projectId && (!storyId || s.id === storyId)
    && text(s.title, 120) && trimStoryTitle(s.title).length > 0
    && text(s.description, 2000) && text(s.acceptance_criteria, 2000)
    && ["high", "medium", "low"].includes(s.priority) && ["todo", "in_progress", "done"].includes(s.status)
    && typeof s.created_at === "string" && Number.isFinite(Date.parse(s.created_at))
    && typeof s.updated_at === "string" && Number.isFinite(Date.parse(s.updated_at))
    && Date.parse(s.updated_at) >= Date.parse(s.created_at);
}
export function isPage(p, projectId, limit, offset) {
  return p !== null && typeof p === "object" && Array.isArray(p.items)
    && p.items.every(s => isStory(s, projectId)) && Number.isSafeInteger(p.total) && p.total >= 0
    && p.limit === limit && p.offset === offset && p.items.length <= limit
    && p.items.length <= Math.max(0, p.total - offset);
}

export function storyChange(saved, draft, permissions) {
  const change = { status: draft.status };
  if (!permissions.includes("backlog:update")) return change;
  change.priority = draft.priority;
  for (const field of ["title", "description", "acceptance_criteria"]) {
    const value = field === "title" ? trimStoryTitle(draft[field]) : draft[field];
    if (value !== saved[field]) change[field] = value;
  }
  return change;
}
