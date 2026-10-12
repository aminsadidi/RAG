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
  assert.equal((await sessionUser(e, s)).name, "ali");
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

test("admin panel: buttons, a user made in three steps, only the owner", async () => {
  const e = env();
  const sent = [];
  globalThis.fetch = async (url, init) => { sent.push({ method: url.split("/").pop(), ...JSON.parse(init.body) }); return new Response("{}"); };
  const post = (body, secret = "hook") => telegramWebhook(new Request("https://x/tg/webhook", {
    method: "POST", headers: { "x-telegram-bot-api-secret-token": secret }, body: JSON.stringify(body) }), e);
  const text = (t, from = 359353459, type = "private") => post({ message: { text: t, from: { id: from }, chat: { id: from, type } } });
  const press = (data, from = 359353459) => post({ callback_query: { id: "1", data, from: { id: from }, message: { message_id: 7, chat: { id: from, type: "private" } } } });
  const last = () => sent.filter((x) => x.text).at(-1);
  const buttons = () => last().reply_markup.inline_keyboard.flat().map((b) => b.callback_data);

  assert.equal((await text("/amin", 359353459)).status, 200);
  assert.match(last().text, /پنل مدیریت/);
  assert.ok(buttons().includes("new") && buttons().includes("ul:0") && buttons().includes("maint"));
  // strangers: no answer, no change
  const before = sent.length;
  await text("/amin", 42); await press("new", 42); await press("maint", 42); await text("/amin", 359353459, "group");
  assert.equal((await post({ message: { text: "/amin", from: { id: 359353459 }, chat: { id: 359353459, type: "private" } } }, "wrong")).status, 403);
  assert.equal(sent.length, before);
  assert.equal((await e.AICACHE.get("site:settings", "json"))?.maintenance ?? false, false);
  // new user: button, name (+ note), access level, validity
  await press("new"); await text("sara دانشجوی آزمایشگاه"); assert.ok(buttons().includes("nr:guest"));
  await press("nr:guest"); assert.ok(buttons().includes("nd:30"));
  await press("nd:30");
  assert.match(last().text, /نام کاربری: sara\nرمز: \S{10}\nسطح دسترسی: مهمان/);
  const u = await e.AICACHE.get("user:sara", "json");
  assert.equal(u.role, "guest"); assert.equal(u.note, "دانشجوی آزمایشگاه");
  // user card actions
  await press("urs:sara:tools"); assert.equal((await e.AICACHE.get("user:sara", "json")).role, "tools");
  await press("uqs:sara:30"); assert.equal((await e.AICACHE.get("user:sara", "json")).quota, 30);
  await press("uoff:sara"); assert.equal((await e.AICACHE.get("user:sara", "json")).active, false);
  // site settings
  await press("maint"); assert.equal((await e.AICACHE.get("site:settings", "json")).maintenance, true);
  await press("banner"); await text("سرور امشب به‌روز می‌شود");
  assert.equal((await e.AICACHE.get("site:settings", "json")).banner, "سرور امشب به‌روز می‌شود");
  await press("udel:sara"); await press("udely:sara"); assert.equal(await e.AICACHE.get("user:sara"), null);
});
