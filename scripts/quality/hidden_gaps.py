"""Data the collection holds but the gap list (gaps.py) misses: the text of old PDFs often mangles a formula's
subscripts ("CuGaS," or "CuGaS 2" for CuGaS2), so the data map does not name the crystal. Among the passages the data
map scores as holding dn/dT or d_ij, this finds the missing crystals by a loose form of their formula and asks SubQ
whether the passage gives measured values of that kind for that crystal. Prints the likely ones (ids and pages; the
text stays in Qdrant).

    python scripts/quality/hidden_gaps.py OUT.json   (QDRANT_URL, QDRANT_API_KEY, SUBQ_KEYS)
"""
import gzip
import json
import re
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import subq  # noqa: E402
from datamap import ROOT, qdrant  # noqa: E402

KIND = {"dndt": "the temperature dependence of the refractive indices (dn/dT, thermo-optic coefficients or a "
                "temperature-dependent Sellmeier equation)",
        "dij": "second-order nonlinear coefficients d_ij (absolute values in pm/V or m/V, or relative to a named crystal)"}


def loose(formula):
    """A regex for a formula whose subscripts the PDF text may have lost or mangled: each number may be missing, spaced,
    or read as a comma; the name must not run on into a longer formula (CuGaS must not match CuGaSe2)."""
    out = ""
    for part in re.findall(r"\d+(?:\.\d+)?|[A-Z][a-z]?|.", formula):
        out += rf"(?:\s?{re.escape(part)}|\s?,)?" if part[0].isdigit() else re.escape(part)
    return re.compile(rf"(?<![A-Za-z]){out}(?![a-z])")


def missing():
    aniso = json.loads((ROOT / "web/public/ri/aniso.json").read_text(encoding="utf-8"))
    dij = json.loads((ROOT / "web/public/ri/dij.json").read_text(encoding="utf-8"))
    # chemical formulas only: two element symbols at least, so "C", "Se" or the liquid crystal "E7" (which match almost
    # every passage and cost thousands of SubQ calls) are left out
    crystals = [c for c in aniso if re.fullmatch(r"[A-Za-z0-9().]+", c["material"]) and len(re.findall(r"[A-Z]", c["material"])) >= 2]
    return {"dndt": [c["material"] for c in crystals if not any(s.get("thermo") for s in c["sources"])],
            "dij": [c["material"] for c in crystals if c["material"] not in dij and not c.get("cubic")]}


def texts(nodes):
    ids = {str(uuid.uuid5(uuid.NAMESPACE_URL, f"matrag:{n}")): n for n in nodes}  # the indexer's point ids
    out = {}
    keys = list(ids)
    for i in range(0, len(keys), 500):
        got = qdrant("/collections/rag-optics/points", {"ids": keys[i:i + 500], "with_payload": ["node_id", "text", "pages", "doc_id"]})
        for p in got:
            out[p["payload"]["node_id"]] = p["payload"]
    return out


def judge(job):
    kind, crystal, pl = job
    p = subq.score(f"Passage from a scientific paper:\n\n{str(pl['text'])[:3000]}",
                   f"Does the passage give measured values of {KIND[kind]} of {crystal}?",
                   "yes, values for this crystal", "no, or only for other crystals, or only calculated or qualitative")
    return {"kind": kind, "crystal": crystal, "doc": pl["doc_id"], "node": pl["node_id"], "pages": pl.get("pages"), "p": round(p or 0, 3)}


def main(out):
    gaps = missing()
    rows = json.load(gzip.open(ROOT / "data/rag-optics/datamap.json.gz"))
    want = {r["node"]: r for r in rows if max((r["s"] or {}).get("dndt", 0), (r["s"] or {}).get("dij", 0)) > 0.7}
    found = texts(want)
    jobs = []
    for kind, crystals in gaps.items():
        pats = [(c, loose(c)) for c in crystals]
        for node, pl in found.items():
            if (want[node]["s"] or {}).get(kind, 0) <= 0.7:
                continue
            for c, pat in pats:
                if c not in (want[node]["f"] or []) and pat.search(str(pl["text"])):
                    jobs.append((kind, c, pl))
    print(f"{len(found)} passages, {len(jobs)} (crystal, passage) pairs to judge", flush=True)
    with ThreadPoolExecutor(12) as ex:
        res = sorted(ex.map(judge, jobs), key=lambda r: -r["p"])
    json.dump(res, open(out, "w"), indent=0)
    for r in res:
        if r["p"] > 0.7:
            print(r["p"], r["kind"], r["crystal"], r["doc"], "p.", r["pages"], r["node"])
    print(f"SubQ tokens {subq.tokens[0]:,}")


if __name__ == "__main__":
    assert loose("CuGaS2").search("of CuGaS, and CuInS") and not loose("CuGaS2").search("CuGaSe2")
    main(sys.argv[1])
