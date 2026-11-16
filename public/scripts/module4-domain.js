// Pure values for item-scoped code reviews. Credentials belong to the backend.
import { isId } from "./story-domain.js";

export const MODULE4_ARCHITECTURES = { multicamadas: "Multicamadas", clean: "Clean", mvc: "MVC", hexagonal: "Hexagonal", onion: "Onion" };
export const REVIEW_STATES = { pending: "Em processamento", succeeded: "Análise recebida", failed: "Análise falhou", blocked: "Análise bloqueada", uncertain: "Resultado incerto" };
export const REVIEW_EFFECTS = { started: "Item iniciado; conclusão manual.", preserved: "Situação preservada; conclusão manual.", not_applied_conflict: "Item alterado durante a análise; situação preservada.", not_applied_access: "Acesso alterado; situação preservada.", not_applied_error: "Situação preservada; análise não aplicada." };

export function module4Draft(values) {
  const { request_id, expected_version, arquitetura = "multicamadas", usar_ia = false } = values;
  if (!isId(request_id) || !Number.isSafeInteger(expected_version) || expected_version < 1
      || !Object.hasOwn(MODULE4_ARCHITECTURES, arquitetura) || typeof usar_ia !== "boolean") throw new TypeError("Confira a versão do item e a arquitetura da revisão.");
  const pr_url = values.pr_url?.trim(), arquivos = values.arquivos?.length ? values.arquivos : undefined;
  if (Boolean(pr_url) === Boolean(arquivos)) throw new TypeError("Informe um Pull Request ou arquivos Python, escolhendo apenas uma origem.");
  if (pr_url && (pr_url.length > 500 || !/^https:\/\/github\.com\/[^/\s%\\?#]+\/[^/\s%\\?#]+\/pull\/[0-9]+\/?$/.test(pr_url)
      || !Number(pr_url.split("/").filter(Boolean).at(-1)) || pr_url.split("/").some(part => [".", ".."].includes(part)))) throw new TypeError("Use a URL HTTPS de um Pull Request do GitHub.");
  if (arquivos) {
    if (arquivos.length > 20) throw new TypeError("Selecione no máximo 20 arquivos Python.");
    const paths = new Set(); let bytes = 0;
    for (const file of arquivos) {
      const path = file.caminho;
      if (typeof path !== "string" || !path.endsWith(".py") || path.length > 240 || path.startsWith("/")
          || /[\\:\u0000-\u001f\u007f]/.test(path) || path.split("/").includes("..") || paths.has(path)
          || typeof file.conteudo !== "string") throw new TypeError("Use nomes relativos de arquivos .py, sem caminhos repetidos.");
      paths.add(path); bytes += new TextEncoder().encode(file.conteudo).length;
    }
    if (bytes > 100000) throw new TypeError("Os arquivos juntos devem ter até 100.000 bytes UTF-8.");
  }
  return { request_id, expected_version, arquitetura, usar_ia, ...(pr_url ? { pr_url } : { arquivos }) };
}

export function isModule4Record(row, projectId, itemId) {
  return Boolean(row && isId(row.id) && isId(row.request_id) && row.project_id === projectId && row.item_id === itemId
    && Object.hasOwn(REVIEW_STATES, row.status) && Object.hasOwn(REVIEW_EFFECTS, row.status_effect)
    && Object.hasOwn(MODULE4_ARCHITECTURES, row.arquitetura) && typeof row.usar_ia === "boolean"
    && ["files", "pull_request"].includes(row.source?.kind) && Array.isArray(row.source.files)
    && row.source.files.every(path => typeof path === "string")
    && Number.isFinite(Date.parse(row.created_at)) && Number.isFinite(Date.parse(row.updated_at))
    && (row.result === null || (row.result && isId(row.result.id) && Array.isArray(row.result.achados)
      && typeof row.result.markdown === "string" && typeof row.result.ia?.texto === "string")));
}

export function isModule4Page(page, projectId, itemId, offset) {
  return Boolean(page && typeof page.enabled === "boolean" && Array.isArray(page.items)
    && page.items.every(row => isModule4Record(row, projectId, itemId))
    && Number.isSafeInteger(page.total) && page.total >= 0 && page.limit === 20 && page.offset === offset
    && page.items.length <= 20 && page.items.length <= Math.max(0, page.total - offset));
}
