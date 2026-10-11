// The owner's admin panel, in Telegram: the bot's webhook (POST /tg/webhook). Telegram signs each call with the
// secret given to setWebhook (header X-Telegram-Bot-Api-Secret-Token = TG_WEBHOOK_SECRET); only private messages
// from the owner (TELEGRAM_CHAT_ID) are acted on, everyone else gets no answer at all.
import { createUser, deleteUser, getUser, listUsers, updateUser, usable } from "./accounts.js";
import { listLogs, telegram } from "./feedback.js";

const SITE = "https://matrag.ethanjamescarter1995.workers.dev";
const KIND = { search: "🔎", unanswered: "❓", feedback: "💬", login: "🔑", failedlogin: "🚫" };
const when = (t) => new Date(t).toLocaleString("fa-IR", { timeZone: "Asia/Tehran", dateStyle: "short", timeStyle: "short" });
const ago = (days) => new Date(Date.now() - days * 86400e3).toISOString();

const HELP = `پنل مدیریت MatRAG

حساب‌ها
/adduser نام [روز] [یادداشت] — حساب تازه با رمز تصادفی (روز: مدت اعتبار، خالی = بی‌پایان)
/users — همه‌ی حساب‌ها با وضعیت و آخرین فعالیت
/user نام — جزئیات و ۲۰ فعالیت آخر
/resetpass نام — رمز تازه
/disable نام — قطع دسترسی (همان لحظه خارج می‌شود)
/enable نام — وصل دوباره
/extend نام روز — تمدید اعتبار
/deluser نام — حذف حساب

پایش
/activity [تعداد] — آخرین فعالیت‌های همه (پیش‌فرض ۲۰)
/unanswered [تعداد] — آخرین سؤال‌های بی‌جواب
/feedback [تعداد] — آخرین بازخوردها
/stats — آمار ۲۴ ساعت و ۷ روز، به تفکیک کاربر`;

function lines(events) {
  return events.map((e) => `${KIND[e.kind] || "•"} ${when(e.time)} · ${e.user}${e.q ? ` · ${e.q}` : ""}${e.v && e.kind === "feedback" ? ` (${e.v})` : ""}`);
}

