import { el, section, details, form, textDate } from "./workspace-view.js";
import { MODULE4_ARCHITECTURES, REVIEW_STATES, REVIEW_EFFECTS } from "./module4-domain.js";

export function module4Form(onSubmit) {
  const editor = form("code-review", [
    { name: "pr_url", label: "URL do Pull Request", type: "url", hint: "Pull Request HTTPS do GitHub. Deixe vazio ao enviar arquivos.", wide: true },
    { name: "arquitetura", label: "Arquitetura da revisão", type: "select", options: MODULE4_ARCHITECTURES, value: "multicamadas" },
    { name: "usar_ia", label: "Usar IA nesta revisão", type: "checkbox", value: false, hint: "Opcional. Habilita a análise com IA do provedor." },
  ], "Solicitar revisão", values => onSubmit(values, [...files.files]));
  editor.node.classList.add("module4-form");
  const field = el("div", null, { class: "field field-wide" });
  const files = el("input", null, { id: "code-review-files", type: "file", accept: ".py", multiple: "", "aria-describedby": "code-review-files-hint" });
  field.append(el("label", "Arquivos Python", { for: files.id }), files,
    el("p", "Até 20 arquivos .py, somando no máximo 100.000 bytes UTF-8. O código será enviado ao serviço de revisão.", { id: "code-review-files-hint", class: "field-hint" }));
  editor.node.insertBefore(field, editor.node.firstChild);
  return editor;
}

export function module4Record(row) {
  const panel = section(REVIEW_STATES[row.status]);
  panel.append(details({ "Solicitação": row.request_id, "Recebida em": textDate(row.created_at), "Atualizada em": textDate(row.updated_at),
    "Origem": row.source.kind === "pull_request" ? row.source.pr_url : row.source.files.join(", "),
    "Arquitetura": MODULE4_ARCHITECTURES[row.arquitetura], "IA solicitada": row.usar_ia ? "Sim" : "Não" }));
  panel.append(el("p", REVIEW_EFFECTS[row.status_effect]));
  if (row.error) panel.append(el("p", "O serviço não confirmou a análise. Consulte o estado registrado antes de solicitar novamente.", { class: "field-hint" }));
  if (row.result) {
    const result = row.result;
    panel.append(details({ "ID do relatório": result.id, "Arquivos analisados": result.arquivos,
      "Testes executados": result.testes_executados ? "Sim" : "Não", "Estado da IA": result.ia.status }));
    const findings = section("Achados");
    if (!result.achados.length) findings.append(el("p", "Nenhum achado informado."));
    for (const finding of result.achados) {
      const entry = el("div", null, { class: "module4-finding" });
      entry.append(el("h3", finding.titulo), details({ "Arquivo": finding.arquivo, "Linha": finding.linha,
        "Categoria": finding.categoria, "Gravidade": finding.gravidade, "Sugestão": finding.sugestao })); findings.append(entry);
    }
    panel.append(findings, section("Análise com IA"), el("p", result.ia.texto || "Nenhuma análise com IA informada.", { class: "module4-text" }),
      section("Relatório em texto"), el("pre", result.markdown, { class: "module4-text" }));
  }
  return panel;
}
