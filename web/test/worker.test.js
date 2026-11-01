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

test("the scope verdict's cache key holds the scope prompt (an edited prompt is not served old verdicts)", async () => {
  const { SCOPE_PROMPT: prompt } = await import("../src/text.js");  // loaded through the test's module hooks
  const model = "@cf/meta/llama-3.3-70b-instruct-fp8-fast";
  const e = env({ AI: fakeAI(), TRANSLATE_MODEL: model, EMBED_MODEL: "@cf/baai/bge-base-en-v1.5" });
  const cacheApi = fakeCaches();
  const q = fakeQdrant([point(0)]);
  try {
    const c = await ownerCookie(e);
    await call(e, "/api/search", withCookie(c, { method: "POST", body: JSON.stringify({ q: "BBO cut angle" }), headers: { "content-type": "application/json" } }));
  } finally { q.restore(); delete globalThis.caches; }
  const { createHash } = await import("node:crypto");
  const key = (input) => `https://matrag-cache.invalid/${createHash("sha256").update(`${model}\n${input}`).digest("hex")}`;
  assert.ok(cacheApi.has(key(`scope\n${prompt}\nBBO cut angle`)));
  assert.ok(!cacheApi.has(key("scope\nBBO cut angle")));
});

test("HTML pages carry a CSP with a fresh nonce on every inline script, and anti-framing headers", async () => {
  const e = env();
  const c = await ownerCookie(e);
  const nonces = [];
  for (let i = 0; i < 2; i++) {
    const r = await call(e, "/", withCookie(c));
    const policy = r.headers.get("content-security-policy");
    const nonce = /'nonce-([^']+)'/.exec(policy)[1];
    nonces.push(nonce);
    assert.match(policy, /frame-ancestors 'none'/); assert.match(policy, /object-src 'none'/); assert.ok(!/script-src[^;]*unsafe-inline/.test(policy));
    assert.equal(r.headers.get("x-frame-options"), "DENY");
    assert.equal(r.headers.get("referrer-policy"), "same-origin");
    assert.equal(r.headers.get("x-content-type-options"), "nosniff");
    const body = await r.text();
    const scripts = body.match(/<script\b[^>]*>/g);
    assert.ok(scripts.length > 5 && scripts.every((t) => t.includes(`nonce="${nonce}"`)), "every inline script has the nonce");
    assert.ok(!body.includes("__CSP_NONCE__"));
    assert.ok(!/\son(click|error|load|input|change)="/i.test(body), "no inline event handlers (the CSP blocks them)");
  }
  assert.notEqual(nonces[0], nonces[1]);
  const login = await call(e, "/");
  assert.match(login.headers.get("content-security-policy"), /frame-ancestors 'none'/);
});

const search = (e, c, body) => call(e, "/api/search", withCookie(c, { method: "POST", body: JSON.stringify(body), headers: { "content-type": "application/json" } }));
const searchEnv = (extra = {}) => env({ AI: fakeAI(), TRANSLATE_MODEL: "@cf/meta/llama-3.3-70b-instruct-fp8-fast", EMBED_MODEL: "@cf/baai/bge-base-en-v1.5", ...extra });

test("a failing best-cosine request does not fail the search", async () => {
  const e = searchEnv();
  const q = fakeQdrant([point(0), point(1)], (u, body) => (u.endsWith("/points/query") && body?.limit === 1 ? new Response("{}", { status: 500 }) : null));
  try {
    const r = await search(e, await ownerCookie(e), { q: "LiNbO3 Sellmeier", perPaper: true });  // perPaper: the cosine has its own request
    assert.equal(r.status, 200);
    const j = await r.json();
    assert.equal(j.hits.length, 2); assert.ok(j.degraded.includes("cosine"));
  } finally { q.restore(); }
});

