#!/usr/bin/env bash
# The keys, from the site, for this repository's CI workflows only: the runner shows GitHub's signed OIDC token
# (web/src/oidc.js checks it, and the branch: only the default branch's workflows get keys). Each workflow gets
# only the keys it needs (CI_WORKFLOWS in oidc.js). Each value is masked in the log before it is set.
set -euo pipefail
oidc=$(curl -sSf -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=matrag" | jq -r .value)
keys=$(curl -sSf -X POST -H "Authorization: Bearer $oidc" "${SITE_URL:-https://matrag.ethanjamescarter1995.workers.dev}/ci/keys")
for k in $(jq -r 'keys[]' <<<"$keys"); do
  [[ "$k" =~ ^[A-Z_]+$ ]] || continue
  v=$(jq -r --arg k "$k" '.[$k]' <<<"$keys")
  [ -n "$v" ] && echo "::add-mask::$v"
  echo "$k=$v" >> "$GITHUB_ENV"
done
echo "keys set: $(jq -r 'keys | join(" ")' <<<"$keys")"
