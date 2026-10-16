// The web app: searches the knowledge base in Qdrant and gives the sources, never an AI-written answer.
// A question in Persian is translated to English (the papers are in English); the query is embedded with
// the same model and pooling as the Python pipeline, and Qdrant fuses dense and BM25 results with RRF.
import { cleanTranslation, contextPack, crystalsIn, expandQuery, foldDigits, isPersian, queryTerms, relevance, shared, sourceLabel, translatePrompt } from "./text.js";
import PAGE from "./page.html";
import LOGIN from "./login.html";
import DISPERSION_JS from "./dispersion.client.js";
import PHASEMATCH_JS from "./phasematch.client.js";
import SPDC_JS from "./spdc.client.js";
// the module imports the phase-matching module by its file name; the browser loads it as /phasematch.js
const SPDC_BROWSER_JS = SPDC_JS.replace('from "./phasematch.client.js"', 'from "/phasematch.js"');
import PAPERS from "./papers.json";
import { verifyOidc } from "./oidc.js";
import { dailySummary, feedback, logEvent, unanswered } from "./feedback.js";
import { OWNER, checkLogin, getSettings, makeSession, sessionUser, takeQuota } from "./accounts.js";
import { telegramWebhook } from "./admin.js";

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

// The signed-in account ({name, role, tabs, search, pdf, quota}; OWNER for the shared password, also in its
// old cookie form), or null.
async function signedIn(request, env) {
  if (!env.SITE_PASSWORD) return null;
  const token = cookie(request, "session");
  if (token && token === (await sessionToken(env))) return OWNER;
  return sessionUser(env, token);
}

const MAINTENANCE = `<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>MatRAG</title>
<body style="font-family:Tahoma,sans-serif;display:grid;place-items:center;min-height:90vh;text-align:center;color:#334">
<div><h2>سایت موقتاً در دست تعمیر است</h2><p>کمی بعد دوباره سر بزنید.</p><p dir="ltr">MatRAG is down for maintenance; please come back a little later.</p><p><a href="/logout">خروج / Log out</a></p></div></body></html>`;

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
// model + the full model input (prompt included, so an edited prompt is not served old answers): a repeated
// question costs no Workers AI Neurons. A failing cache never fails a search.
async function cached(env, model, input, compute) {
  if (!env.AICACHE) return compute();
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`${model}\n${input}`));
  const key = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const hit = await env.AICACHE.get(key, "json").catch(() => null);
  if (hit !== null) return hit;
  const value = await compute();
  if (value === null || value === undefined) return value; // nothing worth keeping (and "null" would read as a miss)
  await env.AICACHE.put(key, JSON.stringify(value), { expirationTtl: 90 * 86400 }).catch((e) => console.log("AICACHE put", String(e)));
  return value;
}

async function translate(env, question) {
  const prompt = translatePrompt(question);
  return cached(env, env.TRANSLATE_MODEL, prompt, async () => {
    const out = await env.AI.run(env.TRANSLATE_MODEL, {
      messages: [{ role: "user", content: prompt }], max_tokens: 120, temperature: 0,
    });
    return cleanTranslation(out.response, question);
  });
}

async function embed(env, query) {
  // "cls" pooling: bge's own pooling, identical to the local sentence-transformers vectors.
  const text = shared.QUERY_INSTRUCTION + query;
  return cached(env, env.EMBED_MODEL, `cls\n${text}`, async () => {
    const out = await env.AI.run(env.EMBED_MODEL, { text: [text], pooling: "cls" });
    return out.data[0];
  });
}

// Reranking: a cross-encoder reads the question and each candidate passage together, which ranks better
// than the separate vectors of the first stage. The passage is cut to about the model's 512 tokens.
const RERANK_POOL = 30;
const RERANK_CHARS = 1800;

