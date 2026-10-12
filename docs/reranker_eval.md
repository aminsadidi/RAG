# Reranker evaluation (2026-10-10)

Question: does a second-stage reranker improve the site search (hybrid dense + BM25, RRF in Qdrant)?

Set: 200 questions drawn at random (seed 0) from `data/rag-optics/gold/questions.csv` and
`generated.csv`, English text, against the live site. A hit is the gold paper (`doc_id`) in the top 10.

## bge-reranker-base (Workers AI), top-30 pool reranked

| | R@1 | R@3 | R@5 | R@10 | MRR@10 | median latency |
|---|---|---|---|---|---|---|
| hybrid (no rerank) | 0.405 | 0.460 | 0.480 | 0.520 | **0.439** | 0.48 s |
| + bge-reranker | 0.360 | 0.420 | 0.445 | 0.510 | 0.401 | 1.14 s |

By group (MRR@10): `ri` 110 questions 0.197 → 0.144; `gen` 76 questions 0.821 → 0.819; others (14) 0.271 → 0.155.

Fusions tried offline on the same pools (RRF of the hybrid rank and the reranker rank with k = 5…60,
hybrid weighted ×2/×3, reranking only the top 10/15/20): best 0.438, none above the hybrid order.

## Clef-flash (Workers AI), top-10 pool, 40 questions

One request per question: the passages in `state`, one `noul` question per passage
("does passage pN come from a paper that answers the search question?").

| | R@1 | R@3 | R@5 | MRR@10 | median latency |
|---|---|---|---|---|---|
| hybrid | 0.425 | 0.550 | 0.550 | **0.483** | — |
| bge-reranker | 0.300 | 0.500 | 0.525 | 0.399 | 0.5 s |
| Clef-flash | 0.425 | 0.450 | 0.475 | 0.447 | 1.1 s |

## Reading

- Neither reranker beats the hybrid order on this set, so reranking is **off by default**
  (a checkbox on the search page turns it on; `rerank: true` in the API).
- The gold set counts one paper per question. Most of the loss is in the `ri` questions
  ("refractive index of X"), where the gold is the refractiveindex.info source and several other
  papers in the collection answer the question as well. In the YVO4 case the reranker put Zelmon 2010 and
  Zeng 1990 (both refractive-index measurements of YVO4) above the gold Lomheim 1978, whose matched passage
  was a cover page. So the metric undercounts the reranker; a set with graded relevance
  (all papers that answer a question) is needed before a final verdict.
- On the questions written from one passage (`gen`), where a single gold is fair, the rerankers tie with hybrid.
- Cost is not the issue: bge-reranker is about 0.003 $/M tokens, Clef-flash is far dearer per query.

Scripts: `rr_eval.py`, `clef_eval.py`, `fuse_eval.py` + `fuse_an.py` (session scratchpad, not in the repo).
