// Query-side text handling; the same rules as src/matrag/qdrant_store.py and qa.py
// (the constants come from shared.json, generated from the Python code).
import S from "./shared.json";

const SPACED_FORMULA = new RegExp(S.SPACED_FORMULA, "g");
const PERSIAN = /[؀-ۿ]/;

export const isPersian = (text) => PERSIAN.test(text || "");

// 'LiB 3 O 5' -> 'LiB3O5'; runs with fewer than two capitals ('Eq 5') are kept.
export function normalizeFormulas(text) {
  return text.replace(SPACED_FORMULA, (s) => ((s.match(/[A-Z]/g) || []).length >= 2 ? s.replace(/\s+/g, "") : s));
}

const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export function expandQuery(query) {
  query = normalizeFormulas(query);
  const extra = Object.entries(S.SYNONYMS)
    .filter(([name, formula]) => new RegExp(`\\b${escape(name)}\\b`).test(query) && !query.includes(formula))
    .map(([, formula]) => formula);
  return [query, ...extra].join(" ");
}

export function translatePrompt(question) {
  const glossary = Object.entries(S.PERSIAN_GLOSSARY).map(([fa, en]) => `  ${fa} = ${en}`).join("\n");
  return S.TRANSLATE_PROMPT.replace("{glossary}", glossary).replace("{question}", question);
}

// First line of the model's reply, as translate_query() does.
export function cleanTranslation(text, question) {
  const line = (text || "").trim().split("\n")[0].trim().replace(/^"+|"+$/g, "");
  return line || question;
}

export function sourceLabel(p) {
  const citation = p.citation || p.doc_id || "?";
  if (p.source_type === "abstract") return `${citation}, abstract only`;
  if (p.source_type === "metadata_only") return `${citation}, title only`;
  let label = `${citation}, p. ${p.pages || "?"}`;
  if (p.content_type === "table") label += ", table";
  return label;
}

const questionText = (question, searchQuery) =>
  searchQuery && searchQuery !== question ? `${question}\n(English translation: ${searchQuery})` : question;

const languageRules = (language) =>
  language ? [`Write the answer in ${language}; keep symbols, units and numbers as in the sources.`] : [];

// Same file as build_context_pack() in qa.py.
export function contextPack(question, payloads, about, language, searchQuery) {
  const rules = ["Write citations as plain text with the page, e.g. (Source 2, p. 5), not as links or footnotes.",
    ...languageRules(language)];
  const context = payloads.map((p, i) => `[${i + 1}] (${sourceLabel(p)})\n${p.text}`).join("\n\n");
  const prompt = S.RAG_PROMPT.replace("{not_found}", S.NOT_FOUND)
    .replace("{extra_rules}", rules.map((r) => `- ${r}\n`).join(""))
    .replace("{context}", context)
    .replace("{question}", questionText(question, searchQuery));
  const aboutLines = Object.entries(about).map(([k, v]) => `- ${k}: ${v}`).join("\n");
  const refs = [...new Set(payloads.map((p) => p.reference || p.doc_id || "?"))].map((r) => `- ${r}`).join("\n");
  return `${prompt}\n\n---\nAbout this file (for the reader; not part of the sources):\n${aboutLines}` +
    `\n\nPapers the sources come from:\n${refs}\n`;
}

export { S as shared };
