// Query-side text handling; the same rules as src/matrag/qdrant_store.py and qa.py
// (the constants come from shared.json, generated from the Python code).
import S from "./shared.json";

const SPACED_FORMULA = new RegExp(S.SPACED_FORMULA, "g");
const PERSIAN = /[؀-ۿ]/;

export const isPersian = (text) => PERSIAN.test(text || "");

// Subscript (LiNbO₃), Persian (LiNbO۳), Arabic-Indic and full-width digits as ASCII digits, so a formula
// typed or pasted with them is still a formula.
const DIGIT_BLOCKS = [0x2080, 0x06f0, 0x0660, 0xff10];
export const foldDigits = (text) => text.replace(/[\u2080-\u2089\u06f0-\u06f9\u0660-\u0669\uff10-\uff19]/g, (c) => {
  const code = c.charCodeAt(0);
  return String(code - DIGIT_BLOCKS.find((b) => code >= b && code <= b + 9));
});

// 'LiB 3 O 5' -> 'LiB3O5'; runs with fewer than two capitals ('Eq 5') are kept.
export function normalizeFormulas(text) {
  return foldDigits(text).replace(SPACED_FORMULA, (s) => ((s.match(/[A-Z]/g) || []).length >= 2 ? s.replace(/\s+/g, "") : s));
}

const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
// A prompt's {name} fields filled in one pass, as Python's str.format: a value is put in as it is (String.replace
// with a string reads $$, $& and $' in it, and paper text in LaTeX has them), and a value holding "{question}"
// or the like is not filled again.
const fill = (template, values) => template.replace(/\{([a-z_]+)\}/g, (m, k) => (Object.hasOwn(values, k) ? String(values[k]) : m));

// Every name of every crystal (src/matrag/crystal_names.py), the longest first, with the same rules as the Python
// find_crystals: a formula (GaP, BiBO) only in its own case, so "gap" or "gas" in a sentence is no crystal; other
// names of three letters or more in any case ("bbo", "lithium niobate"); one-letter names (C) never.
const FORMULA_LIKE = /^(?:[A-Z][a-z]?|\d+(?:\.\d+)?|[()·:\-x])+$/;
const formulaLike = (n) => FORMULA_LIKE.test(n) && /[\da-z]/.test(n) && (n.match(/[A-Z][a-z]?/g) || []).every((e) => ELEMENTS.has(e));
let ALIASES_;
const aliases = () => (ALIASES_ ||= [...new Map(Object.entries(S.CRYSTAL_NAMES).flatMap(([f, names]) => [f, ...names].map((n) => [n, f]))).entries()]
  .filter(([n]) => n.length >= 2).sort((a, b) => b[0].length - a[0].length)
  .map(([n, f]) => [n, f, new RegExp(`(?<![A-Za-z0-9])${escape(n)}(?![A-Za-z0-9])`, n.length >= 3 && !formulaLike(n) ? "gi" : "g")]));
export const CRYSTAL_NAMES = S.CRYSTAL_NAMES;
// The crystals a text names (formulas, in order) and the text with those names blanked out.
export function findCrystals(text) {
  const found = [];
  text = String(text || "");
  // names in their own case first (HgS is cinnabar, not HGS = HgGa2S4 read in any case), then in any case
  for (const pass of [false, true]) for (const [n, f, re] of aliases()) {
    const cs = pass ? re : new RegExp(re.source, "g");
    cs.lastIndex = 0;
    if (cs.test(text)) { cs.lastIndex = 0; text = text.replace(cs, " , "); if (!found.includes(f)) found.push(f); }
  }
  return { found, text };
}
// Whether a text mentions a crystal under any of its names.
const mentions = (text, formula) => aliases().some(([, f, re]) => f === formula && (re.lastIndex = 0, re.test(text)));

