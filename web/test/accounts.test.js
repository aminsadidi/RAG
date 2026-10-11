import test from "node:test";
import assert from "node:assert/strict";
import { checkLogin, createUser, makeSession, sessionUser, updateUser } from "../src/accounts.js";
import { telegramWebhook } from "../src/admin.js";

// KV with list() metadata, as Workers KV
function kv() {
  const m = new Map();
  return {
    get: async (k, t) => (m.has(k) ? (t === "json" ? JSON.parse(m.get(k).v) : m.get(k).v) : null),
    put: async (k, v, o = {}) => { m.set(k, { v, metadata: o.metadata }); },
    delete: async (k) => { m.delete(k); },
    list: async ({ prefix }) => ({ keys: [...m.keys()].filter((k) => k.startsWith(prefix)).sort().map((name) => ({ name, metadata: m.get(name).metadata })), list_complete: true }),
  };
}
const env = () => ({ AICACHE: kv(), SITE_PASSWORD: "site-secret", TELEGRAM_TOKEN: "t", TELEGRAM_CHAT_ID: "359353459", TG_WEBHOOK_SECRET: "hook" });

test("accounts: create, log in, session, disable logs out, expiry", async () => {
  const e = env();
  const pw = await createUser(e, "ali", 0, "test");
  assert.equal(pw.length, 10);
  assert.ok(await checkLogin(e, "ali", pw));
  assert.ok(!(await checkLogin(e, "ali", "wrong")));
  const s = await makeSession(e, "ali");
  assert.equal(await sessionUser(e, s), "ali");
  assert.equal(await sessionUser(e, s.replace(/.$/, (c) => (c === "0" ? "1" : "0"))), null);  // forged
  await updateUser(e, "ali", { active: false });
  assert.equal(await sessionUser(e, s), null);
  assert.ok(!(await checkLogin(e, "ali", pw)));
  await updateUser(e, "ali", { active: true });
  const { password } = await updateUser(e, "ali", { resetPassword: true });
  assert.ok(!(await checkLogin(e, "ali", pw)) && (await checkLogin(e, "ali", password)));
  await assert.rejects(createUser(e, "ali", 0, ""));
  await assert.rejects(createUser(e, "Bad Name", 0, ""));
  await createUser(e, "short", 1, "");
  const u = JSON.parse((await e.AICACHE.get("user:short")) ? JSON.stringify(await e.AICACHE.get("user:short", "json")) : "{}");
  assert.ok(u.expires > Date.now() && u.expires < Date.now() + 2 * 86400e3);
});

test("admin bot: only the owner, only with Telegram's secret", async () => {
  const e = env();
  const sent = [];
  globalThis.fetch = async (url, init) => { sent.push(JSON.parse(init.body).text); return new Response("{}"); };
  const call = (from, text, secret = "hook", type = "private") => telegramWebhook(new Request("https://x/tg/webhook", {
    method: "POST", headers: { "x-telegram-bot-api-secret-token": secret },
    body: JSON.stringify({ message: { text, from: { id: from }, chat: { id: from, type } } }) }), e);
  assert.equal((await call(359353459, "/adduser ali 30", "wrong")).status, 403);
  await call(111, "/adduser mallory");
  await call(359353459, "/adduser bob", "hook", "group");
  assert.equal(sent.length, 0);
  assert.equal(await e.AICACHE.get("user:mallory"), null);
  await call(359353459, "/adduser bob 30 دانشجوی آزمایشگاه");
  assert.match(sent.at(-1), /نام کاربری: bob\nرمز: \S{10}/);
  await call(359353459, "/users");
  assert.match(sent.at(-1), /✅ bob/);
  await call(359353459, "/disable bob");
  await call(359353459, "/users");
  assert.match(sent.at(-1), /⛔ bob/);
  await call(359353459, "/nonsense");
  assert.match(sent.at(-1), /help/);
});
