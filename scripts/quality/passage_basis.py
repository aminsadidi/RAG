"""The kind of each data passage (measured, calculated, both, or cited from other work) from the SubQ audit
(data/rag-optics/audit/data.json.gz, made by audit.py data), written to the passages in Qdrant as the payload field
basis_p; the site shows it on search results in place of the paper's label. Run it again after a Colab update that
rewrites the points (a paper converted again loses the field, and the site falls back to the paper's label).

    python scripts/quality/passage_basis.py [--dry]   (QDRANT_URL, QDRANT_API_KEY)

The thresholds come from a check by hand of 30 passages (2026-10): measured, review and both were right 18 times out of
18; calculated was right only 4 times out of 8 (an experimental paper's "calculated phase-matching angles" or an
introduction scored as calculated), so it is kept only when the passage is clearly not measured.
"""
import collections
import gzip
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from datamap import ROOT, qdrant  # noqa: E402


def label(r):
    m, c, v = r.get("measured", 0), r.get("calculated", 0), r.get("review", 0)
    if v > 0.7:
        return "review"
    if v < 0.5 and m > 0.7:
        return "both" if c > 0.7 else "experimental" if c < 0.5 else None
    if c > 0.85 and m < 0.2 and v < 0.3:
        return "theoretical"
    return None


def main(dry):
    rows = json.load(gzip.open(ROOT / "data/rag-optics/audit/data.json.gz"))
    by = collections.defaultdict(list)
    for r in rows:
        if (lab := label(r)):
            by[lab].append(str(uuid.uuid5(uuid.NAMESPACE_URL, f"matrag:{r['node']}")))  # the indexer's point ids
    # a paper converted again since the audit has new points: setting a payload on a missing id fails the whole call
    ids = [i for v in by.values() for i in v]
    have = {p["id"] for k in range(0, len(ids), 1000)
            for p in qdrant("/collections/rag-optics/points", {"ids": ids[k:k + 1000], "with_payload": False})}
    by = {k: [i for i in v if i in have] for k, v in by.items()}
    print({k: len(v) for k, v in by.items()}, f"of {len(rows)} passages ({len(ids) - len(have)} no longer in Qdrant)")
    if dry:
        return
    for lab, ids in by.items():
        for i in range(0, len(ids), 1000):
            qdrant("/collections/rag-optics/points/payload?wait=true", {"payload": {"basis_p": lab}, "points": ids[i:i + 1000]})


if __name__ == "__main__":
    assert label({"measured": 0.93, "calculated": 0.4, "review": 0.01}) == "experimental"
    assert label({"measured": 0.59, "calculated": 0.95, "review": 0.06}) is None  # an experimental paper's calculated angles
    main("--dry" in sys.argv)
