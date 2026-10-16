"""Search quality on the questions made from the site's own data (data_questions.csv, gold_from_data.py),
on the live site, with and without SubQ reranking. For every question the first 10 papers of each run are
kept, and SubQ judges each paper that is not an accepted answer: does its best passage give the requested
data for this crystal? Papers it finds likely (p > 0.8) are listed for a person to check and, when they do
answer, to add to the question's accepted answers (the score then counts them).

    python scripts/quality/data_eval.py        (SITE_KEY or MATRAG_COOKIES, and SUBQ_KEYS, in the environment)

Writes reports/data-eval-<date>.md, .json and data-alternatives-<date>.csv (ids and scores only; with PRIVATE_DIR
set, the judged passages go to PRIVATE_DIR/data-alternatives-<date>.json, outside the public repository).
"""
import csv
import datetime as dt
import http.cookiejar
import json
import os
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
rows = list(csv.DictReader(open(ROOT / "data/rag-optics/gold/data_questions.csv", encoding="utf-8")))
# papers that also answer, found by SubQ and read by a person (data_alternatives.csv): accepted as well
ALT = {}
for a in csv.DictReader(open(ROOT / "data/rag-optics/gold/data_alternatives.csv", encoding="utf-8")):
    ALT.setdefault(a["id"], set()).add(a["doc_id"])

if os.environ.get("MATRAG_COOKIES"):
    jar = http.cookiejar.MozillaCookieJar(os.environ["MATRAG_COOKIES"])
    jar.load(ignore_discard=True, ignore_expires=True)
else:
    jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.addheaders = [("User-Agent", "matrag-quality/1")]
if not os.environ.get("MATRAG_COOKIES"):
    op.open(f"{BASE}/?key={os.environ['SITE_KEY']}").read()

WHAT = {"data-sellmeier": "a dispersion (Sellmeier) formula or measured refractive indices",
        "data-dndt": "the temperature dependence of the refractive indices (dn/dT values or a thermo-optic formula)",
        "data-dij": "measured values of the second-order nonlinear coefficients d_ij"}


def search(q, rerank):
    req = urllib.request.Request(f"{BASE}/api/search", json.dumps({"q": q, "topK": 10, "perPaper": True, "rerank": rerank}).encode(),
                                 {"content-type": "application/json"})
    for a in range(4):
        try:
            return json.load(op.open(req, timeout=120))
        except Exception:
            time.sleep(3 * (a + 1))
    raise RuntimeError("search failed")


def rank(docs, gold):
    for i, d in enumerate(docs):
        if d in gold:
            return i + 1
    return None


def one(r):
    gold = set(r["doc_id"].split(";")) | ALT.get(r["id"], set())
    out = {"id": r["id"], "group": r["group"], "question": r["question"], "gold": sorted(gold)}
    for name, rr in (("base", False), ("subq", True)):
        d = search(r["question"], rr)
        out[name] = [{"doc": h["doc_id"], "cite": h.get("citation", ""), "text": str(h.get("text", ""))[:1200]} for h in d["hits"]]
        out[name + "_rank"] = rank([h["doc"] for h in out[name]], gold)
    return out


def judge(x):
    crystal = x["question"].split(" of ")[-1].rstrip("?")
    seen, alts = set(x["gold"]), []
    for h in x["base"] + x["subq"]:
        if h["doc"] in seen:
            continue
        seen.add(h["doc"])
        p = subq.score(f"Passage from a paper: {h['cite']} — {h['text']}",
                       f"Does this passage give {WHAT[x['group']]} of the crystal {crystal}?",
                       f"The passage reports this data for {crystal} itself (numbers, a formula or a table)",
                       "Another crystal, another quantity, only a mention or a citation of the data, or unrelated")
        if p is not None and p > 0.8:
            alts.append({"id": x["id"], "doc_id": h["doc"], "cite": h["cite"], "subq": round(p, 3), "passage": h["text"][:300]})
    return alts


def metrics(ranks):
    return {"n": len(ranks), "R@1": st.mean(1 if k == 1 else 0 for k in ranks), "R@10": st.mean(1 if k else 0 for k in ranks),
            "MRR@10": st.mean(1 / k if k else 0 for k in ranks)}


def main():
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(one, rows))
    cache = Path(os.environ["PRIVATE_DIR"], "data-eval-raw.json") if os.environ.get("PRIVATE_DIR") else None
    if cache:  # the searches and their passages, kept outside the repository (a later step failing loses nothing)
        cache.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    with ThreadPoolExecutor(8) as ex:
        alts = [a for part in ex.map(judge, res) for a in part]
    day = dt.date.today().isoformat()
    OUT.mkdir(exist_ok=True)
    groups = sorted({x["group"] for x in res})
    table = {name: {g: metrics([x[name + "_rank"] for x in res if x["group"] == g]) for g in groups}
             for name in ("base", "subq")}
    for name in table:
        table[name]["all"] = metrics([x[name + "_rank"] for x in res])
    lines = [f"# Search on the questions made from the site's data, {day}", "",
             f"{len(res)} questions (data_questions.csv); one result per paper, first 10; SubQ {subq.tokens[0]:,} input tokens.", "",
             "| search | group | n | R@1 | R@10 | MRR@10 |", "|---|---|---|---|---|---|"]
    for name in table:
        for g, m in table[name].items():
            lines.append(f"| {name} | {g} | {m['n']} | {m['R@1']:.3f} | {m['R@10']:.3f} | {m['MRR@10']:.3f} |")
    lines += ["", f"Papers SubQ finds likely to answer as well (p > 0.8), not yet accepted: {len(alts)}, in "
              f"data-alternatives-{day}.csv for a person to check."]
    (OUT / f"data-eval-{day}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / f"data-eval-{day}.json").write_text(json.dumps([{k: v for k, v in x.items() if k not in ("base", "subq")} |
                                                         {"base_docs": [h["doc"] for h in x["base"]], "subq_docs": [h["doc"] for h in x["subq"]]}
                                                         for x in res], indent=0), encoding="utf-8")
    with open(OUT / f"data-alternatives-{day}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "doc_id", "cite", "subq"], extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(alts, key=lambda a: (a["id"], -a["subq"])))
    if os.environ.get("PRIVATE_DIR"):  # the passages themselves (paper text) only outside the public repository
        Path(os.environ["PRIVATE_DIR"], f"data-alternatives-{day}.json").write_text(json.dumps(alts, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
