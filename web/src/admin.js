// The owner's admin panel in Telegram (bot webhook, POST /tg/webhook): /amin opens a panel of inline ("glass")
// buttons that edits itself as you move around. Telegram signs every call with the secret given to setWebhook
// (header X-Telegram-Bot-Api-Secret-Token = TG_WEBHOOK_SECRET); only the owner (TELEGRAM_CHAT_ID), in a private
// chat, is answered; anyone else gets nothing. Free text is read only while the panel waits for it (a new
// user's name, the announcement), the state kept in KV admin:state for 10 minutes.
import { ROLES, createUser, deleteUser, getSettings, getUser, listUsers, setSettings, updateUser, usable } from "./accounts.js";
import { listLogs } from "./feedback.js";

const SITE = "https://matrag.ethanjamescarter1995.workers.dev";
const KIND = { search: "🔎", unanswered: "❓", feedback: "💬", login: "🔑", failedlogin: "🚫" };
const when = (t) => new Date(t).toLocaleString("fa-IR", { timeZone: "Asia/Tehran", dateStyle: "short", timeStyle: "short" });
const ago = (days) => new Date(Date.now() - days * 86400e3).toISOString();
const btn = (text, data) => ({ text, callback_data: data });
const BACK = [btn("🏠 منوی اصلی", "m")];
const PAGE = 8;

