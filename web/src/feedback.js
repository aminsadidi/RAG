// Feedback from the site and questions it could not answer: kept in KV (log:<time>, 180 days) and sent to the
// owner's Telegram (bot TELEGRAM_TOKEN, chat TELEGRAM_CHAT_ID; both optional secrets), with a daily summary.
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

export async function logEvent(env, kind, data) {
  if (!env.AICACHE) return;
  const key = `log:${new Date().toISOString()}:${kind}:${crypto.randomUUID().slice(0, 8)}`;
  await env.AICACHE.put(key, JSON.stringify({ kind, ...data }), { expirationTtl: 180 * DAY }).catch((e) => console.log("log put", String(e)));
}

const VERDICT = { useful: "👍 مفید بود", wrong: "👎 مرتبط نبود", found: "✅ جوابم را پیدا کردم", notfound: "❌ جوابم را پیدا نکردم", comment: "💬 نظر" };

// POST /api/feedback {verdict, question, searchQuery, comment, who, hit: {label, doc_id, node_id}, tab}
export async function feedback(env, body) {
  const verdict = VERDICT[body.verdict] ? body.verdict : "comment";
  const item = { verdict, question: clip(body.question, 500), searchQuery: clip(body.searchQuery, 500), comment: clip(body.comment, 2000),
    who: clip(body.who, 80), tab: clip(body.tab, 30), hit: body.hit ? { label: clip(body.hit.label, 200), doc_id: clip(body.hit.doc_id, 120) } : undefined };
  if (verdict === "comment" && !item.comment) throw Object.assign(new Error("empty feedback"), { status: 400 });
  await logEvent(env, "feedback", item);
  await telegram(env, [`${VERDICT[verdict]} — MatRAG`, item.who && `از: ${item.who}`, item.tab && item.tab !== "search" && `بخش: ${item.tab}`,
    item.question && `سؤال: ${item.question}`, item.hit && `منبع: ${item.hit.label}`, item.comment && `توضیح: ${item.comment}`].filter(Boolean).join("\n"));
  return { ok: true };
}

// A search the collection could not answer, sent right away.
export async function unanswered(env, found) {
  await telegram(env, ["❓ سؤال بی‌جواب — MatRAG", `سؤال: ${clip(found.question, 500)}`,
    found.searchQuery && found.searchQuery !== found.question && `ترجمه: ${clip(found.searchQuery, 300)}`,
    found.relevance?.missingMaterials?.length && `ماده‌ی پیدا نشده: ${found.relevance.missingMaterials.join(", ")}`].filter(Boolean).join("\n"));
}

// The last day's searches and feedback, once a day (the worker's cron).
export async function dailySummary(env) {
  if (!env.AICACHE) return;
  const since = new Date(Date.now() - DAY * 1000).toISOString();
  const counts = { search: 0, none: 0, feedback: 0 };
  let cursor;
  do {
    const page = await env.AICACHE.list({ prefix: "log:", cursor });
    for (const k of page.keys) {
      const [, time, kind] = k.name.match(/^log:(.+Z):([a-z]+):/) || [];
      if (!time || time < since) continue;
      if (kind === "search") counts.search += 1;
      if (kind === "unanswered") { counts.search += 1; counts.none += 1; }
      if (kind === "feedback") counts.feedback += 1;
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  if (counts.search || counts.feedback) {
    await telegram(env, `📊 MatRAG در ۲۴ ساعت گذشته\nجست‌وجو: ${counts.search}\nبی‌جواب: ${counts.none}\nبازخورد: ${counts.feedback}`);
  }
}
