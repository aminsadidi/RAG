// The web app: searches the knowledge base in Qdrant and gives the sources, never an AI-written answer.
// A question in Persian is translated to English (the papers are in English); the query is embedded with
// the same model and pooling as the Python pipeline, and Qdrant fuses dense and BM25 results with RRF.
import { cleanTranslation, contextPack, expandQuery, isPersian, queryTerms, relevance, shared, sourceLabel, translatePrompt } from "./text.js";
import PAGE from "./page.html";
import LOGIN from "./login.html";
import DISPERSION_JS from "./dispersion.client.js";
import PHASEMATCH_JS from "./phasematch.client.js";
import SPDC_JS from "./spdc.client.js";
// the module imports the phase-matching module by its file name; the browser loads it as /phasematch.js
const SPDC_BROWSER_JS = SPDC_JS.replace('from "./phasematch.client.js"', 'from "/phasematch.js"');
import PAPERS from "./papers.json";

const PAYLOAD = [...shared.PAYLOAD_KEYS, "node_id", "text", "drive_id", "ocr", "pdf_mismatch"];
const MODES = ["hybrid", "vector", "bm25"];

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8" } });
const html = (body, status = 200) =>
  new Response(body, { status, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "x-robots-tag": "noindex, nofollow" } });

async function sha256(text) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

const sessionToken = (env) => sha256(`matrag-session:${env.SITE_PASSWORD}`);

function cookie(request, name) {
  const match = (request.headers.get("cookie") || "").match(new RegExp(`(?:^|;\\s*)${name}=([^;]+)`));
  return match ? match[1] : null;
}

async function signedIn(request, env) {
  return Boolean(env.SITE_PASSWORD) && cookie(request, "session") === (await sessionToken(env));
}

