import { el, form, textDate } from "./workspace-view.js";
import { safeArticleLink } from "./module5-domain.js";

export function curationForm(question, onSubmit) {
  const editor = form("curation", [{
    name: "pergunta", label: "Pergunta sobre tecnologia", type: "textarea",
    value: question, required: true, wide: true,
    hint: "Use até 2.000 caracteres. Ao buscar, sua pergunta será enviada ao Módulo 5.",
  }], "Buscar artigos", ({ pergunta }) => onSubmit(pergunta));
  editor.node.classList.add("curation-form");
  const input = editor.inputs.pergunta;
  const submit = editor.node.querySelector("button[type=submit]");
  return {
    node: editor.node,
    focus: () => input.focus(),
    searching(value) {
      input.readOnly = value;
      if (value) submit.setAttribute("aria-disabled", "true");
      else submit.removeAttribute("aria-disabled");
    },
  };
}

function articleRow(article) {
  const link = safeArticleLink(article.link);
  const title = link
    ? el("a", article.titulo, { href: link, target: "_blank", rel: "noopener noreferrer" })
    : el("span", article.titulo);
  const row = el("li", null);
  row.append(title);
  const date = article.data_publicacao && textDate(article.data_publicacao);
  const metadata = [article.fonte, date].filter(Boolean).join(" · ");
  if (metadata) row.append(el("p", metadata, { class: "field-hint" }));
  return row;
}

export function curationResults(title, empty) {
  const node = el("section", null, { class: "curation-results", hidden: true });
  const feedback = el("p", "", { class: "field-hint", role: "status" });
  const sources = el("p", "", { class: "field-hint", hidden: true });
  const list = el("ul", null, { class: "curation-articles", role: "list", hidden: true });
  node.append(el("h3", title), feedback, sources, list);

  function message(text) {
    node.hidden = false;
    feedback.textContent = text;
    sources.hidden = list.hidden = true;
    sources.textContent = "";
    list.replaceChildren();
  }

  function show(result) {
    const count = result.artigos.length;
    const summary = count === 1 ? "1 artigo disponível." : count ? count + " artigos disponíveis." : empty;
    message(result.truncated ? "Exibindo " + count + " de " + result.total + " artigos." : summary);
    if (result.fontes_indisponiveis.length) {
      sources.textContent = "Fontes indisponíveis · " + result.fontes_indisponiveis.join(", ");
      sources.hidden = false;
    }
    list.append(...result.artigos.map(articleRow));
    list.hidden = !count;
  }

  return { node, message, show };
}
