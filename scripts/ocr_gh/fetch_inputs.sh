#!/usr/bin/env bash
# PDFs that are not on the site (over its 25 MB limit) come encrypted as assets of the draft release
# "ocr-inputs" (drafts are visible to the repository's owner only): <doc_id>.pdf.enc -> inputs/<doc_id>.pdf
set -euo pipefail
mkdir -p inputs
release=$(gh api "repos/$GITHUB_REPOSITORY/releases" --jq '.[] | select(.name == "ocr-inputs") | .id' | head -1)
[ -z "$release" ] && { echo "no extra PDFs"; exit 0; }
gh api "repos/$GITHUB_REPOSITORY/releases/$release/assets" --jq '.[] | "\(.id) \(.name)"' | while read -r id name; do
  gh api -H "Accept: application/octet-stream" "repos/$GITHUB_REPOSITORY/releases/assets/$id" > "inputs/$name"
  openssl enc -d -aes-256-cbc -pbkdf2 -pass env:ARTIFACT_KEY -in "inputs/$name" -out "inputs/${name%.enc}"
  rm "inputs/$name"
  echo "extra PDF: ${name%.enc}"
done
