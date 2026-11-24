import { el, action, section, form, rows, textDate } from "./workspace-view.js";

export function artifactsPanel({ query, onFilter, onVersions, onDownload }) {
  const node = section("Artefatos", "Consulte os arquivos e as versões do projeto no Módulo 3.");
  const association = el("div", null, { class: "artifact-association" });
  const message = el("p", "Carregando artefatos…", { role: "status", "aria-live": "polite" });
  const filters = form("artifact-filters", [
    { name: "search", label: "Pesquisar arquivos", value: query.search, maxLength: 120 },
    { name: "artifact_type", label: "Tipo de arquivo", type: "select", value: query.artifact_type,
      options: { "": "Todos os tipos", PDF: "PDF", MARKDOWN: "Markdown", PNG: "PNG", JPEG: "JPEG" } },
  ], "Filtrar arquivos", onFilter);
  filters.node.hidden = true;
  const files = el("div", null, { class: "artifact-files" }), versions = section("Versões do arquivo");
  versions.classList.add("artifact-versions");
  versions.hidden = true;
  node.append(association, filters.node, message, files, versions);
  return {
    node, association,
    message(value) { message.textContent = value; message.hidden = !value; },
    block(value) {
      association.replaceChildren(); files.replaceChildren(); versions.replaceChildren();
      versions.hidden = true; filters.node.hidden = true; this.message(value);
    },
    show(result) {
      files.replaceChildren(); versions.hidden = true;
      filters.node.hidden = !result.enabled || result.module3_project_id === null;
      if (!result.enabled) { this.message("A consulta de artefatos está desativada."); return; }
      if (result.module3_project_id === null) { this.message("Nenhum projeto do Módulo 3 vinculado."); return; }
      this.message(result.truncated ? `Exibindo ${result.items.length} de ${result.total} arquivos. Refine os filtros para encontrar outros arquivos.` : "");
      const listing = rows(result.items, [
        { label: "Arquivo", key: "name" }, { label: "Tipo", key: "artifact_type" },
        { label: "Versão atual", key: "version", numeric: true },
        { label: "Criado em", value: item => textDate(item.created_at) },
      ], { caption: "Arquivos do projeto", empty: "Nenhum arquivo encontrado.", actions: item => [
        action("Versões", () => onVersions(item)), action("Baixar versão atual", () => onDownload(item)),
      ] });
      const labels = ["Arquivo", "Tipo", "Versão atual", "Criado em", "Ações"];
      listing.querySelector("table")?.setAttribute("role", "table");
      for (const row of listing.querySelectorAll("tbody tr")) {
        row.setAttribute("role", "row");
        [...row.children].forEach((cell, i) => { cell.dataset.label = labels[i]; cell.setAttribute("role", "cell"); });
      }
      files.append(listing);
    },
    showVersions(item, result) {
      versions.hidden = false;
      versions.replaceChildren(el("h3", `Versões de ${item.name}`));
      if (!result) { versions.append(el("p", "Carregando versões…", { role: "status" })); return; }
      if (!result.items.length) versions.append(el("p", "Nenhuma versão disponível."));
      const list = el("ol");
      for (const version of result.items) list.append(el("li", `Versão ${version.version_number} — ${textDate(version.created_at)}`));
      versions.append(list);
      if (result.truncated) versions.append(el("p", `Exibindo ${result.items.length} de ${result.total} versões.`));
    },
    versionsMessage(item, value) {
      versions.hidden = false;
      versions.replaceChildren(el("h3", `Versões de ${item.name}`), el("p", value, { role: "status" }));
    },
    retry(callback) { files.replaceChildren(action("Tentar novamente", callback)); },
  };
}

export function artifactAssociationForm(catalog, binding, onSubmit) {
  const options = [{ value: "", label: "Selecione o projeto correspondente" },
    ...catalog.items.map(item => ({ value: String(item.id), label: `${item.name} (#${item.id})` }))];
  const editor = form("artifact-association", [{ name: "module3_project_id", label: "Projeto do Módulo 3",
    type: "select", required: true, options, value: binding === null ? "" : String(binding),
    hint: "Escolha o projeto que corresponde a este espaço de trabalho." }],
  "Vincular projeto", onSubmit);
  if (catalog.truncated) editor.node.append(el("p", `Exibindo ${catalog.items.length} de ${catalog.total} projetos. Se não encontrar o seu, consulte o responsável pelo Módulo 3.`));
  return editor;
}

export function saveArtifactFile(blob, filename) {
  const url = URL.createObjectURL(blob), anchor = el("a", null, { href: url, download: filename, hidden: true });
  document.body.append(anchor);
  try { anchor.click(); } finally { anchor.remove(); }
  let timer;
  const cleanup = () => { clearTimeout(timer); URL.revokeObjectURL(url); };
  timer = setTimeout(cleanup, 1000);
  return cleanup;
}
