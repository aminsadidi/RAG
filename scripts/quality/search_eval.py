"""Search quality on the gold questions, against the live site: the site's order (hybrid) and the same
top-30 pool reranked by SubQ. Writes reports/search-<date>.md and .json, and fails (exit 1) when the
hybrid paper MRR@10 on the dev questions falls more than 0.03 below baseline.json.

The metric is paper-level MRR@10 (a paper counts once, at its best passage; reciprocal rank 0 past 10): not
the chunk-level, page-checked, uncapped "chunk MRR" of src/matrag/evaluate.py. Every value has a 95% bootstrap
interval, and SubQ is compared with the site's order by a paired bootstrap (evalstats.py).

The gold questions are split once and for all (data/rag-optics/gold/split.csv): "dev" holds the 200 questions
every tuning decision so far was made on; tune on dev only, and report numbers on "test" (--split test).
Refractive-index (ri) questions also accept every paper of the collection with a dispersion formula for the
material (paper_formulas.yml), not only the papers refractiveindex.info cites.

    python scripts/quality/search_eval.py [N] [--split dev|test]   (SITE_USER, SITE_PASS, SUBQ_KEYS in the environment)
"""
import csv
import datetime as dt
import json
import os
import random
import statistics as st
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evalstats  # noqa: E402
import site_login  # noqa: E402
import subq  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent / "reports"
BASE = os.environ.get("SITE_URL") or (ROOT / "web" / "site_url.txt").read_text().strip()
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
SPLIT = sys.argv[sys.argv.index("--split") + 1] if "--split" in sys.argv else "dev"
ARGS = [a for a in ARGS if a != SPLIT]
N = int(ARGS[0]) if ARGS else 200

split = evalstats.load_split()
rows = [r for f in ("questions.csv", "generated.csv")
        for r in csv.DictReader(open(ROOT / "data/rag-optics/gold" / f, encoding="utf-8")) if r.get("doc_id")]
# a question added after the split was frozen is a test question
rows = [r for r in rows if split.get(r["id"], "test") == SPLIT]
random.Random(0).shuffle(rows)
rows = rows[:N]
EXTRA = evalstats.ri_alternatives()

op = site_login.login(BASE)


def search(q):
    req = urllib.request.Request(f"{BASE}/api/search", json.dumps({"q": q, "topK": 30, "rerank": False}).encode(),
                                 {"content-type": "application/json"})
    for a in range(4):
        try:
            return json.load(op.open(req, timeout=120))
        except Exception:
            time.sleep(3 * (a + 1))
    raise RuntimeError("search failed")


def one(r):
    d = search(r["question"])
    q = d.get("searchQuery") or r["question"]
    hits = d["hits"]

    def sc(h):
        return subq.score(f"Search question: {q}\n\nPassage: {h.get('citation', '')} — {str(h.get('text', ''))[:1200]}",
                          "Does the passage come from a paper that answers the search question (same material and same quantity)?",
                          "The passage gives or directly concerns the requested data for this material",
                          "Another material, another quantity, or unrelated")
    with ThreadPoolExecutor(10) as ex:
        scores = list(ex.map(sc, hits))
    return {"id": r["id"], "group": r["id"].split("-")[0], "gold": evalstats.accepted(r["id"], r["doc_id"], EXTRA), "ms": d.get("ms"),
            "docs": [h["doc_id"] for h in hits], "subq": scores}


def rank(order, x):
    gold, seen = set(x["gold"].replace(";", "|").split("|")), []
    for i in order:  # a paper counts once, at its best passage
        if x["docs"][i] in seen:
            continue
        seen.append(x["docs"][i])
        if x["docs"][i] in gold:
            return len(seen)
    return None


def metrics(ranks):
    return {"R@1": st.mean(1 if r == 1 else 0 for r in ranks), "R@3": st.mean(1 if r and r <= 3 else 0 for r in ranks),
            "R@10": st.mean(1 if r and r <= 10 else 0 for r in ranks),
            "MRR@10": st.mean(1 / r if r and r <= 10 else 0 for r in ranks)}


