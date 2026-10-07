#!/usr/bin/env python3
"""Interactive Command-Line Tool for Quantum SPDC Engine.
Allows instant simulation, ASCII heatmap generation of Joint Spectral Intensity (JSI),
Schmidt purity calculation, and Bell state analysis directly from the terminal.
"""

import argparse
import sys
from pathlib import Path
import numpy as np

# Ensure research_package is in path
sys.path.insert(0, str(Path(__file__).parent))

from modules.spdc.catalog import PRESETS, get_preset
from modules.spdc.schmidt import SchmidtDecomposition
from modules.spdc.hom_dip import HongOuMandelDip
from modules.spdc.entanglement import PolarizationEntanglement


ASCII_GRADIENT = " .:-=+*#%@"


def render_ascii_jsi(jsi_matrix: np.ndarray, width: int = 40, height: int = 16) -> str:
    """Renders a 2D intensity matrix as an ASCII heatmap in terminal."""
    n_rows, n_cols = jsi_matrix.shape
    row_step = max(1, n_rows // height)
    col_step = max(1, n_cols // width)

    max_val = np.max(jsi_matrix) if np.max(jsi_matrix) > 0 else 1.0
    normalized = jsi_matrix / max_val

    lines = []
    lines.append("  +-" + "-" * width + "-+")
    for r in range(0, min(n_rows, height * row_step), row_step):
        row_str = "  | "
        for c in range(0, min(n_cols, width * col_step), col_step):
            val = normalized[r, c]
            char_idx = min(len(ASCII_GRADIENT) - 1, int(val * (len(ASCII_GRADIENT) - 1)))
            row_str += ASCII_GRADIENT[char_idx]
        row_str += " |"
        lines.append(row_str)
    lines.append("  +-" + "-" * width + "-+")
    return "\n".join(lines)


def run_cli():
    parser = argparse.ArgumentParser(description="Quantum SPDC Terminal Simulator")
    parser.add_argument("--list-presets", action="store_true", help="List all available SPDC experimental presets")
    parser.add_argument("--preset", type=str, default="PPKTP_EVANS_2010", help="Preset key to simulate")
    parser.add_argument("--span-nm", type=float, default=15.0, help="Spectral span in nm for JSA grid")
    parser.add_argument("--points", type=int, default=80, help="Grid resolution")
    parser.add_argument("--export-all", type=str, metavar="DIR", help="Export SVG/CSV for all presets to directory")
    args = parser.parse_args()

    if args.export_all:
        from modules.spdc.export_viz import batch_export_all_presets
        out_path = Path(args.export_all)
        batch_export_all_presets(out_path)
        print(f"\nAll presets exported to: {out_path.resolve()}\n")
        return

    if args.list_presets:
        print("\n=== AVAILABLE QUANTUM SPDC PRESETS ===")
        for key, p in PRESETS.items():
            print(f"  * {key:22s} : {p.name} ({p.crystal}, {p.phase_matching})")
        print()
        return

    try:
        preset = get_preset(args.preset)
    except KeyError as e:
        print(f"Error: {e}")
        return

    print("=" * 65)
    print(f"  QUANTUM SPDC ENGINE: {preset.name}")
    print("=" * 65)
    print(f"  Crystal:            {preset.crystal}")
    print(f"  Interaction:        {preset.phase_matching}")
    print(f"  Crystal Length:     {preset.crystal_length_mm:.1f} mm")
    print(f"  Pump Wavelength:    {preset.pump_lam_um*1000:.1f} nm (FWHM: {preset.pump_fwhm_nm:.2f} nm)")
    print(f"  Signal / Idler:     {preset.signal_lam_um*1000:.1f} nm / {preset.idler_lam_um*1000:.1f} nm")
    if preset.notes:
        print(f"  Literature Note:    {preset.notes}")
    print("-" * 65)

    print("\nComputing Joint Spectral Amplitude (JSA) and JSI grid...")
    engine = preset.build_engine()
    res = engine.compute_jsa(signal_span_nm=args.span_nm, idler_span_nm=args.span_nm, n_points=args.points)

    print("\n[Joint Spectral Intensity (JSI) Heatmap in (omega_s, omega_i) plane]:")
    print(render_ascii_jsi(res["jsi"]))
    print(f"  Axis X: Signal ({res['signal_lam_nm'][0]:.1f} -> {res['signal_lam_nm'][-1]:.1f} nm)")
    print(f"  Axis Y: Idler  ({res['idler_lam_nm'][0]:.1f} -> {res['idler_lam_nm'][-1]:.1f} nm)")

    # Schmidt analysis
    schmidt = SchmidtDecomposition(res["jsa"])
    print("\n=== QUANTUM SPECTRAL STATE METRICS ===")
    print(f"  Spectral Purity (P = 1/K):     {schmidt.purity*100:.2f}%")
    print(f"  Effective Schmidt Number (K):  {schmidt.schmidt_number:.3f}")
    print(f"  Entanglement Entropy:          {schmidt.entanglement_entropy:.3f} bits")

    leading = schmidt.leading_modes(3)
    weights_str = ", ".join(f"{w*100:.1f}%" for w in leading["weights"])
    print(f"  Top Schmidt Mode Weights:      [{weights_str}]")

    # HOM dip analysis
    hom = HongOuMandelDip(res)
    pair_vis = hom.pair_visibility()
    indep_vis = hom.independent_heralded_visibility()
    print("\n=== HONG-OU-MANDEL (HOM) QUANTUM INTERFERENCE ===")
    print(f"  Pair HOM Visibility:           {pair_vis*100:.2f}%")
    print(f"  Independent Photon Visibility: {indep_vis*100:.2f}%")

    # Polarization walk-off
    ent = PolarizationEntanglement(
        crystal_length_mm=preset.crystal_length_mm,
        ng_o=preset.ng_s,
        ng_e=preset.ng_i,
        coherence_time_fs=150.0,
        compensation_ratio=1.0,
    )
    print("\n=== POLARIZATION ENTANGLEMENT (WITH COMPENSATOR) ===")
    print(f"  Raw Walk-off Delay:            {ent.raw_walkoff_fs:.1f} fs")
    print(f"  Compensated Concurrence:       {ent.concurrence:.3f}")
    print(f"  Bell Singlet Fidelity F:       {ent.bell_singlet_fidelity*100:.2f}%")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_cli()
