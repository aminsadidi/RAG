"""Standalone verification tests for the Quantum SPDC engine.
Validates JSA generation, Schmidt purity, Hong-Ou-Mandel interference,
and spatial mode matching against Evans (2010) and Bennink (2010) benchmarks.
"""

import math
import numpy as np
from pathlib import Path
import sys

# Add parent directory to sys.path so modules can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.spdc.jsa_engine import GaussianPump, PhaseMatchingFunction, JSAEngine
from modules.spdc.schmidt import SchmidtDecomposition, schmidt_purity
from modules.spdc.hom_dip import HongOuMandelDip
from modules.spdc.spatial_modes import SpatialModeCoupling


def test_evans_benchmark():
    """Validates the PPKTP engineered factorable state benchmark of Evans et al. (2010)."""
    # Evans (2010): 776 nm Ti:Sapphire pump with 1.3 ps pulse (~0.68 nm FWHM),
    # L = 20 mm PPKTP, down-conversion to 1552 nm telecom band.
    pump = GaussianPump(central_wavelength_um=0.776, fwhm_nm=0.68)
    # Group indices of KTP near 776 nm and 1552 nm:
    # ng_p(y) = 1.811, ng_s(y) = 1.767, ng_i(z) = 1.852 (Type-II)
    pm = PhaseMatchingFunction(
        length_mm=20.0,
        ng_p=1.811,
        ng_s=1.767,
        ng_i=1.852,
        poling_period_um=46.2,
    )

    engine = JSAEngine(pump=pump, pm=pm, signal_lam0_um=1.552, idler_lam0_um=1.552)
    res = engine.compute_jsa(signal_span_nm=15.0, idler_span_nm=15.0, n_points=120)

    # Schmidt decomposition
    schmidt = SchmidtDecomposition(res["jsa"])
    purity = schmidt.purity
    k_number = schmidt.schmidt_number

    print(f"Evans (2010) PPKTP simulation:")
    print(f"  Calculated Purity P = {purity:.4f} (Reported: 0.81 ± 0.02)")
    print(f"  Schmidt number K = {k_number:.3f}")
    assert abs(purity - 0.81) < 0.04, f"Purity {purity} outside expected range around 0.81"

    # HOM test: For factorable states, interference between independent heralded photons
    # yields visibility equal to purity (Mosley 2008, Evans 2010)
    hom = HongOuMandelDip(res)
    indep_vis = hom.independent_heralded_visibility()
    print(f"  Independent Photon HOM Visibility = {indep_vis*100:.1f}% (Purity: {purity*100:.1f}%)")
    assert abs(indep_vis - purity) < 1e-4, "Independent photon visibility must equal purity"
    assert 0.77 <= indep_vis <= 0.85, f"Independent visibility {indep_vis} outside expected range"


def test_hom_symmetry():
    """Checks that a completely symmetric state yields 100% HOM visibility."""
    pump = GaussianPump(central_wavelength_um=0.405, fwhm_nm=1.0)
    # Symmetric group indices for degenerate Type-I: ng_s = ng_i
    pm = PhaseMatchingFunction(length_mm=5.0, ng_p=1.80, ng_s=1.65, ng_i=1.65)
    engine = JSAEngine(pump=pump, pm=pm, signal_lam0_um=0.810, idler_lam0_um=0.810)
    res = engine.compute_jsa(signal_span_nm=20.0, idler_span_nm=20.0, n_points=80)

    hom = HongOuMandelDip(res)
    delays = np.linspace(-300, 300, 61)
    dip_res = hom.compute_dip_curve(delays)

    assert abs(dip_res["pair_visibility"] - 1.0) < 0.02, "Symmetric state must have ~100% visibility"
    assert dip_res["dip_minimum"] < 0.05, "Coincidence at zero delay must drop to near zero"
    print(f"Symmetric HOM Dip: V = {dip_res['pair_visibility']*100:.2f}%, P_min = {dip_res['dip_minimum']:.4f} (OK)")


def test_spatial_mode_coupling():
    """Validates fiber coupling and Bennink (2010) optimal waist condition."""
    # Bennink (2010): optimal collection waist is wc = sqrt(2) * wp
    wp = 50.0  # um
    wc_opt = wp * math.sqrt(2.0)
    wc_subopt = wp * 0.5

    coupler_opt = SpatialModeCoupling(
        pump_waist_um=wp,
        collection_waist_um=wc_opt,
        crystal_length_mm=10.0,
        refractive_index=1.8,
        pump_wavelength_um=0.405,
    )
    eta_opt = coupler_opt.heralding_efficiency()

    coupler_subopt = SpatialModeCoupling(
        pump_waist_um=wp,
        collection_waist_um=wc_subopt,
        crystal_length_mm=10.0,
        refractive_index=1.8,
        pump_wavelength_um=0.405,
    )
    eta_subopt = coupler_subopt.heralding_efficiency()

    print(f"Spatial Mode Coupling:")
    print(f"  Optimal heralding efficiency (wc = sqrt(2)*wp): {eta_opt*100:.1f}%")
    print(f"  Suboptimal heralding efficiency (wc = 0.5*wp):    {eta_subopt*100:.1f}%")
    assert eta_opt > eta_subopt, "Optimal waist must yield higher heralding efficiency"
    assert eta_opt > 0.80, f"Expected eta_opt > 80%, got {eta_opt}"
    print("Spatial mode coupling verified (OK)")


if __name__ == "__main__":
    print("Running Quantum SPDC Engine Verification Suite...")
    test_evans_benchmark()
    test_hom_symmetry()
    test_spatial_mode_coupling()
    print("\nALL QUANTUM SPDC TESTS PASSED!")