async function rerankPoints(env, query, points, topK) {
  if (points.length < 2) return points;
  const ids = points.map((p) => p.id).join(",");
  const scores = await cached(env, env.RERANK_MODEL, `${query}\n${ids}`, async () => {
    const out = await env.AI.run(env.RERANK_MODEL, {
      query, contexts: points.map((p) => ({ text: String(p.payload.text || "").slice(0, RERANK_CHARS) })),
    });
    const s = new Array(points.length).fill(-1);
    for (const r of out.response) s[r.id] = r.score;
    return s;
  });
  return points.map((p, i) => ({ ...p, score: scores[i] ?? -1 }))
    .sort((a, b) => b.score - a.score).slice(0, topK);
}

// SubQ (subq-snap-preview): the probability that each passage of the top-30 pool answers the question; the
// pool is ordered by it. On the 200 gold questions it raised the MRR@10 from 0.511 to 0.609
// (scripts/quality/reports). SUBQ_KEYS holds several keys: one that is spent or refused passes to the next.
// One KV entry per question and pool (the free KV plan allows 1000 writes a day). Any failure keeps the
// site's own order.
async function subqScore(env, q, text) {
  let subqAt = 0;
  const keys = String(env.SUBQ_KEYS || "").split(",").map((k) => k.trim()).filter(Boolean);
  const body = JSON.stringify({ model: "subq-snap-preview", state: `Search question: ${q}\n\nPassage: ${text}`,
    questions: { rel: { type: "noul", instructions: "Does the passage come from a paper that answers the search question (same material and same quantity)?",
      criteria: { true: "The passage gives or directly concerns the requested data for this material", false: "Another material, another quantity, or unrelated" } } } });
  while (subqAt < keys.length) {
    const r = await fetch("https://api.subq.ai/v1/systemone", { method: "POST", body,
      headers: { "content-type": "application/json", authorization: `Bearer ${keys[subqAt]}` } });
    if (r.status === 401 || r.status === 402) { subqAt++; continue; } // this key is spent or refused: the next one
    if (!r.ok) throw new Error(`SubQ ${r.status} ${(await r.text()).slice(0, 200)}`);
    return (await r.json()).answers.rel.noul;
  }
  throw new Error("no SubQ key left");
}
async function subqRerank(env, query, points, topK) {
  if (points.length < 2) return points;
  const scores = await cached(env, "subq-snap-preview", `${query}\n${points.map((p) => p.id).join(",")}`, () =>
    Promise.all(points.map((p) => subqScore(env, query, `${p.payload.citation || ""} — ${String(p.payload.text || "").slice(0, 1200)}`))));
  return points.map((p, i) => ({ ...p, score: scores[i] })).sort((a, b) => b.score - a.score).slice(0, topK);
}
const within = (ms, promise) => Promise.race([promise, new Promise((_, no) => setTimeout(() => no(new Error("timeout")), ms))]);

function filterOf(opts) {
  const must = [];
  if (opts.material) must.push({ key: "material", match: { value: opts.material } });
  if (opts.category) must.push({ key: "category", match: { value: opts.category } });
  if (opts.fullTextOnly) must.push({ key: "source_type", match: { value: "full_text_pdf" } });
  if (opts.docIds?.length) must.push({ key: "doc_id", match: { any: opts.docIds } });
  // The `junk` field (scripts/quality/enrich.py) is not used as a filter: leaving junk > 0.9 out lowered the
  // MRR@10 of the 200 gold questions from 0.511 to 0.485 (scripts/quality/reports), as cover pages, with the
  // title and the crystal's name, were among the "junk" and are what finds some papers.
  return must.length ? { must } : undefined;
}