async function qdrant(env, path, body) {
  const response = await fetch(`${env.QDRANT_URL}${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: { "api-key": env.QDRANT_API_KEY, "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(`Qdrant ${response.status}: ${JSON.stringify(data.status || data).slice(0, 300)}`);
  return data.result;
}

// Model outputs are deterministic (temperature 0), so they are kept in KV for 90 days, keyed by
// model + input: a repeated question costs no Workers AI Neurons. A failing cache never fails a search.
async function cached(env, model, input, compute) {
  if (!env.AICACHE) return compute();
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`${model}\n${input}`));
  const key = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const hit = await env.AICACHE.get(key, "json").catch(() => null);
  if (hit !== null) return hit;
  const value = await compute();
  await env.AICACHE.put(key, JSON.stringify(value), { expirationTtl: 90 * 86400 }).catch((e) => console.log("AICACHE put", String(e)));
  return value;
}

async function translate(env, question) {
  return cached(env, env.TRANSLATE_MODEL, question, async () => {
    const out = await env.AI.run(env.TRANSLATE_MODEL, {
      messages: [{ role: "user", content: translatePrompt(question) }], max_tokens: 120, temperature: 0,
    });
    return cleanTranslation(out.response, question);
  });
}

async function embed(env, query) {
  // "cls" pooling: bge's own pooling, identical to the local sentence-transformers vectors.
  return cached(env, env.EMBED_MODEL, query, async () => {
    const out = await env.AI.run(env.EMBED_MODEL, { text: [shared.QUERY_INSTRUCTION + query], pooling: "cls" });
    return out.data[0];
  });
}

function filterOf(opts) {
  const must = [];
  if (opts.material) must.push({ key: "material", match: { value: opts.material } });
  if (opts.category) must.push({ key: "category", match: { value: opts.category } });
  if (opts.fullTextOnly) must.push({ key: "source_type", match: { value: "full_text_pdf" } });
  if (opts.docIds?.length) must.push({ key: "doc_id", match: { any: opts.docIds } });
  return must.length ? { must } : undefined;
}

async function search(env, opts) {
  const question = String(opts.q || "").trim().slice(0, 1000);
  if (!question) throw new Error("empty question");
  const mode = MODES.includes(opts.mode) ? opts.mode : "hybrid";
  const topK = Math.min(Math.max(parseInt(opts.topK, 10) || 8, 1), 30);
  const started = Date.now();
  const searchQuery = isPersian(question) ? await translate(env, question) : null;
  const query = searchQuery || question;
  const filter = filterOf(opts);
  const sparse = { text: expandQuery(query), model: shared.BM25_MODEL };
  // The materials of the question searched on their own as well: in a long question ("the dispersion formula
  // (Sellmeier coefficients) for the refractive index of NaCl") the common words outweigh the one formula,
  // and papers on other crystals win. Fused with the rest by RRF.
  const materials = queryTerms(query).materials;
  const named = materials.length ? [{ query: { text: expandQuery(materials.join(" ")), model: shared.BM25_MODEL },
    using: shared.SPARSE, filter, limit: 50 }] : [];
  let body;
  // The query vector is needed in every mode: its best cosine similarity is one signal of the relevance check.
  const vector = await embed(env, query);
  const bestCosine = mode === "vector" ? null
    : qdrant(env, `/collections/${env.COLLECTION}/points/query`, { query: vector, using: shared.DENSE, filter, limit: 1 })
      .then((r) => r.points[0]?.score ?? 0);
  if (mode === "bm25") {
    body = named.length
      ? { prefetch: [{ query: sparse, using: shared.SPARSE, filter, limit: 50 }, ...named], query: { fusion: "rrf" }, limit: topK }
      : { query: sparse, using: shared.SPARSE, filter, limit: topK };
  } else {
    body = mode === "vector"
      ? { query: vector, using: shared.DENSE, filter, limit: topK }
      : {
        prefetch: [{ query: vector, using: shared.DENSE, filter, limit: 50 },
          { query: sparse, using: shared.SPARSE, filter, limit: 50 }, ...named],
        query: { fusion: "rrf" }, limit: topK,
      };
  }
  // perPaper: the best passage of each paper (Qdrant groups by doc_id), so one paper cannot fill the list.
  const points = opts.perPaper
    ? (await qdrant(env, `/collections/${env.COLLECTION}/points/query/groups`,
      { ...body, group_by: "doc_id", group_size: 1, with_payload: PAYLOAD })).groups.map((g) => g.hits[0])
    : (await qdrant(env, `/collections/${env.COLLECTION}/points/query`, { ...body, with_payload: PAYLOAD })).points;
  const hits = points.map((p, i) => ({ n: i + 1, score: p.score, label: sourceLabel(p.payload), ...p.payload }));
  const check = relevance(query, hits, mode === "vector" ? (points[0]?.score ?? 0) : await bestCosine);
  return { question, searchQuery, mode, topK, perPaper: Boolean(opts.perPaper), hits, relevance: check, ms: Date.now() - started };
}

async function facets(env) {
  const out = {};
  for (const key of ["material", "category"]) {
    const result = await qdrant(env, `/collections/${env.COLLECTION}/facet`, { key, limit: 500, exact: false });
    out[key] = result.hits.map((h) => ({ value: h.value, count: h.count }));
  }
  const info = await qdrant(env, `/collections/${env.COLLECTION}`);
  const types = await qdrant(env, `/collections/${env.COLLECTION}/facet`, { key: "source_type", limit: 10 });
  out.source_type = types.hits.map((h) => ({ value: h.value, count: h.count }));
  out.points = info.points_count;
  return out;
}

// Which of these papers are in the collection: "full" text or "abstract" only.
async function inCollection(env, ids) {
  ids = [...new Set((ids || []).filter((x) => typeof x === "string"))].slice(0, 500);
  if (!ids.length) return {};
  const facet = (extra) => qdrant(env, `/collections/${env.COLLECTION}/facet`, {
    key: "doc_id", limit: ids.length, exact: true,
    filter: { must: [{ key: "doc_id", match: { any: ids } }, ...extra] },
  }).then((r) => r.hits.map((h) => h.value));
  const value = {};
  for (const id of await facet([])) value[id] = "abstract";
  for (const id of await facet([{ key: "source_type", match: { value: "full_text_pdf" } }])) value[id] = "full";
  return value;
}

async function paper(env, docId) {
  const result = await qdrant(env, `/collections/${env.COLLECTION}/points/scroll`, {
    filter: { must: [{ key: "doc_id", match: { value: docId } }] }, limit: 400, with_payload: PAYLOAD,
  });
  const chunks = result.points.map((p) => p.payload)
    .sort((a, b) => (a.first_page ?? 0) - (b.first_page ?? 0) || String(a.node_id).localeCompare(String(b.node_id), "en", { numeric: true }));
  return { doc_id: docId, chunks };
}

function relevanceNote(r) {
  if (!r || r.verdict === "ok") return "ok: the question's materials and words occur in the sources";
  const parts = [];
  if (r.offTopic) parts.push(`the question is far from every passage (best cosine ${r.bestCosine.toFixed(2)})`);
  if (r.missingMaterials.length) parts.push(`not in any source: ${r.missingMaterials.join(", ")}`);
  if (r.missingWords.length) parts.push(`words in no source: ${r.missingWords.join(", ")}`);
  return `${r.verdict === "none" ? "NO RELEVANT SOURCE FOUND" : "partial"}: ${parts.join("; ")}`;
}

function packFile(found) {
  const language = found.searchQuery ? "Persian" : null;
  const about = {
    question: found.question,
    ...(found.searchQuery ? { "search query (English)": found.searchQuery } : {}),
    corpus: "rag-optics",
    retrieval: `${found.mode}${found.mode === "hybrid" ? " (dense + BM25, RRF in Qdrant)" : ""}, top ${found.topK}${found.perPaper ? ", one passage per paper" : ""}`,
    "embedding model": shared.EMBED_MODEL,
    "relevance check": relevanceNote(found.relevance),
    created: new Date().toISOString().slice(0, 16).replace("T", " ") + " UTC",
  };
  return contextPack(found.question, found.hits, about, language, found.searchQuery);
}

async function handle(request, env) {
  const url = new URL(request.url);
  // The password in a form or in the link (/?key=...): the browser is then remembered for a year.
  const given = url.searchParams.get("key") ??
    (url.pathname === "/login" && request.method === "POST" ? (await request.formData()).get("password") : null);
  if (given !== null) {
    if (env.SITE_PASSWORD && given === env.SITE_PASSWORD) {
      const token = await sessionToken(env);
      return new Response(null, { status: 303, headers: {
        location: "/", "set-cookie": `session=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=31536000` } });
    }
    await new Promise((r) => setTimeout(r, 800));
    return html(LOGIN.replace("<!--error-->", '<p class="err">رمز درست نیست.</p>'), 401);
  }
  if (url.pathname === "/logout") {
    return new Response(null, { status: 303, headers: { location: "/", "set-cookie": "session=; Path=/; Max-Age=0" } });
  }
  if (!(await signedIn(request, env))) {
    return url.pathname.startsWith("/api/") ? json({ error: "login required" }, 401) : html(LOGIN);
  }
  if (url.pathname === "/") return html(PAGE);
  if (url.pathname === "/phasematch.js") {
    return new Response(PHASEMATCH_JS, { headers: { "content-type": "text/javascript; charset=utf-8", "cache-control": "no-cache" } });
  }
  if (url.pathname === "/spdc.js") {
    return new Response(SPDC_BROWSER_JS, { headers: { "content-type": "text/javascript; charset=utf-8", "cache-control": "no-cache" } });
  }
  if (url.pathname === "/dispersion.js") {
    return new Response(DISPERSION_JS, { headers: { "content-type": "text/javascript; charset=utf-8", "cache-control": "no-cache" } });
  }
  if (url.pathname.startsWith("/pdf/") && env.PDFS) {
    const path = url.pathname.slice("/pdf".length);
    const response = await env.PDFS.fetch(new Request(`https://pdfs${path}`));
    if (!response.ok || !(response.headers.get("content-type") || "").includes("pdf")) return json({ error: "no pdf" }, 404);
    return new Response(response.body, { headers: {
      "content-type": "application/pdf", "cache-control": "private, max-age=86400", "x-robots-tag": "noindex" } });
  }
  try {
    if (url.pathname === "/api/search" && request.method === "POST") return json(await search(env, await request.json()));
    if (url.pathname === "/api/pack" && request.method === "POST") {
      const found = await search(env, await request.json());
      return new Response(packFile(found), { headers: {
        "content-type": "text/markdown; charset=utf-8",
        "content-disposition": `attachment; filename="matrag-sources-${Date.now()}.md"` } });
    }
    if (url.pathname === "/api/facets") return json(await facets(env));
    if (url.pathname === "/api/papers") return json(PAPERS);
    if (url.pathname === "/api/incollection" && request.method === "POST") {
      return json(await inCollection(env, (await request.json()).ids));
    }
    if (url.pathname === "/api/paper") return json(await paper(env, url.searchParams.get("doc_id") || ""));
  } catch (error) {
    return json({ error: String(error.message || error) }, 500);
  }
  return json({ error: "not found" }, 404);
}

export default {
  fetch: handle,
  async scheduled(event, env, ctx) {
    ctx.waitUntil(qdrant(env, `/collections/${env.COLLECTION}`).then((info) => console.log("qdrant ok", info.points_count)));
  },
};
