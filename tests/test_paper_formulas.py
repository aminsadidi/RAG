"""The formulas read from papers (data/rag-optics/paper_formulas.yml) against the values the same
papers report: a mistyped coefficient or a wrong formula form fails here."""

import math
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import brentq

from matrag.references import paper_formulas

DATA = Path(__file__).resolve().parents[1] / "data" / "rag-optics" / "paper_formulas.yml"
PAPERS = paper_formulas.load(DATA)


def curve(material: str, page: str, direction: str):
    for p in PAPERS:
        for e in p["entries"]:
            if p["material"] == material and e["page"] == page and str(e["direction"]) == direction:
                return lambda lam, e=e: float(paper_formulas.evaluate(e, lam))
    raise KeyError((material, page, direction))


@pytest.mark.parametrize("paper", PAPERS, ids=lambda p: f"{p['material']}-{p['doc_id']}")
def test_reported_values(paper):
    """Every value in `checks` (the paper's calculated indices, reference indices) is reproduced."""
    formulas = {str(e["direction"]): e for e in paper["entries"] if e["type"] != "tab"}
    for check in paper.get("checks") or []:
        e = formulas[str(check["direction"])]
        for lam, n in check["points"]:
            assert float(paper_formulas.evaluate(e, lam)) == pytest.approx(n, abs=check["tol"]), (lam, n)


def test_entries_are_well_formed():
    for p in PAPERS:
        assert p["doc_id"] and p["reference"] and p["pdf_page"]
        for e in p["entries"]:
            if e["type"] == "tab":
                lams = [x for x, _ in e["points"]]
                assert lams == sorted(lams) and all(1.2 < n < 3.5 for _, n in e["points"])
            else:
                lo, hi = e["range_um"]
                n = paper_formulas.evaluate(e, np.linspace(lo, hi, 50))
                assert np.all(np.isfinite(n)) and np.all((n > 1.2) & (n < 4.0)), (p["material"], e["page"])


def test_feve_resonance_wavelengths():
    """Fève et al. (2000), Table 1, also lists λ_UV = C^(1/p) and λ_IR = E^(1/q): a check on C, p, E, q."""
    table = {("KTiOAsO4", "x"): (0.205, 8.92), ("KTiOAsO4", "y"): (0.206, 10.18), ("KTiOAsO4", "z"): (0.224, 7.30),
             ("RbTiOAsO4", "x"): (0.217, 28.91), ("RbTiOAsO4", "y"): (0.240, 15.03), ("RbTiOAsO4", "z"): (0.267, 8.20),
             ("CsTiOAsO4", "x"): (0.218, 12.71), ("CsTiOAsO4", "y"): (0.259, 19.29), ("CsTiOAsO4", "z"): (0.288, 6.43)}
    for p in PAPERS:
        if p["doc_id"] != "10.1364_josab.17.000775":
            continue
        for e in p["entries"]:
            _, _, pp, c, _, q, ee = e["coefficients"]
            uv, ir = table[(p["material"], e["direction"])]
            assert c ** (1 / pp) == pytest.approx(uv, abs=0.0015) and ee ** (1 / q) == pytest.approx(ir, abs=0.006)


def test_cdsip2_isotropic_point_and_phase_matching():
    """Kato et al. (2011): no = ne at 0.5143 µm; SHG of 4.7846 µm at 43.13° (type 1), of 5.2955 µm at
    42.77° (type 1) and 76.47° (type 2)."""
    no, ne = curve("CdSiP2", "Kato-2011", "o"), curve("CdSiP2", "Kato-2011", "e")
    assert brentq(lambda lam: no(lam) - ne(lam), 0.45, 0.6) == pytest.approx(0.5143, abs=2e-4)

    def ne_theta(lam, th):
        return 1 / math.sqrt(math.cos(th) ** 2 / no(lam) ** 2 + math.sin(th) ** 2 / ne(lam) ** 2)

    def type1(lam):
        return math.degrees(brentq(lambda t: no(lam) - ne_theta(lam / 2, t), 0.01, 1.57))

    assert type1(4.7846) == pytest.approx(43.13, abs=0.05)
    assert type1(5.2955) == pytest.approx(42.77, abs=0.05)
    lam = 5.2955
    th2 = math.degrees(brentq(lambda t: (no(lam) + ne_theta(lam, t)) / 2 - ne_theta(lam / 2, t), 0.01, 1.57))
    assert th2 == pytest.approx(76.47, abs=0.1)