async function search(env, opts) {
  const question = foldDigits(String(opts.q || "")).trim().slice(0, 1000);
  if (!question) throw Object.assign(new Error("empty question"), { status: 400 });
  let mode = MODES.includes(opts.mode) ? opts.mode : "hybrid";
  const topK = Math.min(Math.max(parseInt(opts.topK, 10) || 8, 1), 30);
  // Off by default: on 200 gold questions it lowered MRR@10 (0.439 -> 0.401), see docs/reranker_eval.md.
  // SubQ reranking is on unless the request says rerank: false; the bge reranker only when asked and without SubQ.
  const subq = Boolean(env.SUBQ_KEYS) && opts.rerank !== false;
  const rerank = subq || (opts.rerank === true && Boolean(env.RERANK_MODEL));
  // With the reranker, Qdrant returns a wider candidate list and the cross-encoder picks the topK of it.
  const limit = rerank ? Math.max(topK, RERANK_POOL) : topK;
  const started = Date.now();
  // Workers AI out of quota or down: the search goes on with less (the original question; keywords only)
  // and says so, rather than failing.
  const degraded = [];
  const searchQuery = isPersian(question)
    ? await translate(env, question).catch(() => { degraded.push("translation"); return null; }) : null;
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
  const vector = await embed(env, query).catch(() => { degraded.push("embedding"); return null; });
  if (!vector) mode = "bm25";
  const bestCosine = mode === "vector" || !vector ? null
    : qdrant(env, `/collections/${env.COLLECTION}/points/query`, { query: vector, using: shared.DENSE, filter, limit: 1 })
      .then((r) => r.points[0]?.score ?? 0);
  if (mode === "bm25") {
    body = named.length
      ? { prefetch: [{ query: sparse, using: shared.SPARSE, filter, limit: 50 }, ...named], query: { fusion: "rrf" }, limit }
      : { query: sparse, using: shared.SPARSE, filter, limit };
  } else {
    body = mode === "vector"
      ? { query: vector, using: shared.DENSE, filter, limit }
      : {
        prefetch: [{ query: vector, using: shared.DENSE, filter, limit: 50 },
          { query: sparse, using: shared.SPARSE, filter, limit: 50 }, ...named],
        query: { fusion: "rrf" }, limit,
      };
  }
  // perPaper: the best passage of each paper (Qdrant groups by doc_id), so one paper cannot fill the list.
  const points = opts.perPaper
    ? (await qdrant(env, `/collections/${env.COLLECTION}/points/query/groups`,
      { ...body, group_by: "doc_id", group_size: 1, with_payload: PAYLOAD })).groups.map((g) => g.hits[0])
    : (await qdrant(env, `/collections/${env.COLLECTION}/points/query`, { ...body, with_payload: PAYLOAD })).points;
  // A failing reranker (Workers AI quota, outage) leaves the first-stage order rather than failing the search.
  let reranked = rerank, ranked = points.slice(0, topK);
  if (rerank) ranked = await within(12000, subq ? subqRerank(env, query, points, topK) : rerankPoints(env, query, points, topK))
    .catch((e) => { console.log("rerank", String(e)); degraded.push("rerank"); reranked = false; return ranked; });
  const hits = ranked.map((p, i) => ({ n: i + 1, score: p.score, label: sourceLabel(p.payload), ...p.payload }));
  const check = relevance(query, hits, mode === "vector" ? (points[0]?.score ?? 0) : await bestCosine);
  return { question, searchQuery, mode, degraded, topK, perPaper: Boolean(opts.perPaper), reranked, materials: crystalsIn(searchQuery ? `${question} ${searchQuery}` : question), hits, relevance: check, ms: Date.now() - started };
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
  // page through the scroll API: a book has thousands of chunks (at most 20 pages of 500)
  const points = [];
  let offset = null;
  for (let i = 0; i < 20; i++) {
    const result = await qdrant(env, `/collections/${env.COLLECTION}/points/scroll`, {
      filter: { must: [{ key: "doc_id", match: { value: docId } }] }, limit: 500, with_payload: PAYLOAD,
      ...(offset !== null ? { offset } : {}),
    });
    points.push(...result.points);
    offset = result.next_page_offset ?? null;
    if (offset === null) break;
  }
  const chunks = points.map((p) => p.payload)
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

// ---------- keys for the OCR workflow (.github/workflows/ocr.yml) on GitHub's runners
// A runner proves which workflow it runs with GitHub's signed OIDC token; only this repository's OCR workflow
// gets the keys, so none has to be stored in the (public) repository.
async function ciKeys(request, env) {
  const claims = await verifyOidc((request.headers.get("authorization") || "").replace(/^Bearer /i, ""));
  if (!claims) return json({ error: "not this repository's OCR or quality workflow" }, 403);
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`ocr-artifacts:${env.QDRANT_API_KEY}`));
  return json({ SITE_KEY: env.SITE_PASSWORD, QDRANT_URL: env.QDRANT_URL, QDRANT_API_KEY: env.QDRANT_API_KEY, SUBQ_KEYS: env.SUBQ_KEYS || "",
    ARTIFACT_KEY: [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("") });
}

