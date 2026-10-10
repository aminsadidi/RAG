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

// ---------- relevance check: does anything in the hits answer the question?
// Search always returns the nearest passages, even for a question the collection cannot answer. Two signals
// decide whether to say "not found": the question's materials and content words must occur in the hits, and
// the best cosine similarity must not be that of an off-topic question (0.45–0.6 for bge on this corpus,
// against 0.7–0.9 for optics questions).
export const MIN_COSINE = 0.63;
const STOP = new Set(("a an the of for in on at to by with from and or as is are was were be been it its this that these those " +
  "what which who whom how why when where whose do does did can could should would will shall may might " +
  "me my we our you your i give find show tell list get want need please about between into than then there " +
  "any some all each other more most less very also only not no yes using use used per vs versus via " +
  "alpha beta gamma delta crystal crystals material materials value values paper papers" ).split(" "));
const FORMULA = /\b(?:[A-Z][a-z]?\d*(?:\.\d+)?){2,}\b/g;
const ELEMENTS = new Set(("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr " +
  "Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re " +
  "Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu").split(" "));
// A chemical formula: element symbols only, and a digit (LiB3O5) or a lowercase letter (GaAs); "SHG", "UV", "OPO" are not.
const hasFormulaShape = (w) => (w.match(/[A-Z][a-z]?/g) || []).every((e) => ELEMENTS.has(e)) && /[\da-z]/.test(w);
const stem = (w) => w.replace(/(?:ies|es|s)$/, (m) => (w.length > 4 ? (m === "ies" ? "y" : "") : m));

// Common names of crystals, read as their formula (the translation of «بتا باریم بورات» is "beta barium borate").
const NAMES = { "barium borate": "BaB2O4", "lithium triborate": "LiB3O5", "lithium borate": "LiB3O5", "bismuth triborate": "BiB3O6",
  "bismuth borate": "BiB3O6", "lithium niobate": "LiNbO3", "lithium tantalate": "LiTaO3", "potassium titanyl phosphate": "KTiOPO4",
  "potassium titanyl arsenate": "KTiOAsO4", "rubidium titanyl phosphate": "RbTiOPO4", "potassium dihydrogen phosphate": "KH2PO4",
  "ammonium dihydrogen phosphate": "NH4H2PO4", "zinc germanium phosphide": "ZnGeP2", "silver gallium sulfide": "AgGaS2",
  "silver gallium selenide": "AgGaSe2", "yttrium aluminum garnet": "Y3Al5O12", "yttrium aluminium garnet": "Y3Al5O12",
  "yttrium vanadate": "YVO4", "cesium lithium borate": "CsLiB6O10", "cesium triborate": "CsB3O5", "calcium fluoride": "CaF2",
  "magnesium fluoride": "MgF2", "barium fluoride": "BaF2", "lithium fluoride": "LiF", "zinc selenide": "ZnSe", "zinc sulfide": "ZnS",
  "gallium arsenide": "GaAs", "gallium nitride": "GaN", "gallium phosphide": "GaP", "fused silica": "SiO2", "sapphire": "Al2O3" };

