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


def isotropic_sources(entries: list[dict]) -> list[dict]:
    """Each index set of an optically isotropic (cubic) crystal as a source with o = e, for quasi-phase
    matching in orientation-patterned crystals (OP-GaAs, OP-GaP): no birefringent solution exists."""
    out = [{"label": e["page"], "kind": "uniaxial", "isotropic": True, "range_um": list(e["range_um"]),
            "axes": {a: {k: e[k] for k in KEEP if k in e} for a in ("o", "e")}}
           for e in entries if not e.get("direction") and e["range_um"][1] > e["range_um"][0]]
    # formulas first, then the sets covering most of the 1–12 µm range where these crystals are used
    cover = lambda s: max(0.0, min(s["range_um"][1], 12.0) - max(s["range_um"][0], 1.0))
    return sorted((s for s in out if cover(s) > 0), key=lambda s: (s["axes"]["o"]["type"] == "tab", -cover(s)))


def build(out: Path, thermo_path: Path | None = None, isotropic: tuple[str, ...] = ()) -> int:
    """Write ``aniso.json`` next to the site's ``index.json``; returns the number of crystals.

    A crystal listed on several shelves (e.g. LBO in refractiveindex.info and in the papers of the
    collection) is one entry with all its sources. ``thermo_path`` (thermo_optic.yml) adds the
    temperature dependence to the sources it names. ``isotropic`` names cubic crystals (from the
    main shelf) added for quasi-phase matching."""
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    crystals: dict[str, dict] = {}
    for m in index:
        if m["shelf"] == "specs":
            continue
        found = sources(json.loads((out / "m" / f"{m['i']}.json").read_text(encoding="utf-8")))
        if not found and m["material"] in isotropic and m["shelf"] == "main":
            found = isotropic_sources(json.loads((out / "m" / f"{m['i']}.json").read_text(encoding="utf-8")))
        if not found:
            continue
        if m["material"] in crystals:
            crystals[m["material"]]["sources"] += found
        else:
            crystals[m["material"]] = {"material": m["material"], "name": m.get("name", ""), "shelf": m["shelf"],
                                       "group": m["group"], "sources": found}
    if thermo_path is not None and thermo_path.exists():
        add_thermo(crystals, thermo_path)
    (out / "aniso.json").write_text(json.dumps(list(crystals.values()), ensure_ascii=False, separators=(",", ":")),
                                    encoding="utf-8")
    return len(crystals)


def add_thermo(crystals: dict[str, dict], path: Path) -> None:
    """Attach each block of thermo_optic.yml to its source (``thermo`` on the source, the per-axis
    formula on each axis); a block marked ``prefer`` puts its source first."""
    import yaml

    for block in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
        crystal = crystals.get(block["material"])
        src = next((s for s in crystal["sources"] if s["label"] == block["source"]), None) if crystal else None
        if src is None:
            raise ValueError(f"thermo_optic.yml: no source {block['source']!r} of {block['material']}")
        if set(block["axes"]) != set(src["axes"]):
            raise ValueError(f"thermo_optic.yml: {block['material']} axes {sorted(block['axes'])} "
                             f"do not match the source's {sorted(src['axes'])}")
        src["thermo"] = {k: block[k] for k in ("form", "t0_c", "cite", "doc_id", "pdf_page", "where") if k in block}
        for axis, spec in block["axes"].items():
            src["axes"][axis]["thermo"] = spec
        if block.get("prefer"):
            crystal["sources"].remove(src)
            crystal["sources"].insert(0, src)


CUBIC = ("-43m", "43m", "23", "432")


def cubic_crystals(path: Path) -> tuple[str, ...]:
    """The crystals of nonlinear_coefficients.yml with a cubic point group."""
    import yaml

    rows = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else []
    return tuple(r["material"] for r in rows or [] if str(r["point_group"]) in CUBIC)


def build_nonlinear(out: Path, path: Path) -> int:
    """Write ``dij.json`` (the nonlinear coefficients of data/<corpus>/nonlinear_coefficients.yml) next
    to ``aniso.json``; returns the number of crystals."""
    import yaml

    rows = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else []
    for r in rows or []:
        for s in r["sources"]:
            # YAML reads an unquoted id of digits, dots and '_' as a number (10.1088_1464_4258_10_10_104011)
            if "doc_id" in s and not isinstance(s["doc_id"], str):
                raise ValueError(f"{r['material']}: quote the doc_id {s['doc_id']!r} in {path.name}")
    data = {r["material"]: {"point_group": str(r["point_group"]), "d": {str(k): float(v) for k, v in r["d"].items()},
                            "sources": r["sources"], "notes": r.get("notes", "")} for r in rows or []}
    (out / "dij.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(data)
