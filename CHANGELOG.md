# Changelog

## 1.0.0 (unreleased): first public release

Security
- Shared calculation links could run script in the page (raw box values in HTML); values are escaped, a number box
  accepts only a number from a link, and every HTML page has a nonce-based Content-Security-Policy, no framing,
  `Referrer-Policy: same-origin` and `nosniff`.
- CI keys: only workflows on `main` get keys, each only its own; the owner's password is never sent to CI.
  Sessions are signed with their own `SESSION_SECRET`.
- Removed the permanent owner cookie and the `?key=` login (password in the URL); owner password compared in
  constant time; logout is a POST.
- Quotas and failed-login counts survive the free plan's daily KV write limit (Durable Object), and a login fails
  closed when it cannot be counted.
- pdf.js runs with `isEvalSupported: false` (CVE-2024-4367); accounts without search get no collection lists;
  arXiv ids are validated; a shared Gradio app always asks for a login; workflows pin actions to commits and pass
  inputs through the environment.

Fixes
- Paper text with `$$`, `$&` or `$'` (LaTeX) no longer corrupts the AI file; citations are `(Source 2, p. 5)`.
- Highlighting no longer breaks HTML entities (`&lt;` for the word "LT"); crystal formulas of the question are
  highlighted too.
- Cached scope verdicts follow edits of the scope prompt; a failed similarity request or an incomplete SubQ answer
  no longer fails or poisons a search.
- `export-qdrant` keeps the enrichment fields (crystals, junk, basis_p, has), sends metadata-only fixes, and
  indexes `crystals`.
- The weekly quality run uses its own account and stays out of the log and Telegram.

Evaluation
- Frozen dev/test split of the gold questions, 95% bootstrap intervals, paired comparisons; refractive-index
  questions also accept papers with a hand-read dispersion formula for the material; "chunk MRR" and paper-level
  MRR@10 named apart.

Repository
- New README (Persian and English), CITATION.cff, this changelog; the HITRAN roadmap is archived; the event log
  moves to D1; the site's address is set in one place.
