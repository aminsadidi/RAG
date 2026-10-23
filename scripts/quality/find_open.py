"""Papers outside the collection that may hold the data a crystal lacks: OpenAlex finds open-access works that name the
crystal, SubQ reads each abstract and says how likely the authors measured that kind of data. Writes a CSV of links and
scores only (doi, crystal, kind, p, pdf, title) for the reader (Gemini) that extracts the numbers from the PDFs.

    python scripts/quality/find_open.py OUT.csv "KBe2BO3F2:dndt" "CuGaS2:dij" ...   (SUBQ_KEYS, OPENALEX_API_KEY)
"""
import csv
import json
import os
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import subq  # noqa: E402

WHAT = {
    "dndt": ("thermo-optic", "the temperature dependence of its refractive indices (dn/dT, thermo-optic coefficients or a "
                             "temperature-dependent Sellmeier equation)"),
    "dij": ("nonlinear coefficient", "absolute values of its second-order nonlinear coefficients d_ij in pm/V (not only a "
                                     "powder SHG intensity relative to KDP)"),
    "sellmeier": ("Sellmeier", "its refractive indices at several wavelengths or Sellmeier (dispersion) equations"),
}


def get(url):
    try:
        req = urllib.request.Request(url, headers={"user-agent": "MatRAG (University of Isfahan)"})
        return json.load(urllib.request.urlopen(req, timeout=60))
    except Exception:  # noqa: BLE001 - a failed lookup only leaves this crystal without candidates
        return {}


def abstract(inv):
    """OpenAlex keeps abstracts as {word: [positions]}."""
    words = sorted((i, w) for w, pos in (inv or {}).items() for i in pos)
    return " ".join(w for _, w in words)


def candidates(crystal, kind, n=25):
    term, _ = WHAT[kind]
    q = urllib.parse.urlencode({"filter": f"is_oa:true,title_and_abstract.search:{crystal}", "search": term, "per-page": n,
                                "select": "doi,display_name,abstract_inverted_index,best_oa_location,locations",
                                **({"api_key": os.environ["OPENALEX_API_KEY"]} if os.environ.get("OPENALEX_API_KEY") else {})})
    out = []
    for w in get(f"https://api.openalex.org/works?{q}").get("results", []):
        pdfs = [loc["pdf_url"] for loc in w.get("locations") or [] if loc.get("is_oa") and loc.get("pdf_url")]
        if w.get("doi") and pdfs:
            out.append({"doi": w["doi"].replace("https://doi.org/", ""), "title": w.get("display_name") or "",
                        "abstract": abstract(w.get("abstract_inverted_index")), "pdf": pdfs[0]})
    return out


def judge(crystal, kind, c):
    text = f"{c['title']}\n\n{c['abstract']}"[:3000]
    p = subq.score(f"Title and abstract of a paper:\n\n{text}", f"Did the authors measure {WHAT[kind][1]} of {crystal}?",
                   "yes, the abstract says they measured it", "no, or only other properties or other crystals")
    return {"doi": c["doi"], "crystal": crystal, "kind": kind, "p": round(p or 0, 3), "pdf": c["pdf"], "title": c["title"]}


def main(out, wants):
    jobs = [(cr, kind, c) for cr, kind in (w.split(":") for w in wants) for c in candidates(cr, kind)]
    with ThreadPoolExecutor(8) as ex:
        rows = sorted(ex.map(lambda j: judge(*j), jobs), key=lambda r: (r["crystal"], -r["p"]))
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["doi", "crystal", "kind", "p", "pdf", "title"])
        w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} candidates, {sum(r['p'] > 0.6 for r in rows)} likely; SubQ tokens {subq.tokens[0]:,} -> {out}")


if __name__ == "__main__":
    assert abstract({"b": [1], "a": [0]}) == "a b"
    main(sys.argv[1], sys.argv[2:])
