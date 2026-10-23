// Accounts of the site's users (KV user:<name>), made and managed from the owner's Telegram (admin.js).
// Passwords are generated here (random, 10 characters), so a salted SHA-256 is enough; sessions are signed
// cookies "<user>.<expiry>.<hmac>". The owner keeps the old shared password (the /?key= link) as "owner".
const enc = new TextEncoder();
const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
export const NAME = /^[a-z0-9][a-z0-9_.-]{2,31}$/;
const DAY = 86400;

// Access levels: which tabs a user sees and whether the papers' PDFs are served to them.
export const ROLES = {
  full: { label: "کامل", tabs: ["search", "index", "pm", "advisor", "spdc", "library", "about"], search: true, pdf: true },
  guest: { label: "مهمان (بدون PDF)", tabs: ["search", "index", "pm", "advisor", "spdc", "library", "about"], search: true, pdf: false },
  search: { label: "فقط جست‌وجو", tabs: ["search", "about"], search: true, pdf: false },
  tools: { label: "فقط ابزارها", tabs: ["index", "pm", "advisor", "spdc", "about"], search: false, pdf: false },
};
export const OWNER = { name: "owner", role: "owner", quota: 0, tabs: ROLES.full.tabs, search: true, pdf: true };
const account = (name, u) => ({ name, role: u.role || "full", quota: u.quota || 0, ...(ROLES[u.role] || ROLES.full) });

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

// The user's salt is signed too (it changes with every new password), so a new password signs out old sessions.
export async function makeSession(env, user, days = 30) {
  const payload = `${user}.${Math.floor(Date.now() / 1000) + days * DAY}`;
  const salt = user === "owner" ? "" : (await getUser(env, user))?.salt || "";
  return `${payload}.${await hmac(env, `${payload}.${salt}`)}`;
}

// The account of a signed session cookie ({name, role, quota, tabs, search, pdf}), or null (bad signature,
// expired, or the account was disabled since).
export async function sessionUser(env, token) {
  const m = /^([a-z0-9][a-z0-9_.-]{2,31})\.(\d+)\.([0-9a-f]{64})$/.exec(token || "");
  if (!m || Number(m[2]) < Date.now() / 1000) return null;
  const u = m[1] === "owner" ? null : await getUser(env, m[1]);
  if ((await hmac(env, `${m[1]}.${m[2]}.${u?.salt || ""}`)) !== m[3]) return null;
  if (m[1] === "owner") return OWNER;
  return u && usable(u) ? account(m[1], u) : null;
}

export const usable = (u) => u.active && !(u.expires && u.expires < Date.now());
export async function getUser(env, name) { return env.AICACHE ? env.AICACHE.get(`user:${name}`, "json") : null; }
async function putUser(env, name, u) {
  await env.AICACHE.put(`user:${name}`, JSON.stringify(u), {
    metadata: { active: u.active, expires: u.expires || 0, created: u.created, note: (u.note || "").slice(0, 120), role: u.role || "full", quota: u.quota || 0 } });
}

export async function checkLogin(env, name, password) {
  const u = await getUser(env, name);
  return Boolean(u && usable(u) && (await hash(u.salt, password)) === u.hash);
}

export async function createUser(env, name, days, note, role = "full") {
  if (!NAME.test(name) || name === "owner") throw new Error("نام کاربری: ۳ تا ۳۲ حرف کوچک انگلیسی، عدد، _ . -");
  if (await getUser(env, name)) throw new Error(`«${name}» از قبل هست`);
  const password = newPassword(), salt = newPassword(16);
  await putUser(env, name, { salt, hash: await hash(salt, password), active: true, created: Date.now(),
    expires: days ? Date.now() + days * DAY * 1000 : 0, note: note || "", role: ROLES[role] ? role : "full", quota: 0 });
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
  if (change.role && ROLES[change.role]) u.role = change.role;
  if ("quota" in change) u.quota = Math.max(0, change.quota | 0);
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

// Site-wide settings, changed from the panel: an announcement shown to everyone, maintenance mode.
export async function getSettings(env) { return (env.AICACHE && (await env.AICACHE.get("site:settings", "json"))) || { banner: "", maintenance: false }; }
export async function setSettings(env, change) { const s = { ...(await getSettings(env)), ...change }; await env.AICACHE.put("site:settings", JSON.stringify(s)); return s; }

// Daily search quota (0 = none): true if this search may run (and counts it).
// kind: a second counter with its own limit (feedback). A KV failure (the daily write limit) never blocks the reader.
export async function takeQuota(env, acc, kind = "quota") {
  if (!acc.quota || acc.role === "owner" || !env.AICACHE) return true;
  const key = `${kind}:${acc.name}:${new Date().toISOString().slice(0, 10)}`;
  const used = Number(await env.AICACHE.get(key).catch(() => 0)) || 0;
  if (used >= acc.quota) return false;
  await env.AICACHE.put(key, String(used + 1), { expirationTtl: 2 * DAY }).catch((e) => console.log("quota put", String(e)));
  return true;
}
