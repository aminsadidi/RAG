"""The birefringent crystals of the site's refractive index data, for its phase-matching calculator.

A "source" is one paper's complete set of principal indices: o and e for a uniaxial crystal, x, y, z
(also written α, β, γ or 1, 2, 3) for a biaxial one. ``aniso.json`` holds every such set, with the
curves themselves, so the calculator can compare all crystals without fetching each material.
"""

import json
import re
from pathlib import Path

AXIS = {"o": "o", "e": "e", "x": "x", "y": "y", "z": "z", "alpha": "x", "beta": "y", "gamma": "z",
        "1": "x", "2": "y", "3": "z"}
KEEP = ("type", "coefficients", "points", "range_um", "reference", "doc_id", "doi", "page", "direction")


def sources(entries: list[dict]) -> list[dict]:
    """Complete sets of principal indices among one material's entries (first entry per axis)."""
    groups: dict[str, dict[str, dict]] = {}
    for e in entries:
        axis = AXIS.get(str(e.get("direction") or "").lower())
        if not axis:
            continue
        # refractiveindex.info names pages after the axis ("Eimerl-o"); a paper entry keeps it apart
        page, d = e["page"], str(e["direction"])
        key = page[: -len(d) - 1] if re.search(rf"[-_ ]{re.escape(d)}$", page, re.IGNORECASE) else page
        groups.setdefault(key, {}).setdefault(axis, e)
    out = []
    for label, axes in groups.items():
        if {"o", "e"} <= axes.keys():
            kind, used = "uniaxial", {"o": axes["o"], "e": axes["e"]}
        elif {"x", "y", "z"} <= axes.keys():
            kind, used = "biaxial", {a: axes[a] for a in "xyz"}
        else:
            continue
        lo = max(e["range_um"][0] for e in used.values())
        hi = min(e["range_um"][1] for e in used.values())
        if hi <= lo:
            continue
        out.append({"label": label, "kind": kind, "range_um": [lo, hi],
                    "axes": {a: {k: e[k] for k in KEEP if k in e} for a, e in used.items()}})
    # formulas before measured tables, then the widest range
    out.sort(key=lambda s: (any(e["type"] == "tab" for e in s["axes"].values()), -(s["range_um"][1] - s["range_um"][0])))
    return out


def build(out: Path) -> int:
    """Write ``aniso.json`` next to the site's ``index.json``; returns the number of crystals."""
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    crystals = []
    for m in index:
        if m["shelf"] == "specs":
            continue
        found = sources(json.loads((out / "m" / f"{m['i']}.json").read_text(encoding="utf-8")))
        if found:
            crystals.append({"material": m["material"], "name": m.get("name", ""), "shelf": m["shelf"],
                             "group": m["group"], "sources": found})
    (out / "aniso.json").write_text(json.dumps(crystals, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(crystals)


def build_nonlinear(out: Path, path: Path) -> int:
    """Write ``dij.json`` (the nonlinear coefficients of data/<corpus>/nonlinear_coefficients.yml) next
    to ``aniso.json``; returns the number of crystals."""
    import yaml

    rows = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else []
    data = {r["material"]: {"point_group": str(r["point_group"]), "d": {str(k): float(v) for k, v in r["d"].items()},
                            "sources": r["sources"], "notes": r.get("notes", "")} for r in rows or []}
    (out / "dij.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(data)
