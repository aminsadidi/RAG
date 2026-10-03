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
