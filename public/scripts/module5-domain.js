const QUESTION_LIMIT = 2000;
const ARTICLE_LIMIT = 50;
const unicodeSurrogate = /\p{Cs}/u;

export function curationDraft(question) {
  const pergunta = typeof question === "string" ? question.trim() : "";
  if (!pergunta || Array.from(pergunta).length > QUESTION_LIMIT || unicodeSurrogate.test(pergunta)) {
    throw new TypeError("Digite uma pergunta de 1 a 2.000 caracteres.");
  }
  return { pergunta };
}

export function trainingQuestion(proposal) {
  if (proposal.kind !== "training" || !Array.isArray(proposal.suggestions)) return "";
  const topics = new Set();
  for (const suggestion of proposal.suggestions) {
    if (!Array.isArray(suggestion?.topics)) continue;
    for (const topic of suggestion.topics) {
      if (typeof topic === "string" && topic.trim() && !unicodeSurrogate.test(topic)) topics.add(topic.trim());
    }
  }
  if (!topics.size) return "";
  const prefix = "Quais materiais de estudo abordam ";
  const list = new Intl.ListFormat("pt-BR").format(topics);
  const bounded = Array.from(list).slice(0, QUESTION_LIMIT - prefix.length - 1).join("").trimEnd();
  return prefix + bounded + "?";
}

export function safeArticleLink(value) {
  if (typeof value !== "string" || !/^https?:\/\/[^/?#]+/iu.test(value)
      || /[\s\\\p{Cc}\p{Cf}\p{Cs}]/u.test(value)) return "";
  const authority = value.split("/")[2].split(/[?#]/u)[0];
  if (/[@%]/u.test(authority)) return "";
  try {
    const url = new URL(value);
    return url.hostname && url.port !== "0" ? url.href : "";
  } catch {
    return "";
  }
}

const boundedText = (value, limit, minimum = 0) => {
  if (typeof value !== "string" || unicodeSurrogate.test(value)) return false;
  const length = Array.from(value).length;
  return length >= minimum && length <= limit;
};
const optionalText = (value, limit, minimum) => value === null || boundedText(value, limit, minimum);
const sourceList = value => Array.isArray(value) && value.length <= ARTICLE_LIMIT
  && value.every(source => boundedText(source, 200, 1));
const article = value => value && boundedText(value.titulo, 500, 1)
  && boundedText(value.link, 2048, 1) && optionalText(value.fonte, 200, 1)
  && optionalText(value.idioma, 32) && optionalText(value.data_publicacao, 100);

export function isCurationResult(value) {
  return Boolean(value && typeof value.enabled === "boolean" && typeof value.truncated === "boolean"
    && Array.isArray(value.artigos) && value.artigos.length <= ARTICLE_LIMIT && value.artigos.every(article)
    && Number.isSafeInteger(value.total) && value.total >= value.artigos.length
    && boundedText(value.categoria, 80, 1)
    && sourceList(value.fontes_consultadas) && sourceList(value.fontes_indisponiveis));
}
