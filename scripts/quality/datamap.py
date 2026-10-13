"""Data map of the collection: SubQ reads every passage (chunk) of the site's Qdrant collection and gives the
probability that it holds each kind of data (dispersion formula, d_ij, dn/dT, damage threshold, ...) and
whether it is junk (cover page, references, garbled text). The formulas named in the passage are found by
pattern. Only scores, ids and pages are written, never the text (the repository is public).

    python scripts/quality/datamap.py shard K N OUT.jsonl   (QDRANT_URL, QDRANT_API_KEY, SUBQ_KEYS)
    python scripts/quality/datamap.py merge DIR             (writes data/rag-optics/datamap.json.gz and reports/datamap-<date>.md)
"""
import collections
import datetime as dt
import gzip
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
ROOT = Path(__file__).resolve().parents[2]

QUESTIONS = {
    "sellmeier": "Does the passage give a dispersion formula (Sellmeier or similar equation, with its coefficients) for the refractive index of a material?",
    "ri_table": "Does the passage give measured refractive-index values of a material at several wavelengths (a table or list of numbers)?",
    "dij": "Does the passage give values of second-order nonlinear coefficients (d_ij, d_eff or chi(2), in pm/V or relative to another crystal)?",
    "dndt": "Does the passage give the temperature dependence of the refractive index (dn/dT values or a thermo-optic formula)?",
    "pm": "Does the passage give measured phase-matching angles, phase-matching temperatures or acceptance bandwidths?",
    "damage": "Does the passage give a laser-induced damage threshold (with its pulse duration or wavelength)?",
    "thermal": "Does the passage give thermal conductivity or thermal-expansion coefficients of a crystal?",
    "transparency": "Does the passage give the transparency range or absorption edges / absorption coefficient of a crystal?",
    "bandgap": "Does the passage give the band-gap energy of a material?",
    "junk": "Is the passage without scientific content: a cover page, copyright notice, table of contents, list of references, author affiliations only, or unreadable garbled text?",
}
ELEMENTS = set(("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr "
                "Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt "
                "Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U D").split())
FORMULA = re.compile(r"\b(?:[A-Z][a-z]?\d*(?:\.\d+)?){2,}\b")


def formulas(text):
    out = []
    for w in FORMULA.findall(text):
        els = re.findall(r"[A-Z][a-z]?", w)
        if len(els) >= 2 and all(e in ELEMENTS for e in els) and re.search(r"[\da-z]", w) and w not in out:
            out.append(w)
    return out[:12]


def qdrant(path, body):
    req = urllib.request.Request(os.environ["QDRANT_URL"].rstrip("/") + path, json.dumps(body).encode(),
                                 {"content-type": "application/json", "api-key": os.environ["QDRANT_API_KEY"]})
    return json.load(urllib.request.urlopen(req, timeout=120))["result"]


def points(doc_ids):
    """Every point of these papers (scroll with a doc_id filter)."""
    offset = None
    while True:
        body = {"limit": 256, "with_payload": ["doc_id", "node_id", "pages", "first_page", "text", "content_type"],
                "filter": {"must": [{"key": "doc_id", "match": {"any": doc_ids}}]}}
        if offset is not None:
            body["offset"] = offset
        r = qdrant("/collections/rag-optics/points/scroll", body)
        yield from r["points"]
        offset = r.get("next_page_offset")
        if offset is None:
            return


def judge(p):
    import subq
    pl = p["payload"]
    text = str(pl.get("text", ""))[:2500]
    body = {"model": "subq-snap-preview", "state": f"Passage from a scientific paper on optical crystals:\n\n{text}",
            "questions": {k: {"type": "noul", "instructions": q} for k, q in QUESTIONS.items()}}
    out = subq.ask(body)
    return {"node": pl.get("node_id"), "doc": pl.get("doc_id"), "pages": pl.get("pages"), "type": pl.get("content_type"),
            "f": formulas(text), "s": {k: round(v, 3) for k, v in (out or {}).items()}}


def shard(k, n, path):
    docs = sorted(p["doc_id"] for p in json.loads((ROOT / "web/src/papers.json").read_text(encoding="utf-8")))
    mine = [d for i, d in enumerate(docs) if i % n == k]
    pts = [p for i in range(0, len(mine), 100) for p in points(mine[i:i + 100])]
    print(f"shard {k}/{n}: {len(mine)} papers, {len(pts)} passages", flush=True)
    with ThreadPoolExecutor(16) as ex, open(path, "w", encoding="utf-8") as f:
        for i, row in enumerate(ex.map(judge, pts)):
            f.write(json.dumps(row) + "\n")
            if i % 500 == 0:
                print(i, flush=True)
    import subq
    print(f"done, {subq.tokens[0]:,} input tokens")


def merge(d):
    rows = [json.loads(line) for f in sorted(Path(d).rglob("*.jsonl")) for line in open(f, encoding="utf-8")]
    scored = [r for r in rows if r["s"]]
    out = ROOT / "data/rag-optics/datamap.json.gz"
    with gzip.open(out, "wt", encoding="utf-8") as f:
        json.dump(rows, f, separators=(",", ":"))
    # for each kind of data: how many passages (p > 0.7), and for each crystal named in them, the papers and pages
    by = {k: collections.defaultdict(set) for k in QUESTIONS if k != "junk"}
    for r in scored:
        for k in by:
            if r["s"].get(k, 0) > 0.7:
                for m in r["f"] or ["?"]:
                    by[k][m].add(f"{r['doc']} p{r['pages']}")
    day = dt.date.today().isoformat()
    lines = [f"# Data map {day}", "", f"{len(rows)} passages, {len(scored)} scored by SubQ; junk (p > 0.7): "
             f"{sum(1 for r in scored if r['s'].get('junk', 0) > 0.7)}.", "", "| data | passages (p > 0.7) | crystals named |",
             "|---|---|---|"]
    for k, m in by.items():
        lines.append(f"| {k} | {sum(1 for r in scored if r['s'].get(k, 0) > 0.7)} | {len(m)} |")
    lines += ["", "The full map (every passage, every score, the formulas it names) is data/rag-optics/datamap.json.gz."]
    rep = Path(__file__).parent / "reports" / f"datamap-{day}.md"
    rep.parent.mkdir(exist_ok=True)
    rep.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    if sys.argv[1] == "shard":
        shard(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    else:
        merge(sys.argv[2])
