// The event log in D1 (src/feedback.js): what the admin panel and the daily summary read.
import { test } from "node:test";
import assert from "node:assert/strict";
import { fakeD1, kv } from "./support/worker.js";
import { dailySummary, listLogs, logEvent } from "../src/feedback.js";

test("events go to D1 (no KV write) and are listed oldest first, by user", async () => {
  const e = { LOGS: await fakeD1(), AICACHE: kv() };
  await logEvent(e, "search", { question: "LBO Sellmeier", verdict: "ok" }, "sara");
  await logEvent(e, "unanswered", { question: "x".repeat(400), verdict: "none" }, "ali");
  await logEvent(e, "feedback", { comment: "great" }, "sara");
  assert.equal(e.AICACHE.puts, 0);
  const all = await listLogs(e, "");
  assert.deepEqual(all.map((r) => [r.kind, r.user]), [["search", "sara"], ["unanswered", "ali"], ["feedback", "sara"]]);
  assert.equal(all[1].q.length, 180);
  assert.deepEqual((await listLogs(e, "", { user: "sara" })).map((r) => r.q), ["LBO Sellmeier", "great"]);
  assert.deepEqual(await listLogs(e, "2999-01-01"), []);
});

test("the daily summary counts the last day and drops rows past 180 days", async () => {
  const e = { LOGS: await fakeD1(), TELEGRAM_TOKEN: "t", TELEGRAM_CHAT_ID: "1" };
  const old = new Date(Date.now() - 200 * 86400e3).toISOString();
  e.LOGS.db.prepare("INSERT INTO logs (time, kind, user) VALUES (?, 'search', 'x')").run(old);
  await logEvent(e, "search", { question: "a" }, "u");
  await logEvent(e, "unanswered", { question: "b" }, "u");
  await logEvent(e, "feedback", { comment: "c" }, "u");
  const sent = [];
  const real = globalThis.fetch;
  globalThis.fetch = async (u, init) => { sent.push(JSON.parse(init.body).text); return new Response("{}"); };
  try { await dailySummary(e); } finally { globalThis.fetch = real; }
  assert.match(sent[0], /جست‌وجو: 2\nبی‌جواب: 1\nبازخورد: 1/);
  assert.equal(e.LOGS.db.prepare("SELECT COUNT(*) AS n FROM logs").get().n, 3);
});

test("without D1 the log stays in KV, as before", async () => {
  const e = { AICACHE: kv() };
  await logEvent(e, "search", { question: "q1" }, "sara");
  await logEvent(e, "search", { question: "q2" }, "ali");
  assert.deepEqual((await listLogs(e, "", { user: "ali" })).map((r) => r.q), ["q2"]);
});