def test_recob_phase_matching_and_birefringence():
    """Type-I SHG of 1.064 µm in the xz plane: GdCOB 19.7°, TmCOB 32.5° (Liu et al. 2014, Table 5);
    nz − nx at 1.064 µm: GdCOB 0.033, TmCOB 0.043 (Liu et al. 2014, p. 5)."""
    for mat, page, angle, dn in (("GdCa4O(BO3)3", "Aka-1997", 19.7, 0.033), ("TmCa4O(BO3)3", "Liu-2014", 32.5, 0.043)):
        nx, ny, nz = (curve(mat, page, d) for d in "xyz")
        lam = 1.064
        s2 = (ny(lam) ** -2 - nx(lam / 2) ** -2) / (nz(lam / 2) ** -2 - nx(lam / 2) ** -2)
        assert math.degrees(math.asin(math.sqrt(s2))) == pytest.approx(angle, abs=0.1)
        assert nz(lam) - nx(lam) == pytest.approx(dn, abs=6e-4)


def test_tmcob_fit_follows_measured_table():
    for d in "xyz":
        fit = curve("TmCa4O(BO3)3", "Liu-2014", d)
        measured = next(e for p in PAPERS for e in p["entries"]
                        if e["page"] == "Liu-2014 (measured)" and e["direction"] == d)
        assert max(abs(fit(lam) - n) for lam, n in measured["points"]) < 3e-4


def test_lcb_birefringence():
    """Li et al. (2023) quote Δn = 0.053 at 1064 nm for LCB."""
    nx, nz = curve("La2CaB10O19", "Wang-2002", "x"), curve("La2CaB10O19", "Wang-2002", "z")
    assert nz(1.064) - nx(1.064) == pytest.approx(0.053, abs=5e-4)


def test_one_oscillator_coefficients_from_tables():
    """DAST (Jazbinšek 2008, Table I) and DSTMS (Mutter 2007, Table 1) list q, n0, λ0 [nm];
    the file stores n² = n0² + qλ0²/(λ² − λ0²) as type 4 with C1 = n0², C2 = q·λ0², C4 = λ0, C5 = 2."""
    tables = {("DAST", "Jazbinsek-2008"): {"1": (1.645, 2.078, 533), "2": (0.469, 1.585, 504), "3": (0.234, 1.565, 501)},
              ("DSTMS", "Mutter-2007"): {"1": (1.45, 2.026, 532), "2": (0.36, 1.627, 502), "3": (0.11, 1.579, 360)}}
    for (mat, page), rows in tables.items():
        for d, (q, n0, l0) in rows.items():
            fn = curve(mat, page, d)
            for lam in (0.8, 1.064, 1.55):
                expected = math.sqrt(n0 ** 2 + q * (l0 / 1000) ** 2 / (lam ** 2 - (l0 / 1000) ** 2))
                assert fn(lam) == pytest.approx(expected, abs=1e-6)


def test_catalog_for_the_site():
    items = paper_formulas.catalog(DATA)
    mats = {i["material"] for i in items}
    assert {"KTiOAsO4", "CsB3O5", "KBe2BO3F2", "CdSiP2", "YCa4O(BO3)3", "La2CaB10O19", "DAST"} <= mats
    assert all(i["shelf"] == "papers" and i["doc_id"] and i["range_um"][0] < i["range_um"][1] for i in items)
    assert paper_formulas.names(DATA)[("papers", "papers", "KBe2BO3F2")].endswith("(Potassium fluoroboratoberyllate, KBBF)")


