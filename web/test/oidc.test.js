import test from "node:test";
import assert from "node:assert/strict";
import { verifyOidc } from "../src/oidc.js";

const enc = (o) => Buffer.from(JSON.stringify(o)).toString("base64url");
const { publicKey, privateKey } = await crypto.subtle.generateKey(
  { name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, true, ["sign", "verify"]);
const jwk = { ...(await crypto.subtle.exportKey("jwk", publicKey)), kid: "k1" };
const jwks = () => Promise.resolve(new Response(JSON.stringify({ keys: [jwk] })));
const now = 1_800_000_000;
async function token(claims, kid = "k1") {
  const body = `${enc({ alg: "RS256", kid })}.${enc(claims)}`;
  const sig = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", privateKey, new TextEncoder().encode(body));
  return `${body}.${Buffer.from(sig).toString("base64url")}`;
}
const good = { iss: "https://token.actions.githubusercontent.com", aud: "matrag", exp: now + 300, nbf: now - 10,
  repository: "aminsadidi/RAG", event_name: "workflow_dispatch",
  job_workflow_ref: "aminsadidi/RAG/.github/workflows/ocr.yml@refs/heads/claude/festive-bardeen-nnw123" };

test("only this repository's OCR workflow, with a valid signature, gets through", async () => {
  assert.ok(await verifyOidc(await token(good), now, jwks));
  for (const bad of [{ repository: "someone/RAG" }, { aud: "other" }, { exp: now - 1 },
    { job_workflow_ref: "aminsadidi/RAG/.github/workflows/evil.yml@refs/heads/x" }, { event_name: "pull_request" }]) {
    assert.equal(await verifyOidc(await token({ ...good, ...bad }), now, jwks), null, JSON.stringify(bad));
  }
  const forged = (await token(good)).replace(/\.[^.]+$/, `.${Buffer.from("x".repeat(256)).toString("base64url")}`);
  assert.equal(await verifyOidc(forged, now, jwks), null);
  assert.equal(await verifyOidc(await token(good, "other"), now, jwks), null);
  assert.equal(await verifyOidc("garbage", now, jwks), null);
  assert.equal(await verifyOidc("a.b.c", now, jwks), null);
});
