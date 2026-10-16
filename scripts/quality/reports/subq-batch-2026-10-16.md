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
