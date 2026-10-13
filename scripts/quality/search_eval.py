"""Search quality on the gold questions, against the live site: the site's order (hybrid) and the same
top-30 pool reranked by SubQ. Writes reports/search-<date>.md and .json, and fails (exit 1) when the
hybrid MRR@10 falls more than 0.03 below baseline.json, so a change that hurts search is seen at once.

    python scripts/quality/search_eval.py [N]      (SITE_KEY and SUBQ_KEYS in the environment)
"""
import csv
import datetime as dt
import http.cookiejar
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
import subq  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent / "reports"
BASE = os.environ.get("SITE_URL", "https://matrag.ethanjamescarter1995.workers.dev")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 200

rows = [r for f in ("questions.csv", "generated.csv")
        for r in csv.DictReader(open(ROOT / "data/rag-optics/gold" / f, encoding="utf-8")) if r.get("doc_id")]
random.Random(0).shuffle(rows)
rows = rows[:N]

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.addheaders = [("User-Agent", "matrag-quality/1")]
op.open(f"{BASE}/?key={os.environ['SITE_KEY']}").read()


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
    return {"id": r["id"], "group": r["id"].split("-")[0], "gold": r["doc_id"], "ms": d.get("ms"),
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
mh, mq = metrics(H), metrics(Q) if ok else None
groups = sorted({x["group"] for x in res})

base = json.loads((Path(__file__).parent / "baseline.json").read_text())
day = dt.date.today().isoformat()
lines = [f"# Search quality {day}", "", f"{len(res)} gold questions against {BASE}; SubQ scored {len(ok)} "
         f"({subq.tokens[0]:,} input tokens).", "", "| | R@1 | R@3 | R@10 | MRR@10 |", "|---|---|---|---|---|",
         f"| site order (hybrid) | {mh['R@1']:.3f} | {mh['R@3']:.3f} | {mh['R@10']:.3f} | **{mh['MRR@10']:.3f}** |"]
if mq:
    lines.append(f"| SubQ rerank of the top 30 | {mq['R@1']:.3f} | {mq['R@3']:.3f} | {mq['R@10']:.3f} | **{mq['MRR@10']:.3f}** |")
lines += ["", f"Baseline (hybrid MRR@10): {base['hybrid_mrr10']:.3f}.", "", "| group | n | hybrid | SubQ |", "|---|---|---|---|"]
for g in groups:
    ih = [i for i, x in enumerate(res) if x["group"] == g]
    iq = [i for i, x in enumerate(ok) if x["group"] == g]
    lines.append(f"| {g} | {len(ih)} | {metrics([H[i] for i in ih])['MRR@10']:.3f} | "
                 f"{metrics([Q[i] for i in iq])['MRR@10']:.3f} |" if iq else f"| {g} | {len(ih)} | {metrics([H[i] for i in ih])['MRR@10']:.3f} | — |")
missed = [x["id"] for x, r in zip(res, H) if not r or r > 10]
lines += ["", f"Gold paper not in the top 10 ({len(missed)}): " + ", ".join(missed[:60])]
OUT.mkdir(exist_ok=True)
(OUT / f"search-{day}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
(OUT / f"search-{day}.json").write_text(json.dumps({"hybrid": mh, "subq": mq, "rows": res}), encoding="utf-8")
print("\n".join(lines))
if mh["MRR@10"] < base["hybrid_mrr10"] - 0.03:
    print(f"::error::search MRR@10 {mh['MRR@10']:.3f} is below the baseline {base['hybrid_mrr10']:.3f}")
    sys.exit(1)