with ThreadPoolExecutor(3) as ex:
    res = list(ex.map(one, rows))
H = [rank(range(len(x["docs"])), x) for x in res]
ok = [x for x in res if all(s is not None for s in x["subq"])]
Q = [rank(sorted(range(len(x["docs"])), key=lambda i: -x["subq"][i]), x) for x in ok]
# SubQ is compared with the site's order on the same questions (those SubQ scored completely), not on all of them
Hok = [rank(range(len(x["docs"])), x) for x in ok]
mh, mq = metrics(H), metrics(Q) if ok else None
mhok = metrics(Hok) if ok else None
groups = sorted({x["group"] for x in res})

base = json.loads((Path(__file__).parent / "baseline.json").read_text())
day = dt.date.today().isoformat()
ci = lambda ranks: evalstats.ci_text(evalstats.bootstrap_ci([evalstats.rr10(r) for r in ranks]))  # noqa: E731
lines = [f"# Search quality {day} ({SPLIT} questions)", "", f"{len(res)} {SPLIT} gold questions against {BASE}; SubQ scored {len(ok)} "
         f"({subq.tokens[0]:,} input tokens). Paper-level MRR@10 with its 95% bootstrap interval.", "",
         "| | R@1 | R@3 | R@10 | paper MRR@10 [95% CI] |", "|---|---|---|---|---|",
         f"| site order (hybrid) | {mh['R@1']:.3f} | {mh['R@3']:.3f} | {mh['R@10']:.3f} | **{ci(H)}** |"]
if mq:
    if len(ok) < len(res):
        lines.append(f"| site order, the {len(ok)} SubQ scored | {mhok['R@1']:.3f} | {mhok['R@3']:.3f} | {mhok['R@10']:.3f} | {ci(Hok)} |")
    lines.append(f"| SubQ rerank of the top 30 (same {len(ok)}) | {mq['R@1']:.3f} | {mq['R@3']:.3f} | {mq['R@10']:.3f} | **{ci(Q)}** |")
    pd = evalstats.paired_bootstrap([evalstats.rr10(r) for r in Hok], [evalstats.rr10(r) for r in Q])
    lines += ["", f"SubQ − site order, paired on the same {len(ok)} questions: {pd[0]:+.3f} [{pd[1]:+.3f}, {pd[2]:+.3f}] "
              f"(not better in {pd[3]:.1%} of the resamples)."]
lines += ["", f"Baseline (hybrid paper MRR@10, dev questions): {base['hybrid_mrr10']:.3f}.", "", "| group | n | hybrid | SubQ |", "|---|---|---|---|"]
for g in groups:
    iq = [i for i, x in enumerate(ok) if x["group"] == g]  # both columns on the questions SubQ scored
    lines.append(f"| {g} | {len(iq)} | {metrics([Hok[i] for i in iq])['MRR@10']:.3f} | {metrics([Q[i] for i in iq])['MRR@10']:.3f} |"
                 if iq else f"| {g} | 0 | — | — |")
missed = [x["id"] for x, r in zip(res, H) if not r or r > 10]
lines += ["", f"Gold paper not in the top 10 ({len(missed)}): " + ", ".join(missed[:60])]
OUT.mkdir(exist_ok=True)
name = f"search-{day}" + ("" if SPLIT == "dev" else f"-{SPLIT}")
(OUT / f"{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
(OUT / f"{name}.json").write_text(json.dumps({"split": SPLIT, "hybrid": mh, "hybrid_same_as_subq": mhok, "subq": mq, "rows": res}), encoding="utf-8")
print("\n".join(lines))
if SPLIT == "dev" and mh["MRR@10"] < base["hybrid_mrr10"] - 0.03:
    print(f"::error::search MRR@10 {mh['MRR@10']:.3f} is below the baseline {base['hybrid_mrr10']:.3f}")
    sys.exit(1)
