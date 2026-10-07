"""Verification Tests for Birefringent Phase Matching & QPM Engine.
Validates Fresnel equation, BBO SHG angle, KDP/BBO/PPLN d_eff, and QPM periods
against established literature benchmarks (Eckardt 1990, Gayer 2008, Evans 2010).
"""

import math
import numpy as np
from pathlib import Path
import sys

# Ensure parent directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.phase_matching.fresnel import FresnelOptics, propagation_direction
from modules.phase_matching.deff import EffectiveNonlinearCoefficient, compute_deff
from modules.phase_matching.bpm import PhaseMatchingSolver, ThreeWaveProcess
from modules.phase_matching.qpm import QPMCalculator


def bbo_sellmeier(lam_um: float):
    """Sellmeier formula for Beta-Barium Borate (BBO) (Eimerl 1987, Kato 1986)."""
    l2 = lam_um ** 2
    no2 = 2.7359 + 0.01878 / (l2 - 0.01822) - 0.01354 * l2
    ne2 = 2.3753 + 0.01224 / (l2 - 0.01667) - 0.01516 * l2
    no = math.sqrt(no2)
    ne = math.sqrt(ne2)
    return no, no, ne


def linbo3_sellmeier_gayer(lam_um: float, temp_c: float = 25.0):
    """Extraordinary index Sellmeier for 5 mol% MgO:LiNbO3 (Gayer 2008)."""
    t_factor = (temp_c - 24.5) * (temp_c + 24.5 + 546.32)
    a1, a2, a3, a4, a5, a6 = 5.756, 0.0983, 0.2020, 189.32, 12.52, 1.32e-2
    b1, b2, b3, b4 = 2.860e-6, 4.700e-8, 6.113e-8, 1.516e-4
    l2 = lam_um ** 2
    ne2 = (
        a1
        + b1 * t_factor
        + (a2 + b2 * t_factor) / (l2 - (a3 + b3 * t_factor) ** 2)
        + (a4 + b4 * t_factor) / (l2 - a5 ** 2)
        - a6 * l2
    )
    return math.sqrt(ne2)


def test_fresnel_optics():
    """Validates Fresnel equation roots for isotropic and uniaxial limits."""
    # 1. Isotropic
    iso = FresnelOptics(1.5, 1.5, 1.5)
    s = propagation_direction("xz", math.radians(45.0))
    ns, nf = iso.eigen_indices(s)
    assert abs(ns - 1.5) < 1e-6 and abs(nf - 1.5) < 1e-6, "Isotropic indices must be degenerate"
    print("Fresnel isotropic verification: OK")

    # 2. Uniaxial BBO
    no, _, ne = bbo_sellmeier(1.064)
    bbo = FresnelOptics(no, no, ne)

    # Optic axis propagation (theta = 0)
    s_axis = propagation_direction("xz", 0.0)
    ns0, nf0 = bbo.eigen_indices(s_axis)
    assert abs(ns0 - no) < 1e-5 and abs(nf0 - no) < 1e-5, "Indices along optic axis must equal no"

    # Perpendicular propagation (theta = 90)
    s_perp = propagation_direction("xz", math.pi / 2.0)
    ns90, nf90 = bbo.eigen_indices(s_perp)
    assert abs(ns90 - no) < 1e-5 and abs(nf90 - ne) < 1e-5, "Perpendicular indices must be no and ne"

    # Walk-off angle
    rho_0 = bbo.spatial_walkoff_angle_rad(0.0)
    rho_90 = bbo.spatial_walkoff_angle_rad(math.pi / 2.0)
    rho_45 = bbo.spatial_walkoff_angle_rad(math.pi / 4.0)
    assert abs(rho_0) < 1e-6 and abs(rho_90) < 1e-6, "Walk-off must vanish at 0 and 90 degrees"
    assert rho_45 > 0.04, f"Walk-off at 45 deg expected ~50-60 mrad, got {rho_45*1000:.1f} mrad"
    print(f"Fresnel BBO walk-off verification: peak walk-off = {rho_45*1000:.2f} mrad (OK)")


