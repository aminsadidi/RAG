// The web app: searches the knowledge base in Qdrant and gives the sources, never an AI-written answer.
// A question in Persian is translated to English (the papers are in English); the query is embedded with
// the same model and pooling as the Python pipeline, and Qdrant fuses dense and BM25 results with RRF.
import { cleanTranslation, contextPack, expandQuery, isPersian, shared, sourceLabel, translatePrompt } from "./text.js";
import PAGE from "./page.html";
import LOGIN from "./login.html";

const PAYLOAD = [...shared.PAYLOAD_KEYS, "node_id", "text"];
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

async function translate(env, question) {
  const out = await env.AI.run(env.TRANSLATE_MODEL, {
    messages: [{ role: "user", content: translatePrompt(question) }], max_tokens: 120, temperature: 0,
  });
  return cleanTranslation(out.response, question);
}

async function embed(env, query) {
  // "cls" pooling: bge's own pooling, identical to the local sentence-transformers vectors.
  const out = await env.AI.run(env.EMBED_MODEL, { text: [shared.QUERY_INSTRUCTION + query], pooling: "cls" });
  return out.data[0];
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
  let body;
  if (mode === "bm25") {
    body = { query: sparse, using: shared.SPARSE, filter, limit: topK };
  } else {
    const vector = await embed(env, query);
    body = mode === "vector"
      ? { query: vector, using: shared.DENSE, filter, limit: topK }
      : {
        prefetch: [{ query: vector, using: shared.DENSE, filter, limit: 50 },
          { query: sparse, using: shared.SPARSE, filter, limit: 50 }],
        query: { fusion: "rrf" }, limit: topK,
      };
  }
  const result = await qdrant(env, `/collections/${env.COLLECTION}/points/query`, { ...body, with_payload: PAYLOAD });
  const hits = result.points.map((p, i) => ({ n: i + 1, score: p.score, label: sourceLabel(p.payload), ...p.payload }));
  return { question, searchQuery, mode, topK, hits, ms: Date.now() - started };
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

async function paper(env, docId) {
  const result = await qdrant(env, `/collections/${env.COLLECTION}/points/scroll`, {
    filter: { must: [{ key: "doc_id", match: { value: docId } }] }, limit: 400, with_payload: PAYLOAD,
  });
  const chunks = result.points.map((p) => p.payload)
    .sort((a, b) => (a.first_page ?? 0) - (b.first_page ?? 0) || String(a.node_id).localeCompare(String(b.node_id), "en", { numeric: true }));
  return { doc_id: docId, chunks };
}

function packFile(found) {
  const language = found.searchQuery ? "Persian" : null;
  const about = {
    question: found.question,
    ...(found.searchQuery ? { "search query (English)": found.searchQuery } : {}),
    corpus: "rag-optics",
    retrieval: `${found.mode}${found.mode === "hybrid" ? " (dense + BM25, RRF in Qdrant)" : ""}, top ${found.topK}`,
    "embedding model": shared.EMBED_MODEL,
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
  try {
    if (url.pathname === "/api/search" && request.method === "POST") return json(await search(env, await request.json()));
    if (url.pathname === "/api/pack" && request.method === "POST") {
      const found = await search(env, await request.json());
      return new Response(packFile(found), { headers: {
        "content-type": "text/markdown; charset=utf-8",
        "content-disposition": `attachment; filename="matrag-sources-${Date.now()}.md"` } });
    }
    if (url.pathname === "/api/facets") return json(await facets(env));
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
