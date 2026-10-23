"""What the phase-matching tab still lacks, and where the collection may have it: for every crystal without dn/dT
or without d_ij, the passages the data map scores as holding that kind of data and that name the crystal, best
first. Writes data/rag-optics/gaps.json (ids, pages and scores only; the text stays in Qdrant).

    python scripts/quality/gaps.py
"""
import collections
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KINDS = {"dndt": "dndt", "dij": "dij"}  # what is missing -> the data-map score that finds it


def main(per=6, cut=0.7):
    aniso = json.loads((ROOT / "web/public/ri/aniso.json").read_text(encoding="utf-8"))
    dij = json.loads((ROOT / "web/public/ri/dij.json").read_text(encoding="utf-8"))
    missing = {"dndt": {c["material"] for c in aniso if not any(s.get("thermo") for s in c["sources"])},
               "dij": {c["material"] for c in aniso if c["material"] not in dij}}
    rows = json.load(gzip.open(ROOT / "data/rag-optics/datamap.json.gz"))
    found = {k: collections.defaultdict(list) for k in KINDS}
    for r in rows:
        for k, score in KINDS.items():
            p = (r["s"] or {}).get(score, 0)
            if p > cut:
                for m in set(r["f"] or []) & missing[k]:
                    found[k][m].append({"doc": r["doc"], "pages": r["pages"], "node": r["node"], "p": p})
    out = {}
    for k in KINDS:
        ranked = sorted(found[k].items(), key=lambda kv: -len({c["doc"] for c in kv[1]}))
        out[k] = [{"material": m, "papers": len({c["doc"] for c in cs}),
                   "best": sorted(cs, key=lambda c: -c["p"])[:per]} for m, cs in ranked]
        out[k + "_nothing_found"] = sorted(missing[k] - set(found[k]))
    (ROOT / "data/rag-optics/gaps.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for k in KINDS:
        print(f"{k}: {len(missing[k])} crystals missing, {len(out[k])} with candidate passages, "
              f"{sum(len(g['best']) for g in out[k])} passages to read; top: "
              + ", ".join(f"{g['material']} ({g['papers']})" for g in out[k][:8]))


if __name__ == "__main__":
    main()