async function handle(request, env, ctx) {
  const url = new URL(request.url);
  if (url.pathname === "/ci/keys" && request.method === "POST") return ciKeys(request, env);
  if (url.pathname === "/tg/webhook" && request.method === "POST") return telegramWebhook(request, env);
  // A user's name and password from the form, or the owner's shared password (form without a name, or the
  // /?key= link); the browser is then remembered (owner a year, users 30 days).
  let given = url.searchParams.get("key"), name = "";
  if (given === null && url.pathname === "/login" && request.method === "POST") {
    const form = await request.formData();
    given = form.get("password"); name = String(form.get("username") || "").trim().toLowerCase();
  }
  if (given !== null) {
    const owner = env.SITE_PASSWORD && (!name || name === "owner") && given === env.SITE_PASSWORD;
    const user = owner ? "owner" : name && (await checkLogin(env, name, String(given))) ? name : null;
    ctx?.waitUntil(logEvent(env, user ? "login" : "failedlogin", {}, user || (name || "?").slice(0, 32).replace(/[^a-z0-9_.-]/g, "_")));
    if (user) {
      const days = user === "owner" ? 365 : 30;
      return new Response(null, { status: 303, headers: {
        location: "/", "set-cookie": `session=${await makeSession(env, user, days)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${days * 86400}` } });
    }
    await new Promise((r) => setTimeout(r, 800));
    return html(LOGIN.replace("<!--error-->", '<p class="err">نام کاربری یا رمز درست نیست. / Wrong username or password.</p>'), 401);
  }
  if (url.pathname === "/logout") {
    return new Response(null, { status: 303, headers: { location: "/", "set-cookie": "session=; Path=/; Max-Age=0" } });
  }
  const acc = await signedIn(request, env);
  if (!acc) {
    return url.pathname.startsWith("/api/") ? json({ error: "login required" }, 401) : html(LOGIN);
  }
  const user = acc.name;
  const settings = await getSettings(env);
  if (settings.maintenance && acc.role !== "owner") {
    return url.pathname.startsWith("/api/") ? json({ error: "maintenance" }, 503) : html(MAINTENANCE, 503);
  }
  const denied = (what) => json({ error: what }, 403);
  // Accounts without the papers' PDFs get no trace of them: no file path, Drive link or place on the page.
  const PDF_FIELDS = ["source_file", "drive_id", "boxes", "pdf_mismatch"];
  const noPdf = (rows) => (acc.pdf ? rows : rows.map((r) => Object.fromEntries(Object.entries(r).filter(([k]) => !PDF_FIELDS.includes(k)))));
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
    if (!acc.pdf) return denied("PDFs are not available on this account");
    const path = url.pathname.slice("/pdf".length);
    // Range requests (pdf.js reads a large PDF in parts): the PDF Worker's static assets always send the whole
    // file, so the range is cut here; only that part goes over the reader's connection.
    const response = await env.PDFS.fetch(new Request(`https://pdfs${path}`));
    if (!response.ok || !(response.headers.get("content-type") || "").includes("pdf")) return json({ error: "no pdf" }, 404);
    const headers = { "content-type": "application/pdf", "cache-control": "private, max-age=86400", "x-robots-tag": "noindex",
      "accept-ranges": "bytes" };
    const m = /^bytes=(\d*)-(\d*)$/.exec(request.headers.get("range") || "");
    if (!m || (m[1] === "" && m[2] === "")) {
      if (response.headers.get("content-length")) headers["content-length"] = response.headers.get("content-length");
      return new Response(response.body, { headers });
    }
    const data = new Uint8Array(await response.arrayBuffer()), size = data.length;
    const start = m[1] === "" ? Math.max(0, size - Number(m[2])) : Number(m[1]);
    const end = m[1] === "" || m[2] === "" ? size - 1 : Math.min(Number(m[2]), size - 1);
    if (start > end || start >= size) return new Response(null, { status: 416, headers: { "content-range": `bytes */${size}` } });
    return new Response(data.subarray(start, end + 1), { status: 206, headers: {
      ...headers, "content-range": `bytes ${start}-${end}/${size}`, "content-length": String(end - start + 1) } });
  }
  try {
    if ((url.pathname === "/api/search" || url.pathname === "/api/pack") && request.method === "POST") {
      if (!acc.search) return denied("search is not available on this account");
      if (!(await takeQuota(env, acc))) return json({ error: `daily limit of ${acc.quota} searches reached / سهمیه‌ی روزانه‌ی ${acc.quota} جست‌وجو تمام شد` }, 429);
    }
    if (url.pathname === "/api/search" && request.method === "POST") {
      const found = await search(env, await request.json().catch(() => ({})));
      // every question is kept (log:), the ones the collection cannot answer also go to Telegram
      const none = !found.hits.length || found.relevance?.verdict === "none";
      const log = logEvent(env, none ? "unanswered" : "search", { question: found.question, searchQuery: found.searchQuery,
        verdict: found.relevance?.verdict, hits: found.hits.length, top: found.hits[0]?.doc_id }, user);
      ctx?.waitUntil(none ? Promise.all([log, unanswered(env, found, user)]) : log);
      return json({ ...found, hits: noPdf(found.hits) });
    }
    if (url.pathname === "/api/feedback" && request.method === "POST") return json(await feedback(env, await request.json().catch(() => ({})), user));
    if (url.pathname === "/api/pack" && request.method === "POST") {
      const found = await search(env, await request.json().catch(() => ({})));
      return new Response(packFile(found), { headers: {
        "content-type": "text/markdown; charset=utf-8",
        "content-disposition": `attachment; filename="matrag-sources-${Date.now()}.md"` } });
    }
    if (url.pathname === "/api/me") return json({ user, role: acc.role, tabs: acc.tabs, pdf: acc.pdf, search: acc.search, quota: acc.quota, banner: settings.banner || "" });
    if (url.pathname === "/api/facets") return json(await facets(env));
    if (url.pathname === "/api/papers") return json(PAPERS);
    if (url.pathname === "/api/incollection" && request.method === "POST") {
      return json(await inCollection(env, (await request.json()).ids));
    }
    if (url.pathname === "/api/paper") {
      const data = await paper(env, url.searchParams.get("doc_id") || "");
      return json({ ...data, chunks: noPdf(data.chunks || []) });
    }
  } catch (error) {
    return json({ error: String(error.message || error) }, error.status || 500);
  }
  return json({ error: "not found" }, 404);
}

export default {
  fetch: handle,
  async scheduled(event, env, ctx) {
    ctx.waitUntil(qdrant(env, `/collections/${env.COLLECTION}`).then((info) => console.log("qdrant ok", info.points_count)));
    ctx.waitUntil(dailySummary(env));
  },
};