test("SubQ: a missing answer scores -1, never NaN, and an incomplete answer is not cached", async () => {
  const e = searchEnv({ SUBQ_KEYS: "k1" });
  const pts = [point(0), point(1), point(2)];
  let subqCalls = 0;
  const q = fakeQdrant(pts, (u, body) => {
    if (!u.startsWith("https://api.subq.ai")) return null;
    subqCalls++;
    return Response.json({ answers: { p0: { noul: 0.2 }, p2: { noul: 0.9 } } });  // p1 missing
  });
  try {
    const c = await ownerCookie(e);
    const j = await (await search(e, c, { q: "LiNbO3 Sellmeier" })).json();
    assert.ok(j.reranked);
    assert.ok(j.hits.every((h) => Number.isFinite(h.score)), JSON.stringify(j.hits.map((h) => h.score)));
    assert.deepEqual(j.hits.map((h) => h.doc_id), ["doc2", "doc0", "doc1"]);
    assert.ok(![...e.AICACHE.map.keys()].some((k) => !k.startsWith("log:")), "nothing cached");
    await search(e, c, { q: "LiNbO3 Sellmeier" });
    assert.equal(subqCalls, 2);  // asked again
  } finally { q.restore(); }
});

test("an account without search gets no collection lists (facets, papers, in-collection)", async () => {
  const e = searchEnv();
  const pw = await createUser(e, "toolsonly", 0, "", "tools");
  const c = cookieOf(await call(e, "/login", form({ username: "toolsonly", password: pw })));
  const q = fakeQdrant([point(0)]);
  try {
    for (const [path, init] of [["/api/facets", {}], ["/api/papers", {}], ["/api/incollection", { method: "POST", body: JSON.stringify({ ids: ["doc0"] }) }], ["/api/paper?doc_id=doc0", {}]])
      assert.equal((await call(e, path, withCookie(c, init))).status, 403, path);
    const owner = await ownerCookie(e);
    assert.equal((await call(e, "/api/papers", withCookie(owner))).status, 200);
  } finally { q.restore(); }
});

test("logout is a POST from the site itself; a GET only shows a button", async () => {
  const e = env();
  const get = await call(e, "/logout");
  assert.equal(get.status, 200); assert.equal(get.headers.get("set-cookie"), null); assert.equal(get.headers.get("clear-site-data"), null);
  assert.match(await get.text(), /method="post" action="\/logout"/);
  const cross = await call(e, "/logout", { method: "POST", headers: { origin: "https://evil.example" } });
  assert.equal(cross.status, 403); assert.equal(cross.headers.get("clear-site-data"), null);
  const own = await call(e, "/logout", { method: "POST", headers: { origin: "https://site.test" } });
  assert.equal(own.status, 303); assert.match(own.headers.get("set-cookie"), /Max-Age=0/); assert.ok(own.headers.get("clear-site-data"));
});