export function expandQuery(query) {
  query = normalizeFormulas(query);
  const extra = [];
  // every crystal named, as its formula ("beta barium borate" -> + BaB2O4). Adding the abbreviation too (LiNbO3 -> + LN)
  // lowered the MRR@10 on 200 gold questions (0.421 -> 0.414: LN, RTA, YLF are also other words), so it is not done.
  for (const f of findCrystals(query).found) if (!query.includes(f) && !extra.includes(f)) extra.push(f);
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

// Materials (formulas such as LiB3O5, abbreviations such as BBO, common names) and content words of a query.
export function queryTerms(query) {
  const { found: named, text } = findCrystals(normalizeFormulas(query || ""));
  const formulas = (text.match(FORMULA) || []).filter(hasFormulaShape);
  const isWord = (w) => w.length >= 3 && !STOP.has(w) && !/^\d+$/.test(w);
  // A word named like an element or compound ("unobtainium", "zirconate") is a material too.
  const chemical = (w) => /(?:ium|ide|ate|ite)$/.test(w) && w.length >= 6 && !CHEM_WORDS.has(w);
  const tokens = text.replace(FORMULA, (w) => (hasFormulaShape(w) ? " , " : w)).toLowerCase()
    .split(/[^a-z0-9\u0370-\u03ff,-]+|(?=,)|(?<=,)/).flatMap((w) => (w.includes("-") ? w.split("-") : [w]));
  const all = [...new Set(tokens.filter(isWord))];
  const words = all.filter((w) => !chemical(w));
  // Two content words in a row ("black holes", "water vapor") must occur together, not in different passages.
  const phrases = [];
  for (let i = 1; i < tokens.length; i++) if (isWord(tokens[i - 1]) && isWord(tokens[i])) phrases.push(`${tokens[i - 1]} ${tokens[i]}`);
  return { materials: [...new Set([...named, ...formulas, ...all.filter(chemical)])], words, phrases: [...new Set(phrases)] };
}
// The crystals a query names, as formulas (BBO -> BaB2O4, "lithium niobate" -> LiNbO3), for the crystal cards of the
// search page; words that only look chemical ("zirconate") are left out.
// Abbreviations are also read in lower case ("bbo", "ktp"), except the two-letter ones ("ln", "lt" are words).
export function crystalsIn(query) {
  return queryTerms(query).materials.filter((m) => /[A-Z]/.test(m));
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
  const missingMaterials = materials.filter((m) => (/[A-Z]/.test(m) ? !hay.includes(m) : !has(m)) && !mentions(hay, m));
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

// The scope check (Workers AI, the translation model): is the question one the papers can answer, only a textbook
// definition or a whole topic ("what is a laser", "crystals"), or not about optics at all? On the test set
// (data/rag-optics/gold/scope.csv: 50 off-topic, 50 general) and 200 gold questions: 50/50, 50/50 and 198/200
// specific (the two others, on resins and electrolytes, are saved by the cosine condition in search()).
export const SCOPE_PROMPT = `You sort questions sent to a search engine over research papers and handbooks on optical crystals: nonlinear and laser crystals, refractive index and Sellmeier equations, nonlinear coefficients, phase matching, frequency conversion (SHG, OPO, SPDC), thermal, damage and transparency properties of optical materials.
Answer with one word:
SPECIFIC - a question the papers can answer: it names a crystal or material, a property, a value, a wavelength, a process with details, a method, a measurement or a comparison (even short, e.g. "BBO d22", "LBO thermal expansion").
GENERAL - inside optics but only asks for a textbook definition or a whole broad topic, with nothing specific to look up (e.g. "what is a laser", "explain nonlinear optics", "crystals").
OFFTOPIC - not about optics or optical materials.
The question may be in Persian or English.`;
// The model's answer as "specific", "general" or "offtopic"; anything else is read as specific (never reject by doubt).
export function scopeWord(answer) {
  const w = String(answer || "").trim().split(/\s+/)[0]?.replace(/[^A-Za-z]/g, "").toUpperCase();
  return w === "GENERAL" ? "general" : w === "OFFTOPIC" ? "offtopic" : "specific";
}
// An off-topic answer of the model rejects the question only while no passage is this close (cosine): the two gold
// questions it calls off-topic have their paper near.
export const SCOPE_MAX_COSINE = 0.72;

export function translatePrompt(question) {
  const glossary = Object.entries(S.PERSIAN_GLOSSARY).map(([fa, en]) => `  ${fa} = ${en}`).join("\n");
  return fill(S.TRANSLATE_PROMPT, { glossary, question });
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
  const rules = ["Write citations as plain text, not as links or footnotes.",
    "Say whether each value you give was measured or calculated, as the source shows (each source is labelled with the kind of work it is).",
    ...languageRules(language)];
  const kind = { experimental: "experimental work", theoretical: "theoretical/computational work", both: "experimental and theoretical work", review: "review or compilation" };
  const passage = { experimental: "this passage: measured", theoretical: "this passage: calculated", both: "this passage: measured and calculated", review: "this passage: cites other work" };
  const context = payloads.map((p, i) => `[${i + 1}] (${sourceLabel(p)}${kind[p.basis] ? `; ${kind[p.basis]}` : ""}${passage[p.basis_p] ? `; ${passage[p.basis_p]}` : ""})\n${p.text}`).join("\n\n");
  const prompt = fill(S.RAG_PROMPT, { not_found: S.NOT_FOUND, extra_rules: rules.map((r) => `- ${r}\n`).join(""),
    context, question: questionText(question, searchQuery) });
  const aboutLines = Object.entries(about).map(([k, v]) => `- ${k}: ${v}`).join("\n");
  const refs = [...new Set(payloads.map((p) => p.reference || p.doc_id || "?"))].map((r) => `- ${r}`).join("\n");
  return `${prompt}\n\n---\nAbout this file (for the reader; not part of the sources):\n${aboutLines}` +
    `\n\nPapers the sources come from:\n${refs}\n`;
}

export { S as shared };
