import test from "node:test";
import assert from "node:assert/strict";
import { ciKeysFor, verifyOidc } from "../src/oidc.js";

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
  repository: "aminsadidi/RAG", event_name: "workflow_dispatch", ref: "refs/heads/main",
  job_workflow_ref: "aminsadidi/RAG/.github/workflows/ocr.yml@refs/heads/main" };

test("only this repository's OCR and quality workflows, with a valid signature, get through", async () => {
  assert.ok(await verifyOidc(await token(good), now, jwks));
  for (const bad of [{ repository: "someone/RAG" }, { aud: "other" }, { exp: now - 1 },
    { job_workflow_ref: "aminsadidi/RAG/.github/workflows/evil.yml@refs/heads/main" }, { event_name: "pull_request" },
    // any other branch: a workflow edited there would run with the keys
    { ref: "refs/heads/feature", job_workflow_ref: "aminsadidi/RAG/.github/workflows/ocr.yml@refs/heads/feature" },
    { ref: "refs/heads/feature" }, { job_workflow_ref: "aminsadidi/RAG/.github/workflows/ocr.yml@refs/heads/feature" },
    { job_workflow_ref: "aminsadidi/RAG/.github/workflows/ocr.yml@refs/heads/main-evil" },
    { job_workflow_ref: "someone/RAG/.github/workflows/ocr.yml@refs/heads/main" },
    { job_workflow_ref: "aminsadidi/RAG/.github/workflows/sub/ocr.yml@refs/heads/main" }]) {
    assert.equal(await verifyOidc(await token({ ...good, ...bad }), now, jwks), null, JSON.stringify(bad));
  }
  const forged = (await token(good)).replace(/\.[^.]+$/, `.${Buffer.from("x".repeat(256)).toString("base64url")}`);
  assert.equal(await verifyOidc(forged, now, jwks), null);
  assert.equal(await verifyOidc(await token(good, "other"), now, jwks), null);
  assert.equal(await verifyOidc("garbage", now, jwks), null);
  assert.equal(await verifyOidc("a.b.c", now, jwks), null);
});

test("the branch can be set (CI_REF) and the claims name the workflow", async () => {
  const dev = { ...good, ref: "refs/heads/dev", job_workflow_ref: "aminsadidi/RAG/.github/workflows/quality.yml@refs/heads/dev" };
  assert.equal(await verifyOidc(await token(dev), now, jwks), null);
  assert.equal((await verifyOidc(await token(dev), now, jwks, "refs/heads/dev")).workflow, "quality.yml");
});

test("each workflow gets only its own keys, never the owner's password", async () => {
  const env = { SITE_PASSWORD: "owner-secret", SESSION_SECRET: "sess", CI_USER: "ci-bot", CI_PASSWORD: "ci-pw",
    QDRANT_URL: "https://q", QDRANT_API_KEY: "qk", SUBQ_KEYS: "s1,s2" };
  const keys = async (w) => ciKeysFor({ workflow: w }, env);
  assert.deepEqual(Object.keys(await keys("quality.yml")).sort(), ["SITE_PASS", "SITE_USER", "SUBQ_KEYS"]);
  assert.deepEqual(Object.keys(await keys("datamap.yml")).sort(), ["QDRANT_API_KEY", "QDRANT_URL", "SUBQ_KEYS"]);
  assert.deepEqual(Object.keys(await keys("enrich.yml")).sort(), ["QDRANT_API_KEY", "QDRANT_URL", "SUBQ_KEYS"]);
  const ocr = await keys("ocr.yml");
  assert.deepEqual(Object.keys(ocr).sort(), ["ARTIFACT_KEY", "QDRANT_API_KEY", "QDRANT_URL", "SITE_PASS", "SITE_USER"]);
  assert.equal(ocr.SITE_USER, "ci-bot"); assert.match(ocr.ARTIFACT_KEY, /^[0-9a-f]{64}$/);
  for (const w of ["ocr.yml", "quality.yml", "datamap.yml", "enrich.yml"]) {
    const values = Object.values(await keys(w));
    assert.ok(!values.includes("owner-secret") && !values.includes("sess"), w);
  }
  assert.deepEqual(await keys("evil.yml"), {});
});
