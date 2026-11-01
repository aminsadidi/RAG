// Feedback from the site and questions it could not answer: kept in the D1 database LOGS (migrations/; in KV,
// log:<time>, while that binding is missing), 180 days, and sent to the owner's Telegram (bot TELEGRAM_TOKEN, chat TELEGRAM_CHAT_ID; both optional secrets), with a daily summary.
const DAY = 86400;
const clip = (s, n) => String(s ?? "").replace(/\s+/g, " ").trim().slice(0, n);

export async function telegram(env, text) {
  if (!env.TELEGRAM_TOKEN || !env.TELEGRAM_CHAT_ID) return false;
  const r = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/sendMessage`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text: text.slice(0, 4000), disable_web_page_preview: true }),
  }).catch((e) => ({ ok: false, statusText: String(e) }));
  if (!r.ok) console.log("telegram", r.status, r.statusText);
  return r.ok;
}

const KEEP_DAYS = 180;

// One event. In D1 a row (a KV listing of every log: key, which the admin panel and the daily summary read, grew to
// 180 days of keys and each event was a KV write); in KV log:<time>:<kind>:<user>:<random>, with the question in
// the metadata, so the admin bot reads a user's activity from one listing (no value reads).
export async function logEvent(env, kind, data, user = "?") {
  const time = new Date().toISOString(), q = clip(data.question || data.comment || "", 180), v = clip(data.verdict || "", 20);
  if (env.LOGS) {
    await env.LOGS.prepare("INSERT INTO logs (time, kind, user, q, v, data) VALUES (?, ?, ?, ?, ?, ?)")
      .bind(time, kind, String(user), q, v, JSON.stringify({ kind, user, ...data })).run().catch((e) => console.log("log insert", String(e)));
    return;
  }
  if (!env.AICACHE) return;
  const key = `log:${time}:${kind}:${user}:${crypto.randomUUID().slice(0, 8)}`;
  await env.AICACHE.put(key, JSON.stringify({ kind, user, ...data }), { expirationTtl: KEEP_DAYS * DAY,
    metadata: { q, v } }).catch((e) => console.log("log put", String(e)));
}

// Logged events since an ISO time, oldest first: {time, kind, user, q, v}; `user`: only that user's.
export async function listLogs(env, since = "", { user } = {}) {
  if (env.LOGS) {
    const { results } = await env.LOGS.prepare(`SELECT time, kind, user, q, v FROM logs WHERE time >= ?${user ? " AND user = ?" : ""} ORDER BY time, id`)
      .bind(...(user ? [since, user] : [since])).all();
    return results;
  }
  const out = [];
  let cursor;
  do {
    const page = await env.AICACHE.list({ prefix: "log:", cursor });
    for (const k of page.keys) {
      const m = /^log:(.+Z):([a-z]+):(?:([^:]+):)?[0-9a-f]{8}$/.exec(k.name);
      if (m && m[1] >= since && (!user || (m[3] || "?") === user)) out.push({ time: m[1], kind: m[2], user: m[3] || "?", q: k.metadata?.q || "", v: k.metadata?.v || "" });
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  return out;
}

const VERDICT = { useful: "👍 مفید بود", wrong: "👎 مرتبط نبود", found: "✅ جوابم را پیدا کردم", notfound: "❌ جوابم را پیدا نکردم", comment: "💬 نظر" };

// POST /api/feedback {verdict, question, searchQuery, comment, who, hit: {label, doc_id, node_id}, tab}
export async function feedback(env, body, user = "?") {
  const verdict = VERDICT[body.verdict] ? body.verdict : "comment";
  const item = { verdict, question: clip(body.question, 500), searchQuery: clip(body.searchQuery, 500), comment: clip(body.comment, 2000),
    who: clip(body.who, 80), tab: clip(body.tab, 30), hit: body.hit ? { label: clip(body.hit.label, 200), doc_id: clip(body.hit.doc_id, 120) } : undefined };
  if (verdict === "comment" && !item.comment) throw Object.assign(new Error("empty feedback"), { status: 400 });
  await logEvent(env, "feedback", item, user);
  await telegram(env, [`${VERDICT[verdict]} — MatRAG`, `کاربر: ${user}`, item.who && `نام داده‌شده: ${item.who}`, item.tab && item.tab !== "search" && `بخش: ${item.tab}`,
    item.question && `سؤال: ${item.question}`, item.hit && `منبع: ${item.hit.label}`, item.comment && `توضیح: ${item.comment}`].filter(Boolean).join("\n"));
  return { ok: true };
}

// A search the collection could not answer, sent right away.
export async function unanswered(env, found, user = "?") {
  await telegram(env, ["❓ سؤال بی‌جواب — MatRAG", `کاربر: ${user}`, `سؤال: ${clip(found.question, 500)}`,
    found.searchQuery && found.searchQuery !== found.question && `ترجمه: ${clip(found.searchQuery, 300)}`,
    found.relevance?.missingMaterials?.length && `ماده‌ی پیدا نشده: ${found.relevance.missingMaterials.join(", ")}`].filter(Boolean).join("\n"));
}

// The last day's searches and feedback, once a day (the worker's cron); in D1 the rows past 180 days go too.
export async function dailySummary(env) {
  if (!env.LOGS && !env.AICACHE) return;
  const since = new Date(Date.now() - DAY * 1000).toISOString();
  const counts = { search: 0, none: 0, feedback: 0 };
  const byKind = {};
  if (env.LOGS) {
    await env.LOGS.prepare("DELETE FROM logs WHERE time < ?").bind(new Date(Date.now() - KEEP_DAYS * DAY * 1000).toISOString()).run()
      .catch((e) => console.log("log cleanup", String(e)));
    const { results } = await env.LOGS.prepare("SELECT kind, COUNT(*) AS n FROM logs WHERE time >= ? GROUP BY kind").bind(since).all();
    for (const r of results) byKind[r.kind] = r.n;
  } else {
    for (const e of await listLogs(env, since)) byKind[e.kind] = (byKind[e.kind] || 0) + 1;
  }
  counts.search = (byKind.search || 0) + (byKind.unanswered || 0);
  counts.none = byKind.unanswered || 0;
  counts.feedback = byKind.feedback || 0;
  if (counts.search || counts.feedback) {
    await telegram(env, `📊 MatRAG در ۲۴ ساعت گذشته\nجست‌وجو: ${counts.search}\nبی‌جواب: ${counts.none}\nبازخورد: ${counts.feedback}`);
  }
}
