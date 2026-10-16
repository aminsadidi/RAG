# SubQ reranking in two batched requests (2026-10-16)

The same 200 gold questions (seed 0) as the other reports.

## Pool of 30 passages, MRR@10 by paper (scratchpad replay of the site's first stage)

| ranking | MRR@10 | SubQ requests per search |
|---|---|---|
| first stage (hybrid + crystal focus) | 0.434 | 0 |
| SubQ, one request per passage | 0.493 | 30 |
| SubQ, 2 requests of 15 passages | 0.476 | 2 |
| SubQ, 2 requests of 15, score + 0.1/rank | 0.491 | 2 |

## Live site after the change (scripts: variants with `rerank` true/false)

| search | R@1 | R@10 | MRR@10 | ri | gen | dij | thermo |
|---|---|---|---|---|---|---|---|
| passages, no rerank | 0.450 | 0.680 | 0.532 | 0.394 | 0.758 | 0.500 | 0.250 |
| passages, SubQ | 0.550 | 0.720 | 0.614 | 0.459 | 0.873 | 0.417 | 0.375 |
| one per paper, no rerank | 0.425 | 0.710 | 0.511 | 0.387 | 0.724 | 0.521 | 0.165 |
| one per paper, SubQ | 0.510 | 0.760 | 0.597 | 0.466 | 0.828 | 0.404 | 0.333 |

About 1.2–2.3 s per search with reranking; it is now on by default (rerank: false turns it off). The d_ij
questions lose (0.50 -> 0.42): a case to look at.

## The d_ij questions (7 of the 200)

The loss came from one question. AgGaS2: without reranking the gold paper (Zondy et al. 1997) was first through
its reference list (a passage that names "AgGaS2" and "nonlinear coefficients"); SubQ ranks that passage low and
puts first Harasaki & Katō (1997), whose abstract gives d36(AgGaS2) and was not among the gold answers. For
AgGaSe2 the gold answer was a 2022 chemistry paper on related compounds, while the search finds the measurements
of d36 itself (Kildal & Mikkelsen 1973, Byer et al. 1974). These three papers were added to questions.csv as
accepted answers. Rerun on the live site:

| search | R@1 | R@10 | MRR@10 | ri | gen | dij | thermo |
|---|---|---|---|---|---|---|---|
| passages, no rerank | 0.445 | 0.675 | 0.527 | 0.389 | 0.752 | 0.500 | 0.250 |
| passages, SubQ | 0.555 | 0.725 | 0.618 | 0.459 | 0.864 | 0.571 | 0.500 |

Still missed with either ranking: CsB3O5, whose gold paper (Zhang et al. 2007, the LixCs1−xB3O5 family, filed
under LBO) is not among the first 30 papers of the first stage.