async function tg(env, method, payload) {
  const r = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/${method}`, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) });
  if (!r.ok) console.log("telegram", method, r.status, await r.text().catch(() => ""));
  return r;
}
const getState = (env) => env.AICACHE.get("admin:state", "json");
const setState = (env, s) => (s ? env.AICACHE.put("admin:state", JSON.stringify(s), { expirationTtl: 600 }) : env.AICACHE.delete("admin:state"));

function lines(events) {
  return events.map((e) => `${KIND[e.kind] || "•"} ${when(e.time)} · ${e.user}${e.q ? ` · ${e.q}` : ""}${e.v && e.kind === "feedback" ? ` (${e.v})` : ""}`).join("\n");
}
const clip = (t) => (t.length > 3900 ? "…" + t.slice(-3900) : t);
const state = (u) => (!u.active ? "⛔" : u.expires && u.expires < Date.now() ? "⌛" : "✅");

// ---------- screens: each returns {text, keyboard}
async function home(env) {
  const [users, settings, logs] = await Promise.all([listUsers(env), getSettings(env), listLogs(env, ago(1))]);
  const online = new Set(logs.filter((e) => e.time >= ago(1 / 96)).map((e) => e.user)).size;
  const searches = logs.filter((e) => e.kind === "search" || e.kind === "unanswered").length;
  return {
    text: `🔷 پنل مدیریت MatRAG\n\n👥 حساب‌ها: ${users.length} (${users.filter((u) => u.active).length} فعال)\n🟢 در ۱۵ دقیقه‌ی اخیر: ${online} نفر\n🔎 جست‌وجوی ۲۴ ساعت: ${searches}\n` +
      `🛠 حالت تعمیر: ${settings.maintenance ? "روشن (سایت فقط برای شما باز است)" : "خاموش"}\n📢 اعلان: ${settings.banner ? `«${settings.banner}»` : "ندارد"}`,
    keyboard: [
      [btn("👥 کاربران", "ul:0"), btn("➕ کاربر جدید", "new")],
      [btn("📊 آمار", "stats"), btn("🟢 آنلاین‌ها", "online")],
      [btn("❓ بی‌جواب‌ها", "unans"), btn("💬 بازخوردها", "fb")],
      [btn("🕘 فعالیت‌ها", "act"), btn("🔑 ورودهای ناموفق", "fail")],
      [btn("📢 اعلان سایت", "banner"), btn(settings.maintenance ? "🛠 خاموش‌کردن تعمیر" : "🛠 حالت تعمیر", "maint")],
      [btn("🔄 تازه‌سازی", "m")],
    ],
  };
}

async function userList(env, page) {
  const users = (await listUsers(env)).sort((a, b) => (b.created || 0) - (a.created || 0));
  const logs = await listLogs(env, ago(30));
  const count = {};
  for (const e of logs) if (e.kind === "search" || e.kind === "unanswered") count[e.user] = (count[e.user] || 0) + 1;
  const pages = Math.max(1, Math.ceil(users.length / PAGE)), p = Math.min(Math.max(page, 0), pages - 1);
  const rows = users.slice(p * PAGE, p * PAGE + PAGE).map((u) => [btn(`${state(u)} ${u.name} · ${ROLES[u.role]?.label || "کامل"} · ${count[u.name] || 0} جست‌وجو`, `u:${u.name}`)]);
  const nav = [];
  if (p > 0) nav.push(btn("◀️ قبلی", `ul:${p - 1}`));
  if (p < pages - 1) nav.push(btn("بعدی ▶️", `ul:${p + 1}`));
  return { text: users.length ? `👥 کاربران (${users.length}) — صفحه‌ی ${p + 1} از ${pages}\n✅ فعال · ⛔ قطع · ⌛ منقضی؛ عدد: جست‌وجوی ۳۰ روز` : "هنوز حسابی نیست.",
    keyboard: [...rows, ...(nav.length ? [nav] : []), [btn("➕ کاربر جدید", "new")], BACK] };
}

async function userCard(env, name, note = "") {
  const u = await getUser(env, name);
  if (!u) return { text: `کاربر «${name}» نیست.`, keyboard: [[btn("👥 کاربران", "ul:0")], BACK] };
  const events = (await listLogs(env, ago(180))).filter((e) => e.user === name);
  const s = events.filter((e) => e.kind === "search" || e.kind === "unanswered");
  const last = events.at(-1);
  return {
    text: `${note ? note + "\n\n" : ""}👤 ${name}  ${state(u)} ${usable(u) ? "فعال" : u.active ? "منقضی" : "قطع"}\n` +
      `🎚 سطح دسترسی: ${ROLES[u.role || "full"].label}\n📈 سهمیه‌ی روزانه: ${u.quota ? `${u.quota} جست‌وجو` : "نامحدود"}\n` +
      `📅 ساخته‌شده: ${when(u.created)}\n⏳ اعتبار: ${u.expires ? `تا ${when(u.expires)}` : "بی‌پایان"}${u.note ? `\n📝 ${u.note}` : ""}\n\n` +
      `🔎 ${s.length} جست‌وجو (${s.filter((e) => e.kind === "unanswered").length} بی‌جواب) · 💬 ${events.filter((e) => e.kind === "feedback").length} بازخورد · 🔑 ${events.filter((e) => e.kind === "login").length} ورود\n` +
      `🕘 آخرین فعالیت: ${last ? when(last.time) : "—"}`,
    keyboard: [
      [btn("🕘 فعالیت‌ها", `ua:${name}`), btn("🔑 رمز تازه", `ur:${name}`)],
      [btn("🎚 سطح دسترسی", `uro:${name}`), btn("📈 سهمیه", `uq:${name}`)],
      [btn("⏳ تمدید", `ue:${name}`), u.active ? btn("⛔ قطع دسترسی", `uoff:${name}`) : btn("✅ وصل دوباره", `uon:${name}`)],
      [btn("🗑 حذف", `udel:${name}`)],
      [btn("👥 کاربران", "ul:0"), ...BACK],
    ],
  };
}

const roleKeyboard = (prefix, back) => [...Object.entries(ROLES).map(([k, r]) => [btn(r.label, `${prefix}:${k}`)]), [back]];
const ROLE_HELP = `کامل: همه‌چیز، با نمایش صفحه‌ی اصلی مقاله‌ها
مهمان (بدون PDF): جست‌وجو و همه‌ی ابزارها، بدون هیچ نشانی از PDF مقاله‌ها
فقط جست‌وجو: فقط جست‌وجوی مقاله‌ها (بدون PDF)
فقط ابزارها: ضریب شکست، تطبیق فاز و SPDC؛ بدون جست‌وجو`;

async function logScreen(env, title, filter, days, n = 25) {
  const events = (await listLogs(env, ago(days))).filter(filter).slice(-n);
  return { text: clip(`${title}\n\n${lines(events) || "چیزی نیست."}`), keyboard: [BACK] };
}

async function stats(env) {
  const logs = await listLogs(env, ago(7)), day = ago(1);
  const sum = (es) => {
    const s = es.filter((e) => e.kind === "search" || e.kind === "unanswered");
    return `${s.length} جست‌وجو · ${s.filter((e) => e.kind === "unanswered").length} بی‌جواب · ${es.filter((e) => e.kind === "feedback").length} بازخورد`;
  };
  const per = {};
  for (const e of logs) (per[e.user] ||= []).push(e);
  return { text: `📊 آمار\n\n۲۴ ساعت: ${sum(logs.filter((e) => e.time >= day))}\n۷ روز: ${sum(logs)}\n\nبه تفکیک کاربر (۷ روز):\n` +
    (Object.entries(per).sort((a, b) => b[1].length - a[1].length).map(([u, es]) => `• ${u}: ${sum(es)}`).join("\n") || "—"), keyboard: [BACK] };
}

async function online(env) {
  const logs = await listLogs(env, ago(1 / 24));
  const last = {};
  for (const e of logs) last[e.user] = e;
  const rows = Object.values(last).sort((a, b) => (a.time < b.time ? 1 : -1));
  return { text: `🟢 فعال در یک ساعت اخیر\n\n${rows.map((e) => `• ${e.user} — ${when(e.time)}${e.q ? ` · ${e.q}` : ""}`).join("\n") || "کسی نیست."}`,
    keyboard: [...rows.filter((e) => e.user !== "owner" && e.user !== "?").slice(0, 6).map((e) => [btn(`👤 ${e.user}`, `u:${e.user}`)]), [btn("🔄 تازه‌سازی", "online"), ...BACK]] };
}

const created = (name, password, days, role) =>
  `✅ حساب ساخته شد\n\nآدرس: ${SITE}\nنام کاربری: ${name}\nرمز: ${password}\nسطح دسترسی: ${ROLES[role].label}\n${days ? `اعتبار: ${days} روز` : "اعتبار: بی‌پایان"}\n\n(این پیام را می‌توانید مستقیم برای کاربر بفرستید)`;

// ---------- button presses
async function onButton(env, data) {
  const [k, a, b] = data.split(":");
  switch (k) {
    case "m": await setState(env, null); return home(env);
    case "ul": return userList(env, Number(a) || 0);
    case "u": return userCard(env, a);
    case "ua": return { ...(await logScreen(env, `🕘 فعالیت‌های ${a}`, (e) => e.user === a, 180, 30)), keyboard: [[btn(`👤 ${a}`, `u:${a}`)], BACK] };
    case "ur": { const { password } = await updateUser(env, a, { resetPassword: true }); return userCard(env, a, `🔑 رمز تازه‌ی ${a}: ${password}`); }
    case "uoff": await updateUser(env, a, { active: false }); return userCard(env, a, "⛔ دسترسی قطع شد؛ همین حالا از سایت بیرون است.");
    case "uon": await updateUser(env, a, { active: true }); return userCard(env, a, "✅ دوباره فعال شد.");
    case "uro": return { text: `🎚 سطح دسترسی ${a}\n\n${ROLE_HELP}`, keyboard: roleKeyboard(`urs:${a}`, btn("↩️ بازگشت", `u:${a}`)) };
    case "urs": await updateUser(env, a, { role: b }); return userCard(env, a, `🎚 سطح دسترسی: ${ROLES[b].label}`);
    case "uq": return { text: `📈 سهمیه‌ی روزانه‌ی جست‌وجوی ${a}`, keyboard: [[10, 30, 100].map((q) => btn(`${q} در روز`, `uqs:${a}:${q}`)), [btn("نامحدود", `uqs:${a}:0`)], [btn("↩️ بازگشت", `u:${a}`)]] };
    case "uqs": await updateUser(env, a, { quota: Number(b) }); return userCard(env, a, `📈 سهمیه: ${Number(b) ? `${b} در روز` : "نامحدود"}`);
    case "ue": return { text: `⏳ تمدید اعتبار ${a}`, keyboard: [[7, 30, 90].map((d) => btn(`+${d} روز`, `ues:${a}:${d}`)), [btn("بی‌پایان", `ues:${a}:0`)], [btn("↩️ بازگشت", `u:${a}`)]] };
    case "ues": {
      const { user } = await updateUser(env, a, Number(b) ? { extendDays: Number(b) } : { noExpiry: true });
      return userCard(env, a, `⏳ اعتبار: ${user.expires ? `تا ${when(user.expires)}` : "بی‌پایان"}`);
    }
    case "udel": return { text: `🗑 حساب ${a} حذف شود؟ (سابقه‌ی فعالیتش می‌ماند)`, keyboard: [[btn("بله، حذف کن", `udely:${a}`), btn("نه", `u:${a}`)]] };
    case "udely": await deleteUser(env, a); return { ...(await userList(env, 0)), text: `🗑 ${a} حذف شد.\n\n` + (await userList(env, 0)).text };
    case "new":
      await setState(env, { step: "name" });
      return { text: "➕ کاربر جدید\n\nنام کاربری را بفرستید (حروف کوچک انگلیسی، عدد، _ . - ؛ ۳ تا ۳۲ حرف).\nمی‌توانید بعد از نام یک یادداشت هم بنویسید، مثلاً:\nali دانشجوی دکتری گروه دکتر …", keyboard: [[btn("✖️ انصراف", "m")]] };
    case "nr": { const s = await getState(env); if (!s?.name) return home(env); await setState(env, { ...s, role: a, step: "days" });
      return { text: `➕ ${s.name} — ${ROLES[a].label}\n\nمدت اعتبار؟`, keyboard: [[7, 30, 90].map((d) => btn(`${d} روز`, `nd:${d}`)), [btn("بی‌پایان", "nd:0")], [btn("✖️ انصراف", "m")]] }; }
    case "nd": {
      const s = await getState(env); if (!s?.name || !s.role) return home(env);
      const password = await createUser(env, s.name, Number(a), s.note || "", s.role);
      await setState(env, null);
      return { text: created(s.name, password, Number(a), s.role), keyboard: [[btn(`👤 ${s.name}`, `u:${s.name}`), btn("➕ یکی دیگر", "new")], BACK] };
    }
    case "stats": return stats(env);
    case "online": return online(env);
    case "unans": return logScreen(env, "❓ آخرین سؤال‌های بی‌جواب", (e) => e.kind === "unanswered", 90);
    case "fb": return logScreen(env, "💬 آخرین بازخوردها", (e) => e.kind === "feedback", 90);
    case "act": return logScreen(env, "🕘 آخرین فعالیت‌ها", () => true, 30);
    case "fail": return logScreen(env, "🔑 ورودهای ناموفق", (e) => e.kind === "failedlogin", 30);
    case "maint": { const s = await getSettings(env); await setSettings(env, { maintenance: !s.maintenance }); return home(env); }
    case "banner": {
      const s = await getSettings(env);
      await setState(env, { step: "banner" });
      return { text: `📢 اعلان سایت\n\n${s.banner ? `اکنون: «${s.banner}»\n\n` : ""}متن اعلان را بفرستید؛ بالای سایت برای همه نشان داده می‌شود.`,
        keyboard: [...(s.banner ? [[btn("🗑 برداشتن اعلان", "bclr")]] : []), [btn("✖️ انصراف", "m")]] };
    }
    case "bclr": await setSettings(env, { banner: "" }); await setState(env, null); return home(env);
    default: return home(env);
  }
}

// ---------- free text: commands, or the answer the panel is waiting for
async function onText(env, text) {
  const cmd = text.trim().split(/\s+/)[0].toLowerCase().replace(/@\w+$/, "");
  if (["/amin", "/admin", "/start", "/panel", "/help", "/menu"].includes(cmd)) { await setState(env, null); return home(env); }
  const s = await getState(env);
  if (s?.step === "name") {
    const [name, ...note] = text.trim().split(/\s+/);
    const n = name.toLowerCase();
    if (!/^[a-z0-9][a-z0-9_.-]{2,31}$/.test(n) || n === "owner") return { text: "این نام قابل قبول نیست؛ دوباره بفرستید (حروف کوچک انگلیسی، عدد، _ . -).", keyboard: [[btn("✖️ انصراف", "m")]] };
    if (await getUser(env, n)) return { text: `«${n}» از قبل هست؛ نام دیگری بفرستید.`, keyboard: [[btn(`👤 ${n}`, `u:${n}`), btn("✖️ انصراف", "m")]] };
    await setState(env, { step: "role", name: n, note: note.join(" ") });
    return { text: `➕ ${n}${note.length ? ` (${note.join(" ")})` : ""}\n\nسطح دسترسی؟\n\n${ROLE_HELP}`, keyboard: roleKeyboard("nr", btn("✖️ انصراف", "m")) };
  }
  if (s?.step === "banner") {
    await setSettings(env, { banner: text.trim().slice(0, 300) });
    await setState(env, null);
    const h = await home(env);
    return { ...h, text: "📢 اعلان روی سایت گذاشته شد.\n\n" + h.text };
  }
  return { text: "برای باز کردن پنل /amin را بفرستید.", keyboard: [[btn("🔷 باز کردن پنل", "m")]] };
}

export async function telegramWebhook(request, env) {
  if (!env.TG_WEBHOOK_SECRET || request.headers.get("x-telegram-bot-api-secret-token") !== env.TG_WEBHOOK_SECRET) {
    return new Response("forbidden", { status: 403 });
  }
  const update = await request.json().catch(() => ({}));
  const owner = String(env.TELEGRAM_CHAT_ID);
  const cb = update.callback_query, msg = update.message;
  // Only the owner, in a private chat; anyone else is ignored without any answer.
  if (cb) {
    if (String(cb.from?.id) !== owner || cb.message?.chat?.type !== "private") return new Response("ok");
    let screen;
    try { screen = await onButton(env, cb.data || "m"); } catch (e) { screen = { text: `⚠️ ${e.message || e}`, keyboard: [BACK] }; }
    await tg(env, "answerCallbackQuery", { callback_query_id: cb.id });
    await tg(env, "editMessageText", { chat_id: cb.message.chat.id, message_id: cb.message.message_id, text: screen.text,
      reply_markup: { inline_keyboard: screen.keyboard }, disable_web_page_preview: true });
    return new Response("ok");
  }
  if (!msg?.text || String(msg.from?.id) !== owner || msg.chat?.type !== "private") return new Response("ok");
  let screen;
  try { screen = await onText(env, msg.text); } catch (e) { screen = { text: `⚠️ ${e.message || e}`, keyboard: [BACK] }; }
  await tg(env, "sendMessage", { chat_id: msg.chat.id, text: screen.text, reply_markup: { inline_keyboard: screen.keyboard }, disable_web_page_preview: true });
  return new Response("ok");
}
