// Counters with a limit (daily search quotas, failed logins), in one SQLite-backed Durable Object (available on
// the free Workers plan). KV allows 1000 writes a day on the free plan: when they ran out, every counter in KV
// silently stopped counting, and quotas and the login throttle let everything through.
//   POST /take {key, limit, ttl}: counts one if the count is below the limit -> {ok, n}
//   POST /add  {key, ttl}: counts one -> {n}
//   POST /get  {key} -> {n}
//   POST /give {key}: takes one back (a search that failed on the server) -> {n}
// A count lives `ttl` seconds from its first event (a fixed window), then starts again from 0.
export class Counters {
  constructor(state) {
    this.sql = state.storage.sql;
    this.sql.exec("CREATE TABLE IF NOT EXISTS counts (key TEXT PRIMARY KEY, n INTEGER NOT NULL, expires INTEGER NOT NULL)");
    this.sql.exec("CREATE INDEX IF NOT EXISTS counts_expires ON counts (expires)");
    this.calls = 0;
  }

  current(key, now) {
    const row = this.sql.exec("SELECT n, expires FROM counts WHERE key = ?", key).toArray()[0];
    return row && row.expires > now ? row : null;
  }

  async fetch(request) {
    const { key, limit, ttl } = await request.json().catch(() => ({}));
    if (typeof key !== "string" || !key || key.length > 512) return Response.json({ error: "bad key" }, { status: 400 });
    const now = Math.floor(Date.now() / 1000), op = new URL(request.url).pathname;
    // expired counts of other keys go now and then (each key's own is replaced when it counts again)
    if (++this.calls % 200 === 1) this.sql.exec("DELETE FROM counts WHERE expires <= ?", now);
    const row = this.current(key, now);
    if (op === "/get") return Response.json({ n: row?.n ?? 0 });
    if (op === "/give") {
      if (!row || row.n <= 0) return Response.json({ n: 0 });
      this.sql.exec("UPDATE counts SET n = ? WHERE key = ?", row.n - 1, key);
      return Response.json({ n: row.n - 1 });
    }
    const life = Math.max(1, Math.min(Number(ttl) || 86400, 7 * 86400));
    if (op === "/take" && row && row.n >= Number(limit)) return Response.json({ ok: false, n: row.n });
    if (op !== "/take" && op !== "/add") return Response.json({ error: "unknown" }, { status: 404 });
    const n = (row?.n ?? 0) + 1;
    this.sql.exec("INSERT OR REPLACE INTO counts (key, n, expires) VALUES (?, ?, ?)", key, n, row ? row.expires : now + life);
    return Response.json({ ok: true, n });
  }
}

// A call to the counters; throws when they cannot be reached (the caller decides: fail open or closed).
export async function counter(env, op, body) {
  const stub = env.COUNTERS.get(env.COUNTERS.idFromName("counters"));
  const r = await stub.fetch(`https://counters/${op}`, { method: "POST", body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`counters ${r.status}`);
  return r.json();
}