test("the page logs out with a POST form and offers the reader's own formulas first", async () => {
  const { readFileSync } = await import("node:fs");
  const page = readFileSync(new URL("../src/page.html", import.meta.url), "utf8");
  assert.ok(!page.includes('href="/logout"'));
  assert.match(page, /<form method="post" action="\/logout"[^>]*id="logoutf"/);
  assert.match(page, /localStorage\.getItem\("ri_user"/); assert.match(page, /matrag-my-formulas\.json/);
});

test("the CI account's searches are neither logged nor sent to Telegram", async () => {
  const e = searchEnv({ CI_USER: "ci-bot", TELEGRAM_TOKEN: "t", TELEGRAM_CHAT_ID: "1" });
  const pw = await createUser(e, "ci-bot", 0, "", "search");
  const ci = cookieOf(await call(e, "/login", form({ username: "ci-bot", password: pw })));
  const sent = [];
  const q = fakeQdrant([], (u) => (u.startsWith("https://api.telegram.org") ? (sent.push(u), Response.json({ ok: true })) : null));
  try {
    const logsBefore = [...e.AICACHE.map.keys()].filter((k) => k.startsWith("log:")).length;  // the login itself
    assert.equal((await search(e, ci, { q: "zzqx unknown crystal" })).status, 200);  // no hits: unanswered
    assert.equal([...e.AICACHE.map.keys()].filter((k) => k.startsWith("log:")).length, logsBefore);
    assert.equal(sent.length, 0);
    assert.equal((await search(e, await ownerCookie(e), { q: "zzqx unknown crystal" })).status, 200);
    assert.equal(sent.length, 0);  // not at once: the hourly cron sends the hour's questions together
    const worker = (await import("../src/index.js")).default;
    const waits = [];
    await worker.scheduled({ cron: "5 * * * *", scheduledTime: Date.now() + 3600000 }, e, { waitUntil: (p) => waits.push(p) });
    assert.deepEqual(await Promise.all(waits), [1]);  // anyone else's unanswered question still is, the CI's not
    assert.equal(sent.length, 1);
  } finally { q.restore(); }
});

test("new accounts get a daily quota by access level; a default quota follows a change of level", async () => {
  const { DEFAULT_QUOTA, getUser, updateUser } = await import("../src/accounts.js");
  const e = env();
  await createUser(e, "full1", 0, ""); await createUser(e, "guest1", 0, "", "guest");
  assert.equal((await getUser(e, "full1")).quota, DEFAULT_QUOTA.full);
  assert.equal((await getUser(e, "guest1")).quota, DEFAULT_QUOTA.guest);
  assert.ok(DEFAULT_QUOTA.full >= 300 && DEFAULT_QUOTA.guest === 50);
  await updateUser(e, "guest1", { role: "full" });
  assert.equal((await getUser(e, "guest1")).quota, DEFAULT_QUOTA.full);
  await updateUser(e, "full1", { quota: 0 }); await updateUser(e, "full1", { role: "guest" });
  assert.equal((await getUser(e, "full1")).quota, 0);  // set by hand (unlimited): kept
});

test("the scope check runs on SCOPE_MODEL when set", async () => {
  const ai = fakeAI();
  const e = searchEnv({ AI: ai, SCOPE_MODEL: "@cf/meta/llama-3.1-8b-instruct" });
  const q = fakeQdrant([point(0)]);
  try {
    assert.equal((await search(e, await ownerCookie(e), { q: "LiNbO3 Sellmeier" })).status, 200);
    const models = ai.calls.map((c) => c.model);
    assert.ok(models.includes("@cf/meta/llama-3.1-8b-instruct"));
    assert.ok(!models.includes(e.TRANSLATE_MODEL), "an English question needs no translation, and the scope check is on the small model");
  } finally { q.restore(); }
});

test("opening papers is limited: per search of the daily quota, and per minute (no copying the collection)", async () => {
  const { updateUser, PAPERS_PER_SEARCH, PAPERS_PER_MINUTE } = await import("../src/accounts.js");
  const e = searchEnv({ COUNTERS: await countersNamespace() });
  const pw = await createUser(e, "reader", 0, "");
  await updateUser(e, "reader", { quota: 2 });
  const c = cookieOf(await call(e, "/login", form({ username: "reader", password: pw })));
  const q = fakeQdrant([point(0)]);
  try {
    const open = () => call(e, "/api/paper?doc_id=doc0", withCookie(c));
    const got = [];
    for (let i = 0; i < PAPERS_PER_SEARCH * 2 + 1; i++) got.push((await open()).status);
    assert.deepEqual(got, [...Array(PAPERS_PER_SEARCH * 2).fill(200), 429]);
    assert.match((await (await open()).json()).error, /papers/);
    // an account without a daily quota still cannot open more than PAPERS_PER_MINUTE a minute
    const pw2 = await createUser(e, "bulk", 0, "");
    const c2 = cookieOf(await call(e, "/login", form({ username: "bulk", password: pw2 })));
    const statuses = [], now = Date.now;
    const t = Math.floor(now() / 60000) * 60000 + 1000;
    Date.now = () => t;  // all in one minute
    try {
      for (let i = 0; i < PAPERS_PER_MINUTE + 1; i++) statuses.push((await call(e, "/api/paper?doc_id=doc0", withCookie(c2))).status);
    } finally { Date.now = now; }
    assert.equal(statuses.filter((s) => s === 200).length, PAPERS_PER_MINUTE);
    assert.equal(statuses.at(-1), 429);
    // the owner is not counted
    const owner = await ownerCookie(e);
    for (let i = 0; i < PAPERS_PER_MINUTE + 1; i++) assert.equal((await call(e, "/api/paper?doc_id=doc0", withCookie(owner))).status, 200);
  } finally { q.restore(); }
});

test("odd login requests get the login page, not an exception: no form body, a huge or odd name, KV down", async () => {
  const e = env();
  const notForm = await call(e, "/login", { method: "POST", headers: { "content-type": "application/json" }, body: "{}" });
  assert.equal(notForm.status, 400); assert.match(await notForm.text(), /type="password"/);
  let gets = 0; const get = e.AICACHE.get.bind(e.AICACHE);
  e.AICACHE.get = async (k, ...rest) => { if (k.startsWith("user:")) gets++; return get(k, ...rest); };
  for (const username of ["x".repeat(600), "Sara!", "../user:owner"])
    assert.equal((await call(e, "/login", form({ username, password: "p" }))).status, 401, username.slice(0, 20));
  assert.equal(gets, 0);  // never looked up
  e.AICACHE.get = async () => { throw new Error("KV down"); };
  const down = await call(e, "/login", form({ username: "sara", password: "p" }));
  assert.equal(down.status, 503); assert.match(await down.text(), /type="password"/);
});

test("the owner can be signed out everywhere (ownerEpoch); users' sessions are untouched", async () => {
  const { setSettings } = await import("../src/accounts.js");
  const e = env();
  const owner = await ownerCookie(e);
  const pw = await createUser(e, "sara", 0, "");
  const sara = cookieOf(await call(e, "/login", form({ username: "sara", password: pw })));
  assert.equal((await call(e, "/api/me", withCookie(owner))).status, 200);
  await setSettings(e, { ownerEpoch: 1 });
  assert.equal((await call(e, "/api/me", withCookie(owner))).status, 401);
  assert.equal((await call(e, "/api/me", withCookie(sara))).status, 200);
  assert.equal((await call(e, "/api/me", withCookie(await ownerCookie(e)))).status, 200);  // a new login works
});

test("a table split over passages is stitched with the neighbours' text and their places on the page", async () => {
  const e = searchEnv();
  const table = { content_type: "table", headings: "Table 2", pages: "4" };
  const hit = point(0, { ...table, node_id: "doc0::5", text: "Table 2 row b", boxes: JSON.stringify([[4, 0.1, 0.4, 0.9, 0.5]]) });
  const part = (n, text, boxes) => ({ id: `n${n}`, payload: { ...table, node_id: `doc0::${n}`, text, boxes: JSON.stringify(boxes) } });
  const neighbours = [part(4, "Table 2 row a", [[4, 0.1, 0.3, 0.9, 0.4]]), part(6, "Table 2 row c", [[4, 0.1, 0.5, 0.9, 0.6], [4, 0.1, 0.4, 0.9, 0.5]]),
    { id: "n7", payload: { node_id: "doc0::7", text: "next section", content_type: "text", headings: "3", pages: "4" } }];
  const q = fakeQdrant([hit], (u, body) => (u.endsWith("/points") && body?.ids ? Response.json({ result: neighbours }) : null));
  try {
    const [h] = (await (await search(e, await ownerCookie(e), { q: "LiNbO3 Sellmeier" })).json()).hits;
    assert.equal(h.text, "Table 2 row a\nrow b\nrow c");
    assert.equal(h.stitched, 2);
    assert.deepEqual(JSON.parse(h.boxes), [[4, 0.1, 0.3, 0.9, 0.4], [4, 0.1, 0.4, 0.9, 0.5], [4, 0.1, 0.5, 0.9, 0.6]]);
  } finally { q.restore(); }
});
