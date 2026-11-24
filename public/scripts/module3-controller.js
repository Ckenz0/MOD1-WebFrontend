import { PlatformApiError } from "./api-errors.js";
import { artifactBinding, artifactFilename, artifactQuery, isArtifactCatalog, isArtifactPage, isArtifactVersions } from "./module3-domain.js";
import { artifactAssociationForm, artifactsPanel, saveArtifactFile } from "./module3-view.js";
import { el, action } from "./workspace-view.js";

export function renderArtifactsArea({ project, canEdit, run, updateProject, reload, content, query = {} }) {
  const base = `/projects/${project.id}/artifacts`, filters = artifactQuery(query);
  let binding = project.module3_project_id ?? null;
  const cleanups = new Set();
  const receive = (request, path, validate) => request("projects", "GET", path, undefined, { validate, timeout: 35000 });
  const scoped = (item, operation) => `${base}/${item.id}/${operation}?module3_project_id=${binding}`;
  const panel = artifactsPanel({ query: filters,
    onFilter: values => reload(artifactQuery(values)),
    onVersions: item => run(async (request, { assertCurrent }) => {
      panel.showVersions(item);
      try {
        const result = await receive(request, scoped(item, "versions"), value => isArtifactVersions(value, binding, item.id));
        panel.showVersions(item, result);
      } catch (error) {
        if (!recover(error, assertCurrent)) panel.versionsMessage(item, "As versões estão indisponíveis no momento.");
      }
    }, "", { inlineStatus: true }),
    onDownload: item => run(async (_request, { download, assertCurrent }) => {
      panel.message("Préparando o arquivo para download…");
      try {
        const blob = await download(scoped(item, "download"));
        assertCurrent();
        cleanups.add(saveArtifactFile(blob, artifactFilename(item)));
        panel.message("Download da versão atual iniciado.");
      } catch (error) {
        if (!recover(error, assertCurrent)) panel.message("Não foi possível baixar o arquivo. Tente novamente.");
      }
    }, "", { inlineStatus: true }),
  });
  content.replaceChildren(panel.node);
  const title = panel.node.querySelector("h2"); title.tabIndex = -1; title.focus();

  function recover(error, assertCurrent) {
    assertCurrent();
    if (["unauthorized", "cancelled"].includes(error.kind)) throw error;
    if (["forbidden", "not-found", "conflict"].includes(error.kind)) {
      panel.block(error.kind === "conflict" ? "O vínculo do projeto mudou. Atualize a consulta."
        : "O arquivo ou o acesso ao projeto não está mais disponível. Atualize a consulta.");
      panel.retry(() => reload(filters));
      return true;
    }
    if (!(error instanceof PlatformApiError)) throw error;
    return false;
  }

  async function saveBinding(value) {
    let saved = false;
    await run(async (request, { assertCurrent }) => {
      if (!artifactBinding(value)) throw new TypeError("Selecione um projeto válido.");
      try {
        const next = await request("projects", "PATCH", `/projects/${project.id}`, { module3_project_id: value }, {
          validate: result => result?.id === project.id && result.module3_project_id === value && Array.isArray(result.permissions),
        });
        updateProject(next);
        saved = true;
      } catch (error) {
        if (!recover(error, assertCurrent)) {
          panel.block("Não foi possível confirmar a atualização do vínculo. Atualize a consulta antes de tentar novamente.");
          panel.retry(() => reload(filters));
        }
      }
    }, "Vínculo atualizado.", { inlineStatus: true });
    if (saved && panel.node.isConnected) reload(filters);
  }

  function association() {
    panel.association.replaceChildren();
    if (binding !== null) panel.association.append(el("p", `Projeto vinculado no Módulo 3: #${binding}.`));
    if (!canEdit) return;
    panel.association.append(action("Escolher projeto", () => run(async (request, { assertCurrent }) => {
      try {
        const result = await receive(request, base + "/catalog", isArtifactCatalog);
        if (!result.enabled) { panel.message("A consulta de artefatos está desativada."); return; }
        if (!result.items.length) { panel.message("Nenhum projeto disponível no Módulo 3."); return; }
        const editor = artifactAssociationForm(result, binding,
          values => saveBinding(Number(values.module3_project_id)));
        panel.association.replaceChildren(editor.node);
        editor.inputs.module3_project_id.focus();
      } catch (error) {
        if (!recover(error, assertCurrent)) panel.message("O catálogo está indisponível no momento.");
      }
    }, "", { inlineStatus: true })));
    if (binding !== null) panel.association.append(action("Desvincular projeto", () => saveBinding(null)));
  }

  association();
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.artifact_type) params.set("artifact_type", filters.artifact_type);
  run(async (request, { assertCurrent }) => {
    try {
      const result = await receive(request, base + (params.size ? `?${params}` : ""), isArtifactPage);
      binding = result.module3_project_id;
      panel.show(result);
      association();
    } catch (error) {
      if (recover(error, assertCurrent)) return;
      panel.message("Os artefatos estão indisponíveis no momento.");
      panel.retry(() => reload(filters));
    }
  }, "", { inlineStatus: true });
  return () => { for (const cleanup of cleanups) cleanup(); cleanups.clear(); };
}
