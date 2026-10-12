// GitHub Actions OIDC tokens: which repository and workflow a runner runs (for the OCR workflow's keys).
const OIDC_ISSUER = "https://token.actions.githubusercontent.com";
const CI_REPO = "aminsadidi/RAG", CI_WORKFLOW = `${CI_REPO}/.github/workflows/ocr.yml@`;
const b64url = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(s.length / 4) * 4, "=")),
  (c) => c.charCodeAt(0));

export async function verifyOidc(token, now = Date.now() / 1000, fetchJwks = () => fetch(`${OIDC_ISSUER}/.well-known/jwks`)) {
  try {
    return await check(token, now, fetchJwks);
  } catch {
    return null;  // a malformed token
  }
}

async function check(token, now, fetchJwks) {
  const [h, p, sig] = (token || "").split(".");
  if (!sig) return null;
  const header = JSON.parse(new TextDecoder().decode(b64url(h)));
  const claims = JSON.parse(new TextDecoder().decode(b64url(p)));
  const jwk = ((await (await fetchJwks()).json()).keys || []).find((k) => k.kid === header.kid);
  if (!jwk || header.alg !== "RS256") return null;
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64url(sig), new TextEncoder().encode(`${h}.${p}`));
  const valid = ok && claims.iss === OIDC_ISSUER && claims.aud === "matrag" && claims.exp > now && claims.nbf <= now + 60
    && claims.repository === CI_REPO && (claims.job_workflow_ref || "").startsWith(CI_WORKFLOW)
    && claims.event_name !== "pull_request" && claims.event_name !== "pull_request_target";
  return valid ? claims : null;
}

