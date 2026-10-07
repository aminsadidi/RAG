#!/usr/bin/env python3
"""Command-Line Interface for Birefringent Phase Matching & Quasi-Phase Matching Engine.
Calculates phase matching angles, poling periods, d_eff, and acceptance bandwidths.

Examples:
    python3 research_package/cli_phasematch.py --crystal BBO --process shg --wavelength 1.064
    python3 research_package/cli_phasematch.py --crystal PPLN --qpm --pump 0.532 --signal 1.064 --temp 100
"""

import argparse
import math
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from modules.phase_matching.bpm import PhaseMatchingSolver, ThreeWaveProcess
from modules.phase_matching.qpm import QPMCalculator
from modules.phase_matching.deff import compute_deff
from modules.phase_matching.fresnel import FresnelOptics


def get_crystal_index_fn(crystal_name: str):
    name = crystal_name.upper().strip()
    if name in ("BBO", "BAB2O4"):
        def bbo_indices(lam_um: float):
            l2 = lam_um ** 2
            no = math.sqrt(2.7359 + 0.01878 / (l2 - 0.01822) - 0.01354 * l2)
            ne = math.sqrt(2.3753 + 0.01224 / (l2 - 0.01667) - 0.01516 * l2)
            return no, no, ne
        return bbo_indices, "3m", {22: 2.2, 31: 0.1}

    elif name in ("KDP", "KH2PO4"):
        def kdp_indices(lam_um: float):
            l2 = lam_um ** 2
            no = math.sqrt(2.259276 + 0.01008956 / (l2 - 0.012942625) - 0.001349 * l2)
            ne = math.sqrt(2.132668 + 0.008637494 / (l2 - 0.012281043) - 0.003200 * l2)
            return no, no, ne
        return kdp_indices, "-42m", {36: 0.39}

    elif name in ("PPLN", "LINBO3", "MGO-LINBO3"):
        def ln_indices(lam_um: float, temp_c: float = 25.0):
            t_factor = (temp_c - 24.5) * (temp_c + 24.5 + 546.32)
            l2 = lam_um ** 2
            ne2 = (
                5.756 + 2.860e-6 * t_factor
                + (0.0983 + 4.700e-8 * t_factor) / (l2 - (0.2020 + 6.113e-8 * t_factor) ** 2)
                + (189.32 + 1.516e-4 * t_factor) / (l2 - 12.52 ** 2)
                - 1.32e-2 * l2
            )
            return math.sqrt(ne2)
        return ln_indices, "qpm", {33: 27.2}

    else:
        raise ValueError(f"Crystal '{crystal_name}' not yet registered in quick CLI presets. Try BBO, KDP, or PPLN.")


def main():
    parser = argparse.ArgumentParser(description="Phase Matching & QPM Calculator CLI")
    parser.add_argument("--crystal", default="BBO", help="Crystal name (e.g. BBO, KDP, PPLN)")
    parser.add_argument("--process", default="shg", choices=["shg", "sfg", "opo", "dfg", "spdc"])
    parser.add_argument("--wavelength", type=float, default=1.064, help="Fundamental / Signal wavelength in µm")
    parser.add_argument("--pump", type=float, default=0.532, help="Pump wavelength in µm (for OPO/SPDC/QPM)")
    parser.add_argument("--plane", default="xz", choices=["xz", "yz", "xy"], help="Principal plane")
    parser.add_argument("--type", default="Type-I", choices=["Type-I", "Type-II"], help="Phase matching type")
    parser.add_argument("--qpm", action="store_true", help="Calculate Quasi-Phase Matching period")
    parser.add_argument("--temp", type=float, default=25.0, help="Crystal temperature in °C")
    parser.add_argument("--length", type=float, default=10.0, help="Crystal length in mm")

    args = parser.parse_args()

    print("=" * 60)
    print("PHASE MATCHING & QPM CALCULATOR")
    print("=" * 60)
    print(f"Crystal:       {args.crystal.upper()}")
    print(f"Process:       {args.process.upper()}")
    print(f"Temperature:   {args.temp:.1f} °C")
    print(f"Crystal Length:{args.length:.1f} mm")

    index_fn, pg, d_dict = get_crystal_index_fn(args.crystal)

    if args.qpm or pg == "qpm":
        # QPM Calculation
        qpm = QPMCalculator(material=args.crystal, index_fn=index_fn, t0_c=args.temp)
        period = qpm.calculate_period_um(lam_pump_um=args.pump, lam_signal_um=args.wavelength, temperature_c=args.temp)
        deff = compute_deff("qpm", "Type-I", 0.0, 0.0, d_dict)
        print("\n--- QUASI-PHASE MATCHING RESULTS ---")
        print(f"Pump Wavelength:   {args.pump:.4f} µm")
        print(f"Signal Wavelength: {args.wavelength:.4f} µm")
        print(f"Poling Period Λ:   {period:.3f} µm")
        print(f"Effective d_eff:   {deff:.2f} pm/V (1st order 2/π * d33)")
    else:
        # BPM Calculation
        solver = PhaseMatchingSolver(index_fn=index_fn, temperature_c=args.temp)
        if args.process == "shg":
            process = ThreeWaveProcess("shg", args.wavelength)
        else:
            process = ThreeWaveProcess(args.process, args.pump, args.wavelength)

        theta_pm = solver.solve_angle(args.plane, process, pm_type=args.type)
        if theta_pm is None:
            print(f"\nNo phase matching solution found in {args.plane} plane for {args.type}.")
            return

        bw = solver.compute_bandwidths(args.plane, theta_pm, process, pm_type=args.type, length_mm=args.length)
        deff = compute_deff(pg, args.type, math.radians(theta_pm), math.radians(90.0 if args.plane == "xz" else 0.0), d_dict, plane=args.plane)

        print("\n--- BIREFRINGENT PHASE MATCHING (BPM) RESULTS ---")
        print(f"Phase Matching Angle (θ_pm): {theta_pm:.2f}° (plane: {args.plane})")
        print(f"Effective Nonlinearity deff:  {abs(deff):.3f} pm/V")
        print(f"Angular Acceptance (Δθ·L):   {bw['delta_theta_mrad']:.2f} mrad")
        print(f"Spectral Acceptance (Δλ·L):  {bw['delta_lambda_nm']:.2f} nm")
        print(f"Spatial Walk-off Angle (ρ):  {bw['walkoff_mrad']:.2f} mrad ({math.degrees(bw['walkoff_mrad']/1000.0):.2f}°)")

    print("=" * 60)


if __name__ == "__main__":
    main()
