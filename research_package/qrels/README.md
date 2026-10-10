# MatRAG Optics Qrels Evaluation Package (`gemini/drafts`)

This directory contains the ground truth relevance judgments (`qrels.csv`) for Information Retrieval (IR) and Retrieval-Augmented Generation (RAG) evaluation on the MatRAG optics collection.

## 1. Scope and Dataset Source

- **Questions:** All 402 questions from `data/rag-optics/gold/questions.csv` whose `id` starts with `ri-` (`ri-Ag-1` through `ri-ZrO2-3`), spanning all 134 distinct optical materials and crystals.
- **Corpus:** The complete collection in `web/src/papers.json` (2,612 papers with bibliographic metadata and full references).
- **Generator Script:** `build_qrels.py` (fully reproducible and verified).

---

## 2. Grading Rubric

Each candidate document evaluated for a question is assigned a grade in `[0, 1, 2]` based strictly on its title and metadata in `web/src/papers.json` (no guessing from memory):

- **Grade 2 (Highly Relevant / Exact Answer):**
  The paper gives the requested quantity (dispersion formula, Sellmeier equation, or measured refractive index values across wavelengths) for that exact material.
- **Grade 1 (Partially Relevant / Related Data):**
  The paper investigates the exact same material, but reports related optical or physical data (such as second-harmonic generation $d_{ij}$, phase-matching angles, optical parametric oscillation, crystal growth, Raman spectra, or laser damage thresholds) rather than the linear refractive index dispersion formula/values.
- **Grade 0 (Not Relevant):**
  The paper is not relevant to the question or material (e.g. belongs to a shared cluster or keyword match but covers a different compound, or is a cited general reference that does not provide specific dispersion data for the target crystal).

---

## 3. Columns Specification

`qrels.csv` adheres to the schema:
```csv
id,doc_id,grade,reason
```

- `id`: The question identifier from `questions.csv` (e.g., `ri-Ag-1`, `ri-GaAs-2`, `ri-ZrO2-3`).
- `doc_id`: The document identifier matching `web/src/papers.json`.
- `grade`: Numerical relevance judgment (`2`, `1`, or `0`).
- `reason`: Justification strictly derived from the paper title (length $\le 15$ words).

---

## 4. Benchmark Statistics

- **Total Judged Pairs:** 10,140 rows
- **Evaluated Questions:** 402 (134 unique materials)
- **Unique Documents Judged:** 1,943 papers
- **Max Words in Reason:** 11 words (all strictly $\le 15$ words; min 5 words)
- **Grade Distribution:**
  - **Grade 2:** 1,755 rows (17.3%)
  - **Grade 1:** 3,597 rows (35.5%)
  - **Grade 0:** 4,788 rows (47.2%)
