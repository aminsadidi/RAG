"""Two fields on every passage of the site's Qdrant collection, from SubQ:
  junk      the probability (from the data map) that the passage has no scientific content (cover page,
            references, garbled text); the site leaves passages with junk > 0.9 out of the search;
  crystals  the crystals the passage is about: the candidates (formulas and abbreviations in its text, and
            the crystal of the paper's folder) that SubQ confirms with probability > 0.6.
Only these fields are written; the text stays where it is. The repository is public: nothing is printed.

    python scripts/quality/enrich.py shard K N    (QDRANT_URL, QDRANT_API_KEY, SUBQ_KEYS)
    python scripts/quality/enrich.py index        (the payload indexes for the two fields)
"""
import gzip
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import datamap  # noqa: E402
import subq  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RI = ROOT / "web/public/ri"
KNOWN = ({c["material"] for c in json.loads((RI / "aniso.json").read_text())} | set(json.loads((RI / "dij.json").read_text()))
         | {x["material"] for x in json.loads((RI / "index.json").read_text()) if x["shelf"] in ("main", "papers")})
KNOWN = {m for m in KNOWN if " " not in m and len(m) > 2}
SYN = json.loads((ROOT / "web/src/shared.json").read_text())["SYNONYMS"]
JUNK = {r["node"]: r["s"].get("junk") for r in json.load(gzip.open(ROOT / "data/rag-optics/datamap.json.gz", "rt")) if r["s"]}


def candidates(text, folder):
    found = [m for m in datamap.formulas(text) if m in KNOWN]
    found += [SYN[a] for a in SYN if re.search(rf"\b{re.escape(a)}\b", text) and SYN[a] in KNOWN]
    found += [m for m in KNOWN if m in (folder or "").replace("-", "_").split("_")]
    out = []
    for m in found:
        if m not in out:
            out.append(m)
    return out[:16]


def tag(p):
    pl = p["payload"]
    text = str(pl.get("text", ""))[:2500]
    cand = candidates(text, pl.get("material"))
    crystals = []
    if cand:
        ans = subq.ask({"model": "subq-snap-preview", "state": f"Passage from a scientific paper on optical crystals:\n\n{text}",
                        "questions": {f"c{i}": {"type": "noul", "instructions": f"Is this passage about the crystal {m} (its properties, data, growth or use)?"}
                                      for i, m in enumerate(cand)}}) or {}
        crystals = [m for i, m in enumerate(cand) if ans.get(f"c{i}", 0) > 0.6]
    payload = {"crystals": crystals}
    j = JUNK.get(pl.get("node_id"))
    if j is not None:
        payload["junk"] = round(j, 3)
    datamap.qdrant("/collections/rag-optics/points/payload?wait=false", {"payload": payload, "points": [p["id"]]})
    return len(crystals), j is not None and j > 0.9


def shard(k, n):
    docs = sorted(p["doc_id"] for p in json.loads((ROOT / "web/src/papers.json").read_text(encoding="utf-8")))
    mine = [d for i, d in enumerate(docs) if i % n == k]
    pts = [p for i in range(0, len(mine), 100) for p in datamap.points(mine[i:i + 100], ["doc_id", "node_id", "text", "material"])]
    with ThreadPoolExecutor(16) as ex:
        res = list(ex.map(tag, pts))
    print(f"shard {k}/{n}: {len(pts)} passages, {sum(1 for c, _ in res if c)} with crystals, "
          f"{sum(1 for _, j in res if j)} junk > 0.9, {subq.tokens[0]:,} SubQ tokens")


if __name__ == "__main__":
    if sys.argv[1] == "index":
        for field, schema in (("junk", "float"), ("crystals", "keyword")):
            datamap.qdrant("/collections/rag-optics/index?wait=true", {"field_name": field, "field_schema": schema}, "PUT")
        print("indexes made")
    else:
        shard(int(sys.argv[2]), int(sys.argv[3]))
