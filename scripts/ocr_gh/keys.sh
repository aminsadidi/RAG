#!/usr/bin/env bash
# The keys, from the site, for this repository's OCR workflow only: the runner shows GitHub's signed OIDC
# token (web/src/oidc.js checks it). Each value is masked in the log before it is set.
set -euo pipefail
oidc=$(curl -sSf -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=matrag" | jq -r .value)
keys=$(curl -sSf -X POST -H "Authorization: Bearer $oidc" "${SITE_URL:-https://matrag.ethanjamescarter1995.workers.dev}/ci/keys")
for k in ${KEYS:-SITE_KEY QDRANT_URL QDRANT_API_KEY ARTIFACT_KEY}; do
  v=$(jq -r --arg k "$k" '.[$k]' <<<"$keys")
  echo "::add-mask::$v"
  echo "$k=$v" >> "$GITHUB_ENV"
done
echo "keys set"
