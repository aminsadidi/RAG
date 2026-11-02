// GitHub Actions OIDC tokens: which repository, workflow and branch a runner runs (for the CI workflows' keys).
const OIDC_ISSUER = "https://token.actions.githubusercontent.com";
const CI_REPO = "aminsadidi/RAG";
// Only the default branch's workflows get keys: a workflow file edited on any other branch (or in a fork's PR)
// would otherwise run with them. The branch can be overridden with the Worker variable CI_REF.
export const CI_REF = "refs/heads/main";
// The keys each workflow needs, and no more (index.js ciKeys). SITE_USER/SITE_PASS: the dedicated CI account
// (a normal user account, never the owner's password), for the workflows that use the site itself.
export const CI_WORKFLOWS = {
  "ocr.yml": ["SITE_USER", "SITE_PASS", "QDRANT_URL", "QDRANT_API_KEY", "ARTIFACT_KEY"],
  "quality.yml": ["SITE_USER", "SITE_PASS", "SUBQ_KEYS"],
  "datamap.yml": ["QDRANT_URL", "QDRANT_API_KEY", "SUBQ_KEYS"],
  "enrich.yml": ["QDRANT_URL", "QDRANT_API_KEY", "SUBQ_KEYS"],
};
const b64url = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(s.length / 4) * 4, "=")),
  (c) => c.charCodeAt(0));

// The token's claims with `workflow` (the file name, a key of CI_WORKFLOWS), or null.
export async function verifyOidc(token, now = Date.now() / 1000, fetchJwks = () => fetch(`${OIDC_ISSUER}/.well-known/jwks`), ref = CI_REF) {
  try {
    return await check(token, now, fetchJwks, ref);
  } catch {
    return null;  // a malformed token
  }
}

async function check(token, now, fetchJwks, ref) {
  const [h, p, sig] = (token || "").split(".");
  if (!sig) return null;
  const header = JSON.parse(new TextDecoder().decode(b64url(h)));
  const claims = JSON.parse(new TextDecoder().decode(b64url(p)));
  const jwk = ((await (await fetchJwks()).json()).keys || []).find((k) => k.kid === header.kid);
  if (!jwk || header.alg !== "RS256") return null;
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64url(sig), new TextEncoder().encode(`${h}.${p}`));
  // the workflow file and the branch it was read from: <repo>/.github/workflows/<file>@<ref>, exactly
  const m = /^([^@]+)\/\.github\/workflows\/([^/@]+)@(.+)$/.exec(String(claims.job_workflow_ref || ""));
  const valid = ok && claims.iss === OIDC_ISSUER && claims.aud === "matrag" && claims.exp > now && claims.nbf <= now + 60
    && claims.repository === CI_REPO && claims.ref === ref && Boolean(m) && m[1] === CI_REPO && m[3] === ref
    && Object.hasOwn(CI_WORKFLOWS, m[2])
    && claims.event_name !== "pull_request" && claims.event_name !== "pull_request_target";
  return valid ? { ...claims, workflow: m[2] } : null;
}

// The keys a verified workflow gets: only those CI_WORKFLOWS lists for it. ARTIFACT_KEY (the OCR workflow's
// encryption of paper text between its jobs) is derived from the Qdrant key, so it is not stored anywhere.
export async function ciKeysFor(claims, env) {
  const all = { SITE_USER: env.CI_USER || "", SITE_PASS: env.CI_PASSWORD || "", QDRANT_URL: env.QDRANT_URL,
    QDRANT_API_KEY: env.QDRANT_API_KEY, SUBQ_KEYS: env.SUBQ_KEYS || "" };
  const out = {};
  for (const k of CI_WORKFLOWS[claims.workflow] || []) {
    if (k === "ARTIFACT_KEY") {
      const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`ocr-artifacts:${env.QDRANT_API_KEY}`));
      out[k] = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
    } else out[k] = all[k];
  }
  return out;
}
