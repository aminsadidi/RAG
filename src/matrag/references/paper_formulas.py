"""Dispersion formulas and measured indices read from papers of the collection.

refractiveindex.info has no data for several crystals the collection covers (KTA, CBO, KBBF, CdSiP2,
the ReCOB family, LCB, DAST, ...). ``data/<corpus>/paper_formulas.yml`` holds their formulas and
measured index tables as printed in those papers, each with the paper's own reference values
(``checks``). They are shown in the site's refractive index tab next to the database entries.
"""

from pathlib import Path

import numpy as np
import yaml

from matrag.dispersion import refractiveindex_info

SHELF = "papers"


def load(path: Path) -> list[dict]:
    """The papers of the file, as written (with their ``entries`` and ``checks``)."""
    if not path.exists():
        return []
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def evaluate(entry: dict, wavelength_um) -> np.ndarray:
    """n(λ) of one entry: its formula, or linear interpolation in its measured points."""
    if entry["type"] == "tab":
        pts = np.asarray(entry["points"], dtype=float)
        return np.interp(wavelength_um, pts[:, 0], pts[:, 1], left=np.nan, right=np.nan)
    return refractiveindex_info(int(entry["type"]), entry["coefficients"], wavelength_um)


def catalog(path: Path) -> list[dict]:
    """The entries in the format of ``refractiveindex.formula_catalog`` (one per curve), for the site."""
    out = []
    for paper in load(path):
        for e in paper["entries"]:
            item = {
                "shelf": SHELF, "group": SHELF, "material": paper["material"], "page": e["page"],
                "direction": str(e.get("direction") or ""), "reference": paper["reference"],
                "doi": paper.get("doi"), "doc_id": paper["doc_id"], "path": None,
                "source": "paper", "pdf_page": paper.get("pdf_page"), "where": paper.get("where", ""),
            }
            if e["type"] == "tab":
                pts = sorted([float(x), float(n)] for x, n in e["points"])
                item |= {"type": "tab", "points": pts, "range_um": [pts[0][0], pts[-1][0]]}
            else:
                item |= {"type": int(e["type"]), "coefficients": [float(c) for c in e["coefficients"]],
                         "range_um": [float(x) for x in e["range_um"]]}
            out.append(item)
    return out


def names(path: Path) -> dict[tuple[str, str, str], str]:
    """Display names, keyed like ``refractiveindex.book_names``."""
    return {(SHELF, SHELF, p["material"]): p["name"] for p in load(path) if p.get("name")}


def add_to_site(out: Path, path: Path) -> int:
    """Add the paper entries to the site's refractive index files (``index.json`` and ``m/<i>.json``
    in ``out``, as written by ``matrag export-formulas``), replacing any added before. Returns the
    number of materials added."""
    import json

    index_file = out / "index.json"
    index = [m for m in json.loads(index_file.read_text(encoding="utf-8")) if m["shelf"] != SHELF]
    groups: dict[str, list[dict]] = {}
    for item in catalog(path):
        groups.setdefault(item["material"], []).append(item)
    label = names(path)
    first = max((m["i"] for m in index), default=-1) + 1
    for k in range(first, first + 1000):  # files of a previous run
        (out / "m" / f"{k}.json").unlink(missing_ok=True)
    for i, (material, items) in enumerate(sorted(groups.items()), start=first):
        (out / "m" / f"{i}.json").write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        index.append({"i": i, "shelf": SHELF, "group": SHELF, "material": material,
                      **({"name": label[(SHELF, SHELF, material)]} if (SHELF, SHELF, material) in label else {}),
                      "n": len(items), "formulas": sum(e["type"] != "tab" for e in items),
                      "range_um": [min(e["range_um"][0] for e in items), max(e["range_um"][1] for e in items)]})
    index_file.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(groups)
