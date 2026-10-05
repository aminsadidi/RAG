# Commercial version: notes for later

The owner decided (2026-10-05) to finish and polish the research tool first. When commercialization
starts, remind them of this file and start from it.

## The idea (owner's)
- Freemium: sign in with an email, some parts free; pay for special exports (Lumerical, and also
  Zemax AGF, COMSOL, CSV), API access and licences.
- Partnership with crystal makers: "request a quote" from the crystal page, commission or paid leads.

## Points already discussed
- Copyright: the public version must not show the papers' text or PDFs (they belong to the publishers;
  their text-mining licences usually forbid commercial use). Show title, DOI, extracted values and
  formulas with a link to the publisher. The page view with the yellow box stays private.
- What is worth selling: the checked data (d tensors in the right frame, thermo-optic formulas, formulas
  missing from refractiveindex.info, each tested against its paper), the calculators (phase matching,
  temperature, QPM, GVD) and the exports; also the RAG pipeline for companies' own documents.
- Free competitors: refractiveindex.info (CC0), SNLO (free, A. V. Smith), RP Photonics software.
- Targets before launch: retrieval MRR ~0.6-0.7 and recall@5 ~80 % (2026-10-05: MRR 0.35, recall@5
  0.42 on the 493 curated questions); data must be essentially error free; coverage ~100 crystals with
  d, ~20 with dn/dT (2026-10-05: 30 and 5).
- Quick accuracy win: a reranker (Workers AI has bge-reranker), then fine-tuning the embeddings on the
  generated questions.
- Infrastructure is enough technically (Cloudflare Workers paid ~$5/month, D1/KV for accounts, an email
  service; Qdrant free tier holds the current 57k chunks).
- Non-technical blockers: sanctions (Stripe/Paddle unavailable; Cloudflare/Qdrant accounts at risk for
  commercial use from Iran): domestic gateway (e.g. Zarinpal), a partner abroad, or revenue paid by the
  crystal makers. University IP rules for thesis work.
- Rough plan: month 1 accuracy (reranker, eval loop); month 2 public version without paper text, email
  sign-in, Lumerical/Zemax export; month 3 more checked data and talks with 5-10 crystal makers;
  month 4 trial with a few labs, then pricing.
- Feature asked for: a "crystal page": one view with all papers, refractive index formulas, d tensor and
  thermo-optic data of a crystal.
