// Accounts of the site's users (KV user:<name>), made and managed from the owner's Telegram (admin.js).
// Passwords are generated here (random, 10 characters), so a salted SHA-256 is enough; sessions are signed
// cookies "<user>.<expiry>.<hmac>". The owner keeps the old shared password (the /?key= link) as "owner".
const enc = new TextEncoder();
const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
export const NAME = /^[a-z0-9][a-z0-9_.-]{2,31}$/;
const DAY = 86400;

async function hmac(env, text) {
  const key = await crypto.subtle.importKey("raw", enc.encode(`matrag-users:${env.SITE_PASSWORD}`),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", key, enc.encode(text)));
}
const hash = async (salt, password) => hex(await crypto.subtle.digest("SHA-256", enc.encode(`${salt}:${password}`)));

export function newPassword(n = 10) {
  const abc = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789";  // no 0/O, 1/l/I
  return [...crypto.getRandomValues(new Uint8Array(n))].map((b) => abc[b % abc.length]).join("");
}

export async function makeSession(env, user, days = 30) {
  const payload = `${user}.${Math.floor(Date.now() / 1000) + days * DAY}`;
  return `${payload}.${await hmac(env, payload)}`;
}

// The user of a signed session cookie, or null (bad signature, expired, or the account was disabled).
export async function sessionUser(env, token) {
  const m = /^([a-z0-9][a-z0-9_.-]{2,31})\.(\d+)\.([0-9a-f]{64})$/.exec(token || "");
  if (!m || Number(m[2]) < Date.now() / 1000 || (await hmac(env, `${m[1]}.${m[2]}`)) !== m[3]) return null;
  if (m[1] === "owner") return "owner";
  const u = await getUser(env, m[1]);
  return u && usable(u) ? m[1] : null;
}

export const usable = (u) => u.active && !(u.expires && u.expires < Date.now());
export async function getUser(env, name) { return env.AICACHE ? env.AICACHE.get(`user:${name}`, "json") : null; }
async function putUser(env, name, u) {
  await env.AICACHE.put(`user:${name}`, JSON.stringify(u), {
    metadata: { active: u.active, expires: u.expires || 0, created: u.created, note: (u.note || "").slice(0, 120) } });
}

export async function checkLogin(env, name, password) {
  const u = await getUser(env, name);
  return Boolean(u && usable(u) && (await hash(u.salt, password)) === u.hash);
}

export async function createUser(env, name, days, note) {
  if (!NAME.test(name) || name === "owner") throw new Error("نام کاربری: ۳ تا ۳۲ حرف کوچک انگلیسی، عدد، _ . -");
  if (await getUser(env, name)) throw new Error(`«${name}» از قبل هست`);
  const password = newPassword(), salt = newPassword(16);
  await putUser(env, name, { salt, hash: await hash(salt, password), active: true, created: Date.now(),
    expires: days ? Date.now() + days * DAY * 1000 : 0, note: note || "" });
  return password;
}

export async function updateUser(env, name, change) {
  const u = await getUser(env, name);
  if (!u) throw new Error(`کاربر «${name}» نیست`);
  let password;
  if (change.resetPassword) { password = newPassword(); u.salt = newPassword(16); u.hash = await hash(u.salt, password); }
  if ("active" in change) u.active = change.active;
  if (change.extendDays) u.expires = Math.max(u.expires || Date.now(), Date.now()) + change.extendDays * DAY * 1000;
  if (change.noExpiry) u.expires = 0;
  await putUser(env, name, u);
  return { user: u, password };
}

export async function deleteUser(env, name) {
  if (!(await getUser(env, name))) throw new Error(`کاربر «${name}» نیست`);
  await env.AICACHE.delete(`user:${name}`);
}

export async function listUsers(env) {
  const out = [];
  let cursor;
  do {
    const page = await env.AICACHE.list({ prefix: "user:", cursor });
    for (const k of page.keys) out.push({ name: k.name.slice(5), ...(k.metadata || {}) });
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  return out;
}
