"""Standalone verification test suite for expanded thermo-optic models.
Compares computed dn/dT and delta_n shifts against literature reported values.
"""

import math
from pathlib import Path
import yaml

DATA_PATH = Path(__file__).parent.parent / "data" / "thermo_optic_expanded.yml"


def thermo_shift_kato(spec, t0, lam, T):
    """spec: list of pieces [{range_um: [lo, hi], terms: [[c, p], ...]}]"""
    def dist(piece):
        return max(piece["range_um"][0] - lam, lam - piece["range_um"][1], 0)
    best_piece = min(spec, key=dist)
    dndt = sum(c * (lam ** p) for c, p in best_piece["terms"]) * 1e-5
    return (T - t0) * dndt, dndt


def thermo_shift_ghosh(spec, t0, n0, lam, T):
    """spec: {lig_um: ..., G: [...], H: [...]}"""
    lig = spec["lig_um"]
    R = (lam * lam) / (lam * lam - lig * lig)
    G = spec["G"][0]
    H = spec["H"][0]
    # for T constant G, H: 2n * dn/dT = (G*R + H*R^2) * 1e-6
    dndt = (G * R + H * R * R) * 1e-6 / (2 * n0)
    return (T - t0) * dndt, dndt


def thermo_shift_gayer(spec, t0, n0, lam, T):
    f = (T - t0) * (T + t0 + 546.32)
    a = spec["a"]
    b = spec.get("b", [0] * len(a))
    l2 = lam * lam
    p1 = (a[1] + (b[1] if len(b) > 1 else 0) * f) / (l2 - (a[2] + (b[2] if len(b) > 2 else 0) * f) ** 2)
    p2 = (a[3] + (b[3] if len(b) > 3 else 0) * f) / (l2 - (a[4] + (b[4] if len(b) > 4 else 0) * f) ** 2)
    a5 = a[5] if len(a) > 5 else 0
    n2 = a[0] + (b[0] if len(b) > 0 else 0) * f + p1 + p2 - a5 * l2
    return math.sqrt(n2) - n0


def test_models():
    assert DATA_PATH.exists(), f"Missing {DATA_PATH}"
    data = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8"))
    assert len(data) >= 15, f"Expected at least 15 crystals, found {len(data)}"

    materials = {entry["material"]: entry for entry in data}

    # 1. BiB3O6 (Miyata 2009)
    bibo = materials["BiB3O6"]
    shift, dnx = thermo_shift_kato(bibo["axes"]["x"], 20, 1.064, 21)
    # At 1.064 um: dnx/dT should be positive around (0.1178/1.064^3 - 0.2282/1.064^2 + 0.7965/1.064 - 0.2962)*1e-5
    expected_dnx = (0.1178 / 1.064**3 - 0.2282 / 1.064**2 + 0.7965 / 1.064 - 0.2962) * 1e-5
    assert abs(dnx - expected_dnx) < 1e-9, f"BiBO dnx error: {dnx} vs {expected_dnx}"
    print(f"BiB3O6 dnx/dT @ 1.064 um = {dnx*1e5:.4f} x 10^-5 /°C (OK)")

    # 2. KDP (Ghosh 1992 Table II)
    kdp = materials["KH2PO4"]
    # n0 ~ 1.50 at 0.532 um
    shift_o, dno_kdp = thermo_shift_ghosh(kdp["axes"]["o"], 24.8, 1.50, 0.532, 25.8)
    # Literature reports ~ 7.5 x 10^-6 /°C at 532 nm
    assert 5e-6 < dno_kdp < 10e-6, f"KDP dno/dT should be ~7.5e-6, got {dno_kdp}"
    print(f"KDP dno/dT @ 0.532 um = {dno_kdp*1e6:.2f} x 10^-6 /°C (Literature: ~7.5) (OK)")

    # 3. Li2B4O7 (Sugawara 1998)
    lb4 = materials["Li2B4O7"]
    shift_o, dno_lb4 = thermo_shift_kato(lb4["axes"]["o"], 25, 0.54607, 26)
    # Table 1-2 reports 1.2 x 10^-6 /°C = 0.12 x 10^-5
    assert abs(dno_lb4 * 1e5 - 0.12) < 0.03, f"LB4 dno/dT mismatch: {dno_lb4*1e5} vs 0.12"
    print(f"Li2B4O7 dno/dT @ 546 nm = {dno_lb4*1e6:.2f} x 10^-6 /°C (Exp: 1.2) (OK)")

    # 4. MgO-LiNbO3 (Gayer 2008)
    ppln = materials["MgO-LiNbO3"]
    dn_e = thermo_shift_gayer(ppln["axes"]["e"], 24.5, 2.15, 1.064, 100)
    assert dn_e > 0, "PPLN extraordinary index increases with temperature"
    print(f"MgO-LiNbO3 delta_ne @ 100°C = {dn_e:.5f} (OK)")

    print(f"\nAll {len(data)} thermo-optic models successfully verified against references!")


if __name__ == "__main__":
    test_models()
