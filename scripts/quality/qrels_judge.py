"""A second judge for the relevance judgments (qrels.csv, made by Gemini from paper titles): SubQ reads
the same question and the paper's reference, and every pair where the two disagree is listed for a
person to look at. Writes reports/qrels-<date>.md and qrels-disagreements-<date>.csv.

    python scripts/quality/qrels_judge.py QRELS_CSV      (SUBQ_KEYS in the environment)
"""
import csv
import datetime as dt
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import subq  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent / "reports"
qrels = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
questions = {r["id"]: r["question"] for r in csv.DictReader(open(ROOT / "data/rag-optics/gold/questions.csv", encoding="utf-8"))}
papers = {p["doc_id"]: p for p in json.loads((ROOT / "web/src/papers.json").read_text(encoding="utf-8"))}


def judge(r):
    p = papers.get(r["doc_id"], {})
    ref = p.get("reference") or p.get("citation") or r["doc_id"]
    s = subq.score(f"Search question: {questions.get(r['id'], r['id'])}\n\nPaper: {ref}",
                   "Does this paper give the requested quantity (dispersion formula or measured refractive indices) for this exact material?",
                   "The paper reports refractive-index data or a dispersion formula for this material",
                   "Another material, or other properties of it, or unrelated")
    return {**r, "subq": s}


with ThreadPoolExecutor(12) as ex:
    res = list(ex.map(judge, qrels))
done = [x for x in res if x["subq"] is not None]
# disagreement: Gemini says exact answer (2) and SubQ below 0.2, or Gemini says not relevant (0) and SubQ above 0.8
dis = [x for x in done if (x["grade"] == "2" and x["subq"] < 0.2) or (x["grade"] == "0" and x["subq"] > 0.8)]
by = {g: [x["subq"] for x in done if x["grade"] == g] for g in ("0", "1", "2")}
day = dt.date.today().isoformat()
OUT.mkdir(exist_ok=True)
with open(OUT / f"qrels-disagreements-{day}.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id", "doc_id", "grade", "subq", "reason"], extrasaction="ignore")
    w.writeheader()
    w.writerows(sorted(dis, key=lambda x: (x["id"], x["doc_id"])))
mean = lambda v: sum(v) / len(v) if v else float("nan")  # noqa: E731
lines = [f"# Relevance judgments, second judge {day}", "",
         f"{len(res)} pairs of {sys.argv[1]}; SubQ judged {len(done)} ({subq.tokens[0]:,} input tokens).", "",
         "| Gemini grade | pairs | mean SubQ probability |", "|---|---|---|"]
lines += [f"| {g} | {len(v)} | {mean(v):.3f} |" for g, v in by.items()]
lines += ["", f"Disagreements (grade 2 with SubQ < 0.2, or grade 0 with SubQ > 0.8): **{len(dis)}**, "
          f"listed in qrels-disagreements-{day}.csv for a person to check."]
(OUT / f"qrels-{day}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