def test_bbo_shg_1064nm():
    """Validates 1064 nm Type-I SHG phase matching in BBO against literature theta_pm ~ 22.8 deg."""
    solver = PhaseMatchingSolver(index_fn=bbo_sellmeier)
    process = ThreeWaveProcess("shg", 1.064)
    theta_pm = solver.solve_angle("xz", process, pm_type="Type-I")

    assert theta_pm is not None, "Phase matching angle must exist for BBO 1064 nm SHG"
    print(f"BBO 1064 nm SHG Type-I Phase Matching Angle: {theta_pm:.2f}° (Expected: 22.8°)")
    assert abs(theta_pm - 22.8) < 0.3, f"BBO SHG angle {theta_pm} deviates from 22.8°"

    # Acceptance bandwidths for 10 mm crystal
    bw = solver.compute_bandwidths("xz", theta_pm, process, pm_type="Type-I", length_mm=10.0)
    print(f"  Angular bandwidth:   {bw['delta_theta_mrad']:.2f} mrad (10 mm)")
    print(f"  Spectral bandwidth:  {bw['delta_lambda_nm']:.2f} nm (10 mm)")
    print(f"  Spatial walk-off:    {bw['walkoff_mrad']:.2f} mrad")
    assert 0.2 <= bw["delta_theta_mrad"] <= 2.0, "Angular acceptance out of typical range"
    assert 30.0 <= bw["walkoff_mrad"] <= 70.0, "Spatial walk-off out of typical range"
    print("BBO SHG phase matching and bandwidths: OK")


def test_deff_symmetry_and_values():
    """Validates effective nonlinear coefficient calculations across point groups."""
    # 1. KDP (-42m): d36 = 0.39 pm/V
    # Type-I at theta = 45 deg, phi = 45 deg: deff = d36 * sin(45) * sin(90) = d36 / sqrt(2)
    deff_kdp = compute_deff("-42m", "Type-I", math.radians(45.0), math.radians(45.0), {36: 0.39})
    expected_kdp = 0.39 * math.sin(math.radians(45.0))
    assert abs(deff_kdp - expected_kdp) < 1e-5, "KDP d_eff Type-I failed"
    print(f"KDP (-42m) Type-I d_eff: {deff_kdp:.4f} pm/V (OK)")

    # 2. BBO (3m): d22 = 2.2 pm/V, d31 = 0.1 pm/V
    # Type-I at theta = 22.8 deg, phi = 90 deg: deff = d31*sin(22.8) + d22*cos(22.8)
    deff_bbo = compute_deff("3m", "Type-I", math.radians(22.8), math.radians(90.0), {22: 2.2, 31: 0.1})
    expected_bbo = 0.1 * math.sin(math.radians(22.8)) + 2.2 * math.cos(math.radians(22.8))
    assert abs(deff_bbo - expected_bbo) < 1e-4, "BBO d_eff Type-I failed"
    print(f"BBO (3m) Type-I d_eff: {deff_bbo:.4f} pm/V (OK)")

    # 3. PPLN QPM: d33 = 27.2 pm/V -> deff = (2/pi) * 27.2 = 17.316 pm/V
    deff_ppln = compute_deff("qpm", "Type-I", 0.0, 0.0, {33: 27.2})
    expected_ppln = (2.0 / math.pi) * 27.2
    assert abs(deff_ppln - expected_ppln) < 1e-4, "QPM 1st-order d_eff failed"
    print(f"PPLN QPM d_eff: {deff_ppln:.4f} pm/V (OK)")


def test_qpm_ppln_gayer():
    """Validates PPLN 1064 nm SHG poling period against Gayer et al. (2008) ~ 6.97 µm."""
    qpm = QPMCalculator(
        material="mgo-linbo3",
        index_fn=linbo3_sellmeier_gayer,
        t0_c=25.0,
    )
    # SHG: pump 0.532 µm, fundamental 1.064 µm
    period_25c = qpm.calculate_period_um(lam_pump_um=0.532, lam_signal_um=1.064, temperature_c=25.0)
    period_100c = qpm.calculate_period_um(lam_pump_um=0.532, lam_signal_um=1.064, temperature_c=100.0)

    print(f"PPLN 1064 nm SHG Poling Period @ 25°C:  {period_25c:.3f} µm (Literature: 6.97 µm)")
    print(f"PPLN 1064 nm SHG Poling Period @ 100°C: {period_100c:.3f} µm (Literature: 6.84 µm)")

    assert abs(period_25c - 6.97) < 0.05, f"PPLN period {period_25c} deviates from 6.97 µm"
    assert abs(period_100c - 6.84) < 0.05, f"PPLN period {period_100c} deviates from 6.84 µm"
    print("PPLN QPM poling period benchmark: OK")


if __name__ == "__main__":
    print("Running Phase Matching & QPM Engine Verification Suite...")
    test_fresnel_optics()
    test_bbo_shg_1064nm()
    test_deff_symmetry_and_values()
    test_qpm_ppln_gayer()
    print("\nALL PHASE MATCHING & QPM TESTS PASSED!")