def test_dkdp_phase_matching_angles():
    """Kirby & DeShazer (1987) KD*P: the type-I SHG angles Nikogosyan (2005, PDF p. 160) calculates from it
    (1.2 µm: 35.94°, 1.0 µm: 37.47°, 0.8 µm: 43.75°; SFG 1.0642 + 0.5321 µm: 46.82°) and the measured
    type-II SHG angle of 1.0642 µm, 53.5–54° (PDF p. 159)."""
    no, ne = curve("KD2PO4", "Kirby-1987", "o"), curve("KD2PO4", "Kirby-1987", "e")

    def ne_theta(lam, th):
        return 1 / math.sqrt(math.cos(th) ** 2 / no(lam) ** 2 + math.sin(th) ** 2 / ne(lam) ** 2)

    def type1(l1, l2):
        l3 = 1 / (1 / l1 + 1 / l2)
        return math.degrees(brentq(lambda t: no(l1) / l1 + no(l2) / l2 - ne_theta(l3, t) / l3, 0.01, 1.5707))

    for lam, angle in ((1.2, 35.94), (1.0, 37.47), (0.8, 43.75)):
        assert type1(lam, lam) == pytest.approx(angle, abs=0.02)
    assert type1(1.0642, 0.5321) == pytest.approx(46.82, abs=0.02)
    lam = 1.0642
    th2 = math.degrees(brentq(lambda t: (no(lam) + ne_theta(lam, t)) / 2 - ne_theta(lam / 2, t), 0.01, 1.57))
    assert 53.4 < th2 < 54.0


def test_lithium_tantalate_temperature_curves():
    """Abedin & Ito (1996), Fig. 3: from 25 to 300 °C, ne(468 nm) rises from about 2.237 to 2.258 and
    no(468 nm) from 2.232 to 2.236 (the gayer form of thermo_optic.yml, with f_c = 546)."""
    import yaml
    block = next(b for b in yaml.safe_load(open(DATA.parent / "thermo_optic.yml")) if b.get("source") == "Abedin-1996")

    def n(axis, lam, T):
        a, b = block["axes"][axis]["a"], block["axes"][axis]["b"]
        f = (T - 25) * (T + 25 + 546)
        return math.sqrt(a[0] + b[0] * f + (a[1] + b[1] * f) / (lam ** 2 - (a[2] + b[2] * f) ** 2) - a[5] * lam ** 2)

    assert n("e", 0.468, 25) == pytest.approx(2.237, abs=2e-3) and n("e", 0.468, 300) == pytest.approx(2.258, abs=2e-3)
    assert n("o", 0.468, 300) - n("o", 0.468, 25) == pytest.approx(0.0045, abs=1.5e-3)


def test_langatate_shg_tuning_curve():
    """Boursier et al. (2014), LGT type-I SHG (e + e → o) in the (y, z) plane: the slab for 1.34 µm was cut at
    θ = 79° from the fitted tuning curve (p. 3); Fig. 2's fitted curve reaches 90° near 1.30 and 3.27 µm and
    its turning point is at about 55° near 2.05 µm."""
    no, ne = (curve("La3Ga5.5Ta0.5O14", "Boursier-2014", d) for d in "oe")

    def theta(lam):
        s2 = (no(lam / 2) ** -2 - no(lam) ** -2) / (ne(lam) ** -2 - no(lam) ** -2)
        return math.degrees(math.asin(math.sqrt(s2)))
    assert theta(1.34) == pytest.approx(79, abs=1)
    assert min(theta(1.6 + 0.01 * i) for i in range(100)) == pytest.approx(55, abs=1)


