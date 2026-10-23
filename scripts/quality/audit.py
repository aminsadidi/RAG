"""Quality audits of the collection and of the site's data with SubQ; each writes scores and ids only (the text stays in
Qdrant), so the four can run at once, each on its own keys.

    python scripts/quality/audit.py verify  OUT.json   # is each value of the site's YAML files in the passage it cites?
    python scripts/quality/audit.py archive OUT.json   # per paper: about optics? the paper its title says? Supporting Information?
    python scripts/quality/audit.py data    OUT.json   # per passage holding data: measured, calculated or reviewed, and are its
                                                       # numbers readable (not reversed, scrambled)? One request per passage
(QDRANT_URL, QDRANT_API_KEY, SUBQ_KEYS; THREADS, default 24)
"""
import gzip
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import subq  # noqa: E402
from basis import QUESTIONS as BASIS  # noqa: E402
from datamap import ROOT, points  # noqa: E402
from hidden_gaps import texts  # noqa: E402

DATA = ROOT / "data/rag-optics"
ANY = ("sellmeier", "ri_table", "dij", "dndt", "pm", "damage", "thermal", "transparency", "bandgap")


def ask(state, questions):
    """{key: probability} for several yes/no questions about one text, in one request."""
    return subq.ask({"model": subq.MODEL, "state": state[:6000],
                     "questions": {k: {"type": "noul", "instructions": q} for k, q in questions.items()}}) or {}


def run(jobs, fn, out):
    with ThreadPoolExecutor(int(os.environ.get("THREADS", 24))) as ex:
        res = [r for r in ex.map(fn, jobs) if r]
    json.dump(res, open(out, "w"), indent=0)
    print(f"{len(res)} results -> {out}; SubQ tokens {subq.tokens[0]:,}; errors {dict(subq.errors)}; keys left {len(subq._keys)}", flush=True)


def pages(p):
    return {int(x) for x in re.findall(r"\d+", str(p.get("pages") or ""))}


# ---------- 1. every value of the calculator against the passage it cites
def claims():
    out = []
    for e in yaml.safe_load(open(DATA / "nonlinear_coefficients.yml")):
        for s in e["sources"]:
            if s.get("doc_id"):
                out.append({"file": "nonlinear", "material": e["material"], "doc": s["doc_id"], "page": s.get("pdf_page"), "claim": s["what"]})
    for f, key in (("paper_formulas", "where"), ("thermo_optic", "where")):
        for e in yaml.safe_load(open(DATA / f"{f}.yml")):
            if e.get("doc_id"):
                out.append({"file": f, "material": e["material"], "doc": e["doc_id"], "page": e.get("pdf_page"), "claim": e.get(key, "")})
    return out


def verify(c):
    pts = [p["payload"] for p in points([c["doc"]], ("node_id", "text", "pages"))]
    near = [p for p in pts if c["page"] and pages(p) & {c["page"] - 1, c["page"], c["page"] + 1}] or pts[:40]
    q = {"q": f"Does this passage state, in its text or a table, the values described here for {c['material']}: "
              f"{str(c['claim'])[:700]}? Answer yes if the passage gives these numbers (rounding and notation may differ)."}
    best = max(((ask(p["text"], q).get("q", 0), p["node_id"]) for p in near), default=(0, None))
    return {**{k: c[k] for k in ("file", "material", "doc", "page")}, "p": round(best[0], 3), "node": best[1], "passages": len(near)}


# ---------- 2. the archive: papers off topic, PDFs of another paper, Supporting Information
def archive(paper):
    pts = sorted((p["payload"] for p in points([paper["doc_id"]], ("node_id", "text"))),
                 key=lambda p: int(str(p["node_id"]).split("::")[-1]) if str(p["node_id"]).split("::")[-1].isdigit() else 0)
    if not pts:
        return None
    text = "\n\n".join(str(p["text"]) for p in pts[:2])[:4000]
    title = re.sub(r"^.*?\(\d{4}\)\.\s*", "", paper.get("reference") or paper.get("citation") or "")[:300]
    q = {"optics": "Is this text about optics or photonics, or about the optical, nonlinear-optical or structural properties of "
                   "crystals or materials?",
         "si": "Is this a Supporting Information or supplementary material document rather than a paper itself?"}
    if paper.get("source_type") == "full_text_pdf" and title:
        q["same"] = f"Is this text from the paper titled: {title}?"
    return {"doc": paper["doc_id"], "type": paper.get("source_type"), **{k: round(v, 3) for k, v in ask(text, q).items()}}


# ---------- 3 and 4. the passages that hold data
def data_nodes(kinds):
    rows = json.load(gzip.open(DATA / "datamap.json.gz"))
    return [r["node"] for r in rows if r["s"] and r["s"].get("junk", 0) <= 0.5 and max(r["s"].get(k, 0) for k in kinds) > 0.7]


def passages(kinds):
    nodes = data_nodes(kinds)
    got = texts(nodes)
    return [got[n] for n in nodes if n in got]


def data(p):
    """Both questions about a passage that holds data in one request: the passage text, most of the tokens, is sent once."""
    q = {**BASIS, "ok": "Are the numbers in this passage readable and in a sensible order: digits not reversed or scrambled, "
                        "table values under the right column headings, signs and powers of ten not lost?"}
    out = ask(f"Passage from a scientific paper on optical crystals:\n\n{p['text']}", q)
    return {"node": p["node_id"], "doc": p["doc_id"], **{k: round(v, 3) for k, v in out.items()}} if out else None


if __name__ == "__main__":
    what, out = sys.argv[1], sys.argv[2]
    if what == "verify":
        run(claims(), verify, out)
    elif what == "archive":
        run(json.loads((ROOT / "web/src/papers.json").read_text(encoding="utf-8")), archive, out)
    elif what == "data":
        run(passages(ANY), data, out)
