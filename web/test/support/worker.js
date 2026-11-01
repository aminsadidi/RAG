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
