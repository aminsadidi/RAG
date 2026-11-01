// The Worker's own routes (src/index.js), driven in Node with fake bindings (support/worker.js).
import { test } from "node:test";
import assert from "node:assert/strict";
import { call, cookieOf, env, form } from "./support/worker.js";
import { createUser } from "../src/accounts.js";

const withCookie = (c, init = {}) => ({ ...init, headers: { ...(init.headers || {}), cookie: `session=${c}` } });

test("login: the owner and users by the form; a session cookie, signed, is the only way in", async () => {
  const e = env();
  const owner = await call(e, "/login", form({ username: "", password: "owner-pass" }));
  assert.equal(owner.status, 303);
  assert.equal((await (await call(e, "/api/me", withCookie(cookieOf(owner)))).json()).role, "owner");
  const pw = await createUser(e, "sara", 0, "");
  const user = await call(e, "/login", form({ username: "sara", password: pw }));
  assert.equal((await (await call(e, "/api/me", withCookie(cookieOf(user)))).json()).user, "sara");
  assert.equal((await call(e, "/login", form({ username: "owner", password: "wrong" }))).status, 401);
});

test("no login by ?key= (a password in a URL), and the old static owner cookie no longer works", async () => {
  const e = env();
  const r = await call(e, "/?key=owner-pass");
  assert.equal(r.status, 200); assert.equal(r.headers.get("set-cookie"), null);
  assert.match(await r.text(), /type="password"/);  // the login page
  const { createHash } = await import("node:crypto");
  const old = createHash("sha256").update("matrag-session:owner-pass").digest("hex");
  assert.equal((await call(e, "/api/me", withCookie(old))).status, 401);
});