async function run(env, text) {
  const [cmdRaw, ...args] = text.trim().split(/\s+/);
  const cmd = cmdRaw.toLowerCase().replace(/@\w+$/, "");
  const name = (args[0] || "").toLowerCase();
  const n = (d) => Math.min(Math.max(parseInt(args[0], 10) || d, 1), 60);
  switch (cmd) {
    case "/start": case "/help": return HELP;
    case "/adduser": {
      const days = parseInt(args[1], 10) || 0;
      const note = args.slice(Number.isFinite(parseInt(args[1], 10)) ? 2 : 1).join(" ");
      const password = await createUser(env, name, days, note);
      return `✅ حساب ساخته شد\n\nآدرس: ${SITE}\nنام کاربری: ${name}\nرمز: ${password}\n${days ? `اعتبار: ${days} روز` : "اعتبار: بی‌پایان"}${note ? `\nیادداشت: ${note}` : ""}\n\n(این پیام را می‌توانید مستقیم برای کاربر بفرستید)`;
    }
    case "/resetpass": { const { password } = await updateUser(env, name, { resetPassword: true }); return `🔑 رمز تازه‌ی ${name}: ${password}`; }
    case "/disable": await updateUser(env, name, { active: false }); return `⛔ دسترسی ${name} قطع شد.`;
    case "/enable": await updateUser(env, name, { active: true }); return `✅ ${name} دوباره فعال شد.`;
    case "/extend": {
      const days = parseInt(args[1], 10);
      if (!days) return "مثال: /extend ali 30";
      const { user } = await updateUser(env, name, { extendDays: days });
      return `⏳ اعتبار ${name} تا ${when(user.expires)} تمدید شد.`;
    }
    case "/deluser": await deleteUser(env, name); return `🗑 حساب ${name} حذف شد (سابقه‌ی فعالیتش می‌ماند).`;
    case "/users": {
      const users = await listUsers(env);
      if (!users.length) return "هنوز حسابی نساخته‌اید. /adduser";
      const logs = await listLogs(env, ago(30));
      const last = {}, count = {};
      for (const e of logs) { last[e.user] = e.time; if (e.kind === "search" || e.kind === "unanswered") count[e.user] = (count[e.user] || 0) + 1; }
      return `👥 ${users.length} حساب (فعالیت ۳۰ روز اخیر)\n\n` + users.map((u) => {
        const state = !u.active ? "⛔" : u.expires && u.expires < Date.now() ? "⌛" : "✅";
        return `${state} ${u.name} — ${count[u.name] || 0} جست‌وجو · آخرین: ${last[u.name] ? when(last[u.name]) : "—"}` +
          `${u.expires ? ` · تا ${when(u.expires)}` : ""}${u.note ? ` · ${u.note}` : ""}`;
      }).join("\n");
    }
    case "/user": {
      const u = await getUser(env, name);
      if (!u) return `کاربر «${name}» نیست.`;
      const events = (await listLogs(env, ago(180))).filter((e) => e.user === name);
      const searches = events.filter((e) => e.kind === "search" || e.kind === "unanswered");
      return `👤 ${name} — ${usable(u) ? "فعال" : u.active ? "منقضی" : "غیرفعال"}\nساخته شده: ${when(u.created)}${u.expires ? `\nاعتبار تا: ${when(u.expires)}` : ""}${u.note ? `\nیادداشت: ${u.note}` : ""}\n` +
        `جست‌وجو: ${searches.length} (بی‌جواب: ${searches.filter((e) => e.kind === "unanswered").length}) · بازخورد: ${events.filter((e) => e.kind === "feedback").length} · ورود: ${events.filter((e) => e.kind === "login").length}\n\n` +
        (lines(events.slice(-20)).join("\n") || "هنوز فعالیتی ندارد.");
    }
    case "/activity": return lines((await listLogs(env, ago(30))).slice(-n(20))).join("\n") || "فعالیتی نیست.";
    case "/unanswered": return lines((await listLogs(env, ago(90))).filter((e) => e.kind === "unanswered").slice(-n(15))).join("\n") || "سؤال بی‌جوابی نیست.";
    case "/feedback": return lines((await listLogs(env, ago(90))).filter((e) => e.kind === "feedback").slice(-n(15))).join("\n") || "بازخوردی نیست.";
    case "/stats": {
      const logs = await listLogs(env, ago(7));
      const day = ago(1);
      const sum = (es) => {
        const s = es.filter((e) => e.kind === "search" || e.kind === "unanswered");
        return `${s.length} جست‌وجو، ${s.filter((e) => e.kind === "unanswered").length} بی‌جواب، ${es.filter((e) => e.kind === "feedback").length} بازخورد`;
      };
      const per = {};
      for (const e of logs) (per[e.user] ||= []).push(e);
      return `📊 ۲۴ ساعت: ${sum(logs.filter((e) => e.time >= day))}\n📊 ۷ روز: ${sum(logs)}\n\n` +
        Object.entries(per).sort((a, b) => b[1].length - a[1].length).map(([u, es]) => `• ${u}: ${sum(es)}`).join("\n");
    }
    default: return "دستور ناشناخته. /help";
  }
}

export async function telegramWebhook(request, env) {
  if (!env.TG_WEBHOOK_SECRET || request.headers.get("x-telegram-bot-api-secret-token") !== env.TG_WEBHOOK_SECRET) {
    return new Response("forbidden", { status: 403 });
  }
  const update = await request.json().catch(() => ({}));
  const msg = update.message;
  // Only the owner, in a private chat; anyone else is ignored without a reply.
  if (!msg?.text || String(msg.from?.id) !== String(env.TELEGRAM_CHAT_ID) || msg.chat?.type !== "private") return new Response("ok");
  let reply;
  try { reply = await run(env, msg.text); } catch (e) { reply = `⚠️ ${e.message || e}`; }
  await telegram(env, reply);
  return new Response("ok");
}
