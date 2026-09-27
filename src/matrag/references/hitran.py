"""HITRAN as ground truth for line parameters, through the official HAPI library.

HAPI (https://hitran.org/hapi, Kochanov et al. 2016) downloads line lists
from hitran.org without an API key. Extracted values are matched to HITRAN
lines by rotational branch and J (e.g. "R(50)") inside a wavenumber window
the user chooses (that window selects the band); when several lines match,
the strongest one is taken.

HITRAN conventions: half-widths (HWHM) in cm-1/atm and line intensities in
cm-1/(molecule cm-2), both at 296 K. Papers sometimes use other units
(e.g. 10^-3 cm-1/atm, MHz/Torr), so the comparison reports the ratio as well
as the relative difference, and units should be checked by eye.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from matrag.schema import ExtractedRecord

# HITRAN molecule numbers (https://hitran.org/docs/molec-meta/).
MOLECULES = {"H2O": 1, "CO2": 2, "O3": 3, "N2O": 4, "CO": 5, "CH4": 6, "O2": 7, "NO": 8, "SO2": 9,
             "NO2": 10, "NH3": 11, "HNO3": 12, "OH": 13, "HF": 14, "HCl": 15, "N2": 22, "H2S": 31}

# Extracted property name -> HITRAN parameter, first match wins.
_PARAMETERS = [
    (r"temperature|exponent|\bn[_ ]?air\b", "n_air"),
    (r"shift", "delta_air"),
    (r"self", "gamma_self"),
    (r"broaden|half.?width|\bgamma|γ", "gamma_air"),
    (r"intensit|strength", "sw"),
    (r"position|wavenumber|line cent|frequency", "nu"),
]

_BRANCH_J = re.compile(r"\b([PQR])\s*\(?\s*(\d+)\s*\)?")


def hitran_parameter(property_name: str) -> str | None:
    text = property_name.lower()
    return next((param for pattern, param in _PARAMETERS if re.search(pattern, text)), None)


def branch_j(text: str) -> tuple[str, int] | None:
    m = _BRANCH_J.search(text or "")
    return (m.group(1), int(m.group(2))) if m else None


@dataclass
class HitranLine:
    nu: float
    sw: float
    gamma_air: float
    gamma_self: float
    n_air: float
    delta_air: float
    lower_quanta: str
    references: str  # HITRAN reference codes (iref) for nu, sw, gamma_air, gamma_self, n_air, delta_air


def fetch_lines(molecule: str, isotopologue: int, nu_min: float, nu_max: float,
                cache_dir: Path = Path("storage/_hapi")) -> list[HitranLine]:
    import hapi

    cache_dir.mkdir(parents=True, exist_ok=True)
    table = f"{molecule}_{isotopologue}_{nu_min:g}_{nu_max:g}".replace(".", "p")
    hapi.db_begin(str(cache_dir))
    if table not in hapi.tableList():
        hapi.fetch(table, MOLECULES[molecule], isotopologue, nu_min, nu_max)
    cols = ["nu", "sw", "gamma_air", "gamma_self", "n_air", "delta_air", "local_lower_quanta", "iref"]
    return [HitranLine(*(float(v) for v in row[:6]), row[6].strip(), row[7].strip())
            for row in zip(*hapi.getColumns(table, cols))]


def match_line(record: ExtractedRecord, lines: list[HitranLine]) -> HitranLine | None:
    wanted = branch_j(record.spectral_position or "")
    if wanted is None:
        return None
    candidates = [line for line in lines if branch_j(line.lower_quanta) == wanted]
    return max(candidates, key=lambda line: line.sw, default=None)


def compare(records: list[ExtractedRecord], molecule: str, isotopologue: int, nu_min: float, nu_max: float,
            cache_dir: Path = Path("storage/_hapi")) -> list[dict]:
    """Extracted values next to the corresponding HITRAN values."""
    lines = fetch_lines(molecule, isotopologue, nu_min, nu_max, cache_dir)
    rows = []
    for r in records:
        param = hitran_parameter(r.property)
        line = match_line(r, lines) if param else None
        ref = getattr(line, param) if line else None
        rows.append({
            "doc_id": r.doc_id, "pages": r.pages, "property": r.property, "spectral_position": r.spectral_position,
            "broadener": r.broadener, "value": r.value, "unit": r.unit, "hitran_parameter": param or "",
            "hitran_line": line.lower_quanta if line else "", "hitran_nu": line.nu if line else "",
            "hitran_value": ref if ref is not None else "",
            "ratio": round(r.value / ref, 5) if ref else "",
            "abs_diff": f"{r.value - ref:.3g}" if ref is not None else "",
            "rel_diff": f"{(r.value - ref) / ref:.3g}" if ref else "",
        })
    return rows
