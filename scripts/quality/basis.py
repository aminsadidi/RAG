"""Experimental or theoretical: SubQ reads a few telling passages of each paper (its abstract and the passages the
data map finds most likely to hold data, junk left out) and says whether the authors measured, calculated or
reviewed. The paper gets the label of the strongest answers. Only scores and labels are written (public repo).

    python scripts/quality/basis.py run OUT.jsonl [N]   (QDRANT_URL, QDRANT_API_KEY, SUBQ_KEYS; N papers, for a trial)
    python scripts/quality/basis.py label OUT.jsonl     (writes data/rag-optics/paper_basis.json)
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from datamap import ROOT, points  # noqa: E402

QUESTIONS = {
    "measured": "Does the passage report results that the authors themselves obtained in an experiment: values measured "
                "on a sample with an instrument or laser (not taken from other papers)?",
    "calculated": "Does the passage report results the authors computed from theory rather than measured: first-principles "
                  "(DFT, ab initio), numerical simulation or a model calculation?",
    "review": "Is the passage from a review, handbook, book chapter or compilation that summarizes results of other papers "
              "rather than reporting new work?",
}
DATA = ("sellmeier", "ri_table", "dij", "dndt", "pm", "damage", "thermal", "transparency", "bandgap")


def data_scores():
    """node_id -> how surely the passage holds data (its best datamap score), None for junk."""
    import gzip
    rows = json.load(gzip.open(ROOT / "data/rag-optics/datamap.json.gz"))
    return {r["node"]: (None if r["s"].get("junk", 0) > 0.5 else max(r["s"].get(k, 0) for k in DATA)) for r in rows if r["s"]}


def telling(pts, scores, k=4):
    """The abstract and the passages most likely to hold data (from the data map), junk left out; at most k."""
    def rank(p):
        pl = p["payload"]
        return 2 if pl.get("source_type") != "full_text_pdf" else scores.get(pl.get("node_id"), 0) or 0
    return sorted((p for p in pts if scores.get(p["payload"].get("node_id"), 0) is not None), key=rank, reverse=True)[:k]


def judge(p):
    import subq
    text = str(p["payload"].get("text", ""))[:2500]
    out = subq.ask({"model": "subq-snap-preview", "state": f"Passage from a scientific paper on optical crystals:\n\n{text}",
                    "questions": {k: {"type": "noul", "instructions": q} for k, q in QUESTIONS.items()}})
    return {"doc": p["payload"].get("doc_id"), "s": {k: round(v, 3) for k, v in (out or {}).items()}}


def run(path, n=None):
    docs = sorted(p["doc_id"] for p in json.loads((ROOT / "web/src/papers.json").read_text(encoding="utf-8")))[:n]
    fields = ("doc_id", "node_id", "text", "source_type")
    pts = [p for i in range(0, len(docs), 100) for p in points(docs[i:i + 100], fields)]
    by = {}
    for p in pts:
        by.setdefault(p["payload"]["doc_id"], []).append(p)
    scores = data_scores()
    chosen = [p for d in by.values() for p in telling(d, scores)]
    print(f"{len(by)} papers, {len(chosen)} passages", flush=True)
    with ThreadPoolExecutor(16) as ex, open(path, "w", encoding="utf-8") as f:
        for row in ex.map(judge, chosen):
            f.write(json.dumps(row) + "\n")
    import subq
    print(f"done, {subq.tokens[0]:,} input tokens")


def label(m, c, r):
    """A paper's label from the highest probability of each answer over its passages."""
    if r > 0.6 and max(m, c) < 0.8:
        return "review"
    if m > 0.6 and c > 0.8:  # a side calculation (a fit, a band structure) in an experimental paper is not "both"
        return "both"
    if m > 0.6:
        return "experimental"
    if c > 0.6:
        return "theoretical"
    return "unknown"


def write(path):
    best = {}
    for line in open(path, encoding="utf-8"):
        row = json.loads(line)
        if row["s"]:
            b = best.setdefault(row["doc"], dict.fromkeys(QUESTIONS, 0.0))
            for k in QUESTIONS:
                b[k] = max(b[k], row["s"].get(k, 0))
    out = {d: {"label": label(b["measured"], b["calculated"], b["review"]), **b} for d, b in sorted(best.items())}
    (ROOT / "data/rag-optics/paper_basis.json").write_text(json.dumps(out, indent=0) + "\n", encoding="utf-8")
    from collections import Counter
    print(Counter(v["label"] for v in out.values()))


if __name__ == "__main__":
    assert label(0.9, 0.1, 0.1) == "experimental" and label(0.1, 0.9, 0.1) == "theoretical" and label(0.9, 0.9, 0) == "both"
    assert label(0.3, 0.2, 0.9) == "review" and label(0.2, 0.2, 0.2) == "unknown"
    if sys.argv[1] == "run":
        run(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
    else:
        write(sys.argv[2])
