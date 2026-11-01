// The Worker's own routes (src/index.js), driven in Node with fake bindings (support/worker.js).
import { test } from "node:test";
import assert from "node:assert/strict";
import { call, cookieOf, env, form } from "./support/worker.js";
import { createUser } from "../src/accounts.js";

const withCookie = (c, init = {}) => ({ ...init, headers: { ...(init.headers || {}), cookie: `session=${c}` } });

test("login: the owner and users by the form; a session cookie, signed, is the only way in", async () => {
  const e = env();
  const owner = await call(e, "/login", form({ username: "", password: "owner-pass" }));
  assert.equal(owner.status, 303);
  assert.equal((await (await call(e, "/api/me", withCookie(cookieOf(owner)))).json()).role, "owner");
  const pw = await createUser(e, "sara", 0, "");
  const user = await call(e, "/login", form({ username: "sara", password: pw }));
  assert.equal((await (await call(e, "/api/me", withCookie(cookieOf(user)))).json()).user, "sara");
  assert.equal((await call(e, "/login", form({ username: "owner", password: "wrong" }))).status, 401);
});

test("no login by ?key= (a password in a URL), and the old static owner cookie no longer works", async () => {
  const e = env();
  const r = await call(e, "/?key=owner-pass");
  assert.equal(r.status, 200); assert.equal(r.headers.get("set-cookie"), null);
  assert.match(await r.text(), /type="password"/);  // the login page
  const { createHash } = await import("node:crypto");
  const old = createHash("sha256").update("matrag-session:owner-pass").digest("hex");
  assert.equal((await call(e, "/api/me", withCookie(old))).status, 401);
});

import { countersNamespace } from "./support/worker.js";

test("failed logins are counted in the Counters object even when KV writes are spent, and fail closed", async () => {
  const e = env({ COUNTERS: await countersNamespace() });
  e.AICACHE.fail = true;  // the free plan's 1000 KV writes a day are used up
  for (let i = 0; i < 10; i++) assert.equal((await call(e, "/login", form({ username: "owner", password: "guess" + i }))).status, 401);
  assert.equal((await call(e, "/login", form({ username: "owner", password: "owner-pass" }))).status, 429);
  const other = { ...form({ username: "owner", password: "x" }) }; other.headers = { ...other.headers, "cf-connecting-ip": "5.6.7.8" };
  assert.equal((await call(e, "/login", other)).status, 401);  // another address is not locked out
  e.COUNTERS.down = true;
  assert.equal((await call(e, "/login", { ...other, body: new URLSearchParams({ username: "owner", password: "owner-pass" }) })).status, 503);
});

test("without the Counters object, a KV that cannot count refuses logins instead of allowing unlimited tries", async () => {
  const e = env();
  e.AICACHE.fail = true;
  assert.equal((await call(e, "/login", form({ username: "owner", password: "guess" }))).status, 503);
  e.AICACHE.get = async () => { throw new Error("KV down"); };
  assert.equal((await call(e, "/login", form({ username: "owner", password: "owner-pass" }))).status, 503);
});

test("daily quota is kept in the Counters object when KV writes are spent", async () => {
  const { takeQuota } = await import("../src/accounts.js");
  const e = env({ COUNTERS: await countersNamespace() });
  e.AICACHE.fail = true;
  const acc = { name: "sara", role: "full", quota: 3 };
  const got = [];
  for (let i = 0; i < 5; i++) got.push(await takeQuota(e, acc));
  assert.deepEqual(got, [true, true, true, false, false]);
  assert.ok(await takeQuota(e, { ...acc, name: "ali" }));  // per user
  assert.ok(await takeQuota(e, { ...acc, quota: 1 }, "feedback"));  // per kind
});

import { fakeAI, fakeCaches, fakeQdrant, ownerCookie, point } from "./support/worker.js";

test("the query embedding and the scope check are cached in the Cache API, not in KV (KV writes are scarce)", async () => {
  const e = env({ AI: fakeAI(), TRANSLATE_MODEL: "@cf/meta/llama-3.3-70b-instruct-fp8-fast", EMBED_MODEL: "@cf/baai/bge-base-en-v1.5" });
  const cacheApi = fakeCaches();
  const q = fakeQdrant([point(0), point(1)]);
  try {
    const c = await ownerCookie(e);
    const ask = () => call(e, "/api/search", withCookie(c, { method: "POST", body: JSON.stringify({ q: "LiNbO3 Sellmeier equation" }), headers: { "content-type": "application/json" } }));
    assert.equal((await ask()).status, 200);
    const kvKeys = [...e.AICACHE.map.keys()].filter((k) => !k.startsWith("log:"));
    assert.deepEqual(kvKeys, []);  // neither the embedding nor the scope verdict went to KV
    assert.equal(cacheApi.size, 2);
    const before = e.AI.calls.length;
    assert.equal((await ask()).status, 200);
    assert.equal(e.AI.calls.length, before);  // the second time both come from the cache
  } finally { q.restore(); delete globalThis.caches; }
});
