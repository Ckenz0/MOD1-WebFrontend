const id = value => Number.isSafeInteger(value) && value > 0;
const text = (value, max) => typeof value === "string" && value.length > 0 && value.length <= max;
const types = new Set(["PDF", "MARKDOWN", "PNG", "JPEG"]);
const date = value => typeof value === "string" && Number.isFinite(Date.parse(value));
const page = value => value && Array.isArray(value.items) && value.items.length <= 100
  && Number.isSafeInteger(value.total) && value.total >= value.items.length && typeof value.truncated === "boolean";

export const artifactBinding = value => value === null || id(value);
export const isArtifactCatalog = value => page(value) && typeof value.enabled === "boolean"
  && value.items.every(item => id(item.id) && text(item.name, 300)
    && (item.description === null || typeof item.description === "string"));
export const isArtifactPage = value => page(value) && typeof value.enabled === "boolean"
  && artifactBinding(value.module3_project_id) && value.items.every(item => id(item.id)
    && item.project_id === value.module3_project_id && text(item.name, 300)
    && types.has(item.artifact_type) && id(item.version) && date(item.created_at));
export const isArtifactVersions = (value, binding, artifact) => page(value)
  && value.module3_project_id === binding && value.artifact_id === artifact
  && value.items.every(item => id(item.id) && item.artifact_id === artifact
    && id(item.version_number) && date(item.created_at));

export function artifactQuery(values = {}) {
  const search = String(values.search || "").trim(), artifact_type = values.artifact_type || "";
  if (search.length > 120 || (artifact_type && !types.has(artifact_type))) throw new TypeError("Filtro de arquivos inválido.");
  return { search, artifact_type };
}

export function artifactFilename(item) {
  if (!id(item?.id) || !types.has(item.artifact_type)) throw new TypeError("Arquivo inválido.");
  return `artifact-${item.id}.${({ PDF: "pdf", MARKDOWN: "md", PNG: "png", JPEG: "jpg" })[item.artifact_type]}`;
}
