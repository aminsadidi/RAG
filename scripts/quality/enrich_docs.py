"""The data map and the enrichment (datamap.py, enrich.py) for some papers only, e.g. the ones just added:
SubQ scores every passage of these papers (kinds of data, junk), the passages get `has` (the kinds scored
above 0.7, as for the rest of the collection), `junk` and `crystals`, and the scores are added to
data/rag-optics/datamap.json.gz. Only ids, scores and crystal names are written, never text.

    python scripts/quality/enrich_docs.py DOC_IDS.json      (QDRANT_URL, QDRANT_API_KEY, SUBQ_KEYS)
"""
import gzip
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import datamap  # noqa: E402
import enrich  # noqa: E402
import subq  # noqa: E402

MAP = enrich.ROOT / "data/rag-optics/datamap.json.gz"
KINDS = [k for k in datamap.QUESTIONS if k != "junk"]


def one(p):
    row = datamap.judge(p)  # SubQ: kinds of data and junk
    pl = p["payload"]
    text = str(pl.get("text", ""))[:2500]
    cand = enrich.candidates(text, pl.get("material"))
    crystals = []
    if cand:
        ans = subq.ask({"model": "subq-snap-preview", "state": f"Passage from a scientific paper on optical crystals:\n\n{text}",
                        "questions": {f"c{i}": {"type": "noul", "instructions": f"Is this passage about the crystal {m} (its properties, data, growth or use)?"}
                                      for i, m in enumerate(cand)}}) or {}
        crystals = [m for i, m in enumerate(cand) if ans.get(f"c{i}", 0) > 0.6]
    s = row["s"]
    payload = {"crystals": crystals, "has": [k for k in KINDS if s.get(k, 0) > 0.7]}
    if "junk" in s:
        payload["junk"] = round(s["junk"], 3)
    datamap.qdrant("/collections/rag-optics/points/payload?wait=false", {"payload": payload, "points": [p["id"]]})
    return row, payload


def main():
    docs = json.loads(Path(sys.argv[1]).read_text())
    pts = [p for i in range(0, len(docs), 50)
           for p in datamap.points(docs[i:i + 50], ("doc_id", "node_id", "pages", "content_type", "text", "material"))]
    with ThreadPoolExecutor(16) as ex:
        res = list(ex.map(one, pts))
    rows = json.load(gzip.open(MAP, "rt"))
    done = {r["node"] for r, _ in res}
    rows = [r for r in rows if r["node"] not in done] + [r for r, _ in res]
    with gzip.open(MAP, "wt", encoding="utf-8") as f:
        json.dump(rows, f, separators=(",", ":"))
    print(f"{len(docs)} papers, {len(pts)} passages: {sum(1 for _, p in res if p['crystals'])} with crystals, "
          f"{sum(1 for _, p in res if p['has'])} with data, {sum(1 for _, p in res if p.get('junk', 0) > 0.9)} junk > 0.9; "
          f"{subq.tokens[0]:,} SubQ tokens")


if __name__ == "__main__":
    main()
