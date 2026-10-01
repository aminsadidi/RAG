# OCR of scanned papers (site, October 2026)

Run once from a folder holding `targets.json`, `scanned.json`, the PDFs under `root/` (downloaded
from the site) and `master.jsonl` (the master index); QDRANT_URL / QDRANT_API_KEY set.

1. **Targets** (102): full-text papers with no text (9), almost no text (<3000 characters, 14) or garbled
   text (stop-word ratio < 0.12, 6), plus the 73 papers behind refractiveindex.info's formulas.
   A PDF counts as scanned when a single image covers most of its first pages; the 33 born-digital
   benchmark papers keep their exact embedded text. 61 papers were OCR'd (the 9 without text were
   not on the site and are left for Colab).
2. `run_ocr.py i n` — Docling with RapidOCR on every page image (`MATRAG_FORCE_OCR=true`).
3. `replace.py` — re-chunks with the pipeline's chunker and embedding model and replaces a paper's
   points when its text is better: more text or more stop words (readable prose), or (`force.json`)
   when it keeps every decimal number of the old text (`numbers.json`). 45 papers replaced
   (`report.json`); their points carry `ocr: true`.
4. `fix_wrong.py` — 6 PDFs held another paper (title words absent from the first pages,
   `title_match.json`, checked by hand); their full text was removed and the paper indexed from its
   master-index abstract (`pdf_mismatch: true`). The PDFs on Drive are untouched.

Effect on the site's retrieval (86 questions, MRR): hybrid 0.254 → 0.292, BM25 0.290 → 0.307,
vector 0.133 → 0.147; hybrid recall@10 0.349 → 0.419.
