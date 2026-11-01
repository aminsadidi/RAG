// The Worker (src/index.js) in Node, with a fake KV, Workers AI and Qdrant: the tests send it Requests.
import { register } from "node:module";

register("./loader.mjs", import.meta.url);
const { default: worker } = await import("../../src/index.js");
export { worker };

// KV with list() metadata and TTLs ignored, as Workers KV; `fail` makes every put throw (the daily write limit)
export function kv() {
  const m = new Map();
  const store = {
    fail: false, puts: 0,
    get: async (k, t) => (m.has(k) ? (t === "json" ? JSON.parse(m.get(k).v) : m.get(k).v) : null),
    put: async (k, v, o = {}) => { if (store.fail) throw new Error("KV put() limit exceeded for the day."); store.puts++; m.set(k, { v, metadata: o.metadata }); },
    delete: async (k) => { m.delete(k); },
    list: async ({ prefix = "" } = {}) => ({ keys: [...m.keys()].filter((k) => k.startsWith(prefix)).sort().map((name) => ({ name, metadata: m.get(name).metadata })), list_complete: true }),
    map: m,
  };
  return store;
}

export const env = (extra = {}) => ({ AICACHE: kv(), SITE_PASSWORD: "owner-pass", SESSION_SECRET: "session-secret",
  COLLECTION: "rag-optics", QDRANT_URL: "https://qdrant.test", QDRANT_API_KEY: "qk", ...extra });

export const ctx = () => { const waits = []; return { waitUntil: (p) => waits.push(Promise.resolve(p).catch(() => {})), waits }; };

export async function call(e, path, init = {}) {
  const c = ctx();
  const r = await worker.fetch(new Request(`https://site.test${path}`, init), e, c);
  await Promise.all(c.waits);
  return r;
}

export const form = (o) => ({ method: "POST", body: new URLSearchParams(o), headers: { "content-type": "application/x-www-form-urlencoded", "cf-connecting-ip": "1.2.3.4" } });
export const cookieOf = (r) => /session=([^;]*)/.exec(r.headers.get("set-cookie") || "")?.[1];

// The Counters Durable Object over node:sqlite, as a DO namespace binding; `down` makes it unreachable
export async function countersNamespace() {
  const { DatabaseSync } = await import("node:sqlite");
  const { Counters } = await import("../../src/counters.js");
  const db = new DatabaseSync(":memory:");
  const sql = { exec: (q, ...args) => { const st = db.prepare(q); const rows = /^\s*select/i.test(q) ? st.all(...args) : (st.run(...args), []); return { toArray: () => rows }; } };
  const obj = new Counters({ storage: { sql } });
  const ns = { down: false, idFromName: (n) => n, get: () => ({ fetch: async (url, init) => {
    if (ns.down) throw new Error("Durable Object unreachable");
    return obj.fetch(new Request(url, init));
  } }) };
  return ns;
}

// Workers AI that answers each model with a fixed output and counts the calls
export function fakeAI(answers = {}) {
  const calls = [];
  return { calls, run: async (model, input) => {
    calls.push({ model, input });
    if (answers[model] instanceof Error) throw answers[model];
    if (typeof answers[model] === "function") return answers[model](input);
    if (model.includes("bge-base")) return { data: [new Array(768).fill(0.01)] };
    if (model.includes("reranker")) return { response: [] };
    return { response: answers[model] ?? "specific" };
  } };
}

// A Qdrant that returns `points` for every query (with the best cosine for the batch's second search), through a
// replaced global fetch; `seen` keeps the request bodies
export function fakeQdrant(points, extra = () => null) {
  const seen = [];
  const real = globalThis.fetch;
  globalThis.fetch = async (url, init = {}) => {
    const u = String(url);
    const body = init.body ? JSON.parse(init.body) : undefined;
    seen.push({ url: u, body });
    const own = await extra(u, body, init);
    if (own) return own;
    if (!u.startsWith("https://qdrant.test")) throw new Error(`unexpected fetch ${u}`);
    let result;
    if (u.endsWith("/points/query/batch")) result = [{ points }, { points: [{ score: 0.8 }] }];
    else if (u.endsWith("/points/query")) result = { points };
    else if (u.endsWith("/points/query/groups")) result = { groups: points.map((p) => ({ hits: [p] })) };
    else if (u.endsWith("/points/scroll")) result = { points, next_page_offset: null };
    else if (u.endsWith("/points")) result = [];
    else if (u.endsWith("/facet")) result = { hits: [] };
    else result = { points_count: points.length };
    return new Response(JSON.stringify({ result }), { headers: { "content-type": "application/json" } });
  };
  return { seen, restore: () => { globalThis.fetch = real; } };
}

export const point = (i, payload = {}) => ({ id: `id-${i}`, score: 1 / (i + 1), payload: { doc_id: `doc${i}`, node_id: `doc${i}::${i}`,
  text: `LiNbO3 refractive index Sellmeier passage ${i}`, citation: `Author ${i} (2000)`, pages: "1", first_page: 1, material: "LiNbO3", ...payload } });

// The Cache API (caches.default) in memory
export function fakeCaches() {
  const m = new Map();
  globalThis.caches = { default: { match: async (u) => (m.has(String(u)) ? new Response(m.get(String(u))) : undefined),
    put: async (u, r) => { m.set(String(u), await r.text()); } } };
  return m;
}

export async function ownerCookie(e) {
  const { makeSession } = await import("../../src/accounts.js");
  return makeSession(e, "owner", 1);
}