// Materials (formulas such as LiB3O5, abbreviations such as BBO, common names) and content words of a query.
export function queryTerms(query) {
  let text = normalizeFormulas(query || "");
  const named = [];
  for (const [name, formula] of Object.entries(NAMES)) {
    const re = new RegExp(`\\b${name}\\b`, "i");
    if (re.test(text)) { named.push(formula); text = text.replace(re, " "); }
  }
  const formulas = (text.match(FORMULA) || []).filter(hasFormulaShape);
  const abbrs = Object.keys(S.SYNONYMS).filter((n) => new RegExp(`\\b${escape(n)}\\b`).test(text));
  const isWord = (w) => w.length >= 3 && !STOP.has(w) && !/^\d+$/.test(w) && !abbrs.some((n) => n.toLowerCase() === w);
  // A word named like an element or compound ("unobtainium", "zirconate") is a material too.
  const chemical = (w) => /(?:ium|ide|ate|ite)$/.test(w) && w.length >= 6 && !CHEM_WORDS.has(w);
  const tokens = text.replace(FORMULA, (w) => (hasFormulaShape(w) ? " , " : w)).toLowerCase()
    .split(/[^a-z0-9\u0370-\u03ff,-]+|(?=,)|(?<=,)/).flatMap((w) => (w.includes("-") ? w.split("-") : [w]));
  const all = [...new Set(tokens.filter(isWord))];
  const words = all.filter((w) => !chemical(w));
  // Two content words in a row ("black holes", "water vapor") must occur together, not in different passages.
  const phrases = [];
  for (let i = 1; i < tokens.length; i++) if (isWord(tokens[i - 1]) && isWord(tokens[i])) phrases.push(`${tokens[i - 1]} ${tokens[i]}`);
  return { materials: [...new Set([...formulas, ...abbrs, ...named, ...all.filter(chemical)])], words, phrases: [...new Set(phrases)] };
}
// The crystals a query names, as formulas (BBO -> BaB2O4, "lithium niobate" -> LiNbO3), for the crystal cards of the
// search page; words that only look chemical ("zirconate") are left out.
export function crystalsIn(query) {
  return [...new Set(queryTerms(query).materials.map((m) => S.SYNONYMS[m] || m).filter((m) => /[A-Z]/.test(m)))];
}
const CHEM_WORDS = new Set(["estimate", "accurate", "separate", "moderate", "appropriate", "approximate", "intermediate",
  "substrate", "aggregate", "elaborate", "calculate", "evaluate", "indicate", "investigate", "demonstrate", "integrate",
  "generate", "illustrate", "compensate", "elevated", "provide", "decide", "guide", "outside", "inside", "wide", "medium"]);

// verdict: "ok", "weak" (some words of the question are in no hit) or "none" (nothing relevant).
export function relevance(query, hits, bestCosine) {
  const { materials, words, phrases } = queryTerms(query);
  const hay = normalizeFormulas(hits.map((h) => [h.text, h.citation, h.reference, h.material, h.headings].join(" ")).join("\n"));
  const low = hay.toLowerCase().replace(/\s+/g, " ");
  const has = (term) => new RegExp(`(?:^|[^a-z0-9])${escape(stem(term)).replace(/ /g, "[\\s-]+")}`).test(low);
  // two words of a phrase within three words of each other, in either order
  const near = (a, b) => [[a, b], [b, a]].some(([x, y]) =>
    new RegExp(`(?:^|[^a-z0-9])${escape(stem(x))}[a-z0-9]*(?:[^a-z0-9]+[a-z0-9]+){0,3}?[^a-z0-9]+${escape(stem(y))}`).test(low));
  const missingMaterials = materials.filter((m) => (/[A-Z]/.test(m) ? !hay.includes(m) : !has(m))
    && !(S.SYNONYMS[m] && hay.includes(S.SYNONYMS[m]))
    && !Object.entries(S.SYNONYMS).some(([n, f]) => f === m && new RegExp(`\\b${escape(n)}\\b`).test(hay)));
  const missingWords = [...words.filter((w) => !has(w)),
    ...phrases.filter((p) => p.split(" ").every((w) => has(w)) && !near(...p.split(" ")))];
  const offTopic = typeof bestCosine === "number" && bestCosine < MIN_COSINE;
  const missingSingle = missingWords.filter((w) => !w.includes(" ")).length;
  const missingPhrases = missingWords.length - missingSingle;
  const verdict = !hits.length || offTopic || missingMaterials.length || (words.length >= 2 && missingSingle > words.length / 2)
    || (phrases.length >= 2 && missingPhrases > phrases.length / 2)
    ? "none" : missingWords.length ? "weak" : "ok";
  return { verdict, missingMaterials, missingWords, bestCosine: bestCosine ?? null, offTopic };
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