def test_bgse_boursier_phase_matching():
    """Boursier et al. (2016), p. 3: NCPM SHG along x at 1.80 µm (type I) and 2.53 µm (type II); p. 4: type-I OPG
    pumped at 2.37 µm, degenerate at 4.74 µm, at θ = 41° in the (x, z) plane."""
    nx, ny, nz = (curve("BaGa4Se7", "Boursier-2016", d) for d in "xyz")
    assert brentq(lambda lam: nz(lam) - ny(lam / 2), 1.5, 2.2) == pytest.approx(1.80, abs=0.01)
    assert brentq(lambda lam: (ny(lam) + nz(lam)) / 2 - ny(lam / 2), 2.2, 3.0) == pytest.approx(2.53, abs=0.04)

    def ne(lam, t):
        return (math.cos(t) ** 2 / nx(lam) ** 2 + math.sin(t) ** 2 / nz(lam) ** 2) ** -0.5
    t = brentq(lambda t: ny(2.37) / 2.37 - 2 * ne(4.74, t) / 4.74, math.radians(20), math.radians(60))
    assert math.degrees(t) == pytest.approx(41, abs=0.6)


@pytest.mark.parametrize("material, cases", [
    # Dmitriev, Gurzadyan, Nikogosyan (1999): calculated θpm of o + o ⇒ e SHG (and SFG) from the same equations
    ("NH4D2PO4", [(1.0642, None, 36.93), (0.5321, None, 79.53), (1.0642, 0.5321, 46.44)]),
    ("RbH2PO4", [(1.0642, None, 51.08), (0.6328, None, 81.31), (1.0642, 0.5321, 60.86)]),
    ("RbD2PO4", [(1.0642, None, 47.19), (0.6328, None, 81.66), (1.0642, 0.5321, 60.01)]),
    ("KH2AsO4", [(1.0642, None, 41.89), (0.6328, None, 74.64), (1.0642, 0.5321, 54.29)]),
    ("NH4H2AsO4", [(1.0642, None, 41.71), (0.6328, None, 67.42), (1.0642, 0.5321, 53.05)]),
    ("NH4D2AsO4", [(1.0642, None, 39.04), (0.6328, None, 68.11), (1.0642, 0.5321, 52.89)]),
    ("RbH2AsO4", [(1.0642, None, 49.52), (0.6943, None, 79.06), (1.0642, 0.5321, 67.35)]),
    ("RbD2AsO4", [(1.0642, None, 46.62), (1.3188, None, 42.98), (1.0642, 0.5321, 69.79)]),
    ("BeSO4·4H2O", [(1.0642, None, 41.88), (0.6943, None, 50.32), (1.0642, 0.3547, 62.50)]),
])
def test_dmitriev_kdp_isomorphs(material, cases):
    no, ne = curve(material, "Dmitriev-1999", "o"), curve(material, "Dmitriev-1999", "e")

    def ne_theta(lam, th):
        return (math.cos(th) ** 2 / no(lam) ** 2 + math.sin(th) ** 2 / ne(lam) ** 2) ** -0.5
    for l1, l2, theta in cases:
        l2 = l2 or l1
        l3 = 1 / (1 / l1 + 1 / l2)
        t = brentq(lambda t: no(l1) / l1 + no(l2) / l2 - ne_theta(l3, t) / l3, 0.01, 1.5707)
        assert math.degrees(t) == pytest.approx(theta, abs=0.03), (l1, l2)


def test_kb5_xy_plane_shg():
    """Dmitriev et al. (1999), p. 144: type-I SHG in the XY plane (book frame), φtheor = 80.4°, 54.1°, 32.8° at
    0.4384, 0.50, 0.630 µm (column 3.402). Book X, Y, Z = z, y, x here; the second harmonic is polarized along
    the book's Z (x here), the fundamental in the XY plane at φ from X."""
    nx, ny, nz = (curve("KB5O8·4H2O", "Dmitriev-1999", d) for d in "xyz")
    for lam, phi in ((0.4384, 80.4), (0.50, 54.1), (0.630, 32.8)):
        def n_phi(p):  # wave in the book's XY plane, direction at φ from X, polarized in the plane
            return (math.cos(p) ** 2 / ny(lam) ** 2 + math.sin(p) ** 2 / nz(lam) ** 2) ** -0.5
        p = brentq(lambda p: n_phi(p) - nx(lam / 2), 0.01, 1.5707)
        assert math.degrees(p) == pytest.approx(phi, abs=0.2), lam
