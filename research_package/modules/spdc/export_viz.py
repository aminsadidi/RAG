"""Data Exporter & Vector SVG Visualization Engine for SPDC States.
Generates CSV matrix data and standalone publication-quality SVG graphics
for Joint Spectral Intensity (JSI) 2D heatmaps and Hong-Ou-Mandel interference dips
without requiring external graphical libraries (pure Python standard library + numpy).
"""

import csv
import math
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .catalog import PRESETS, SPDCPreset
from .schmidt import SchmidtDecomposition
from .hom_dip import HongOuMandelDip


def colormap_viridis(val: float) -> str:
    """Simple viridis-like colormap mapping val in [0, 1] to hex color string."""
    v = max(0.0, min(1.0, val))
    # Approximation of colormap (dark purple -> blue -> teal -> yellow)
    r = int(255 * (0.28 + 0.72 * (v ** 2) if v > 0.5 else 0.28 * (v * 2)))
    g = int(255 * (0.01 + 0.99 * v))
    b = int(255 * (0.33 + 0.67 * (1.0 - v) if v < 0.7 else 0.2 * (1.0 - v)))
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def export_jsi_csv(jsa_result: Dict, filepath: Path):
    """Exports 2D normalized JSI grid to CSV file."""
    sig_nm = jsa_result.get("signal_lam_nm", jsa_result.get("signal_wavelengths_nm"))
    idl_nm = jsa_result.get("idler_lam_nm", jsa_result.get("idler_wavelengths_nm"))
    jsi = jsa_result["jsi"]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Signal_nm \\ Idler_nm"] + [f"{w:.3f}" for w in idl_nm])
        for i, s_val in enumerate(sig_nm):
            row = [f"{s_val:.3f}"] + [f"{jsi[i, j]:.6e}" for j in range(len(idl_nm))]
            writer.writerow(row)


def export_hom_csv(delays_fs: np.ndarray, coincidences: np.ndarray, filepath: Path):
    """Exports optical delay tau and coincidence probability to CSV file."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Delay_tau_fs", "Coincidence_Probability"])
        for tau, p in zip(delays_fs, coincidences):
            writer.writerow([f"{tau:.2f}", f"{p:.6f}"])


def generate_jsi_svg(
    jsa_result: Dict,
    filepath: Path,
    title: str = "Joint Spectral Intensity (JSI)",
    purity: Optional[float] = None,
    schmidt_k: Optional[float] = None,
):
    """Generates a standalone vector SVG heatmap for 2D JSI."""
    sig_nm = jsa_result.get("signal_lam_nm", jsa_result.get("signal_wavelengths_nm"))
    idl_nm = jsa_result.get("idler_lam_nm", jsa_result.get("idler_wavelengths_nm"))
    jsi = jsa_result["jsi"]
    n_pts = len(sig_nm)

    width = 600
    height = 550
    margin_left = 90
    margin_right = 50
    margin_top = 60
    margin_bottom = 70

    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    cell_w = plot_w / n_pts
    cell_h = plot_h / n_pts

    purity_text = f"Purity P = {purity:.3f} | K = {schmidt_k:.2f}" if purity is not None else ""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <style>
    .title {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 16px; font-weight: bold; fill: #1e293b; text-anchor: middle; }}
    .subtitle {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; fill: #0284c7; text-anchor: middle; }}
    .axis-label {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; font-weight: 600; fill: #475569; text-anchor: middle; }}
    .tick {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 10px; fill: #64748b; }}
  </style>
  <rect width="{width}" height="{height}" fill="#ffffff"/>
  <text x="{width/2}" y="28" class="title">{title}</text>
  <text x="{width/2}" y="48" class="subtitle">{purity_text}</text>

  <!-- Heatmap Grid -->
  <g transform="translate({margin_left}, {margin_top})">
"""

    # Cells
    for i in range(n_pts):
        for j in range(n_pts):
            val = float(jsi[i, j])
            color = colormap_viridis(val)
            x = j * cell_w
            y = (n_pts - 1 - i) * cell_h
            svg += f'    <rect x="{x:.1f}" y="{y:.1f}" width="{cell_w+0.5:.1f}" height="{cell_h+0.5:.1f}" fill="{color}"/>\n'

    # Border
    svg += f"""    <rect x="0" y="0" width="{plot_w}" height="{plot_h}" fill="none" stroke="#334155" stroke-width="1.5"/>
  </g>

  <!-- X-Axis Labels (Idler Wavelength) -->
  <text x="{margin_left + plot_w/2}" y="{height - 20}" class="axis-label">Idler Wavelength λ_i (nm)</text>
  <text x="{margin_left}" y="{height - 45}" class="tick" text-anchor="middle">{idl_nm[0]:.1f}</text>
  <text x="{margin_left + plot_w/2}" y="{height - 45}" class="tick" text-anchor="middle">{idl_nm[n_pts//2]:.1f}</text>
  <text x="{margin_left + plot_w}" y="{height - 45}" class="tick" text-anchor="middle">{idl_nm[-1]:.1f}</text>

  <!-- Y-Axis Labels (Signal Wavelength) -->
  <text x="25" y="{margin_top + plot_h/2}" class="axis-label" transform="rotate(-90, 25, {margin_top + plot_h/2})">Signal Wavelength λ_s (nm)</text>
  <text x="{margin_left - 10}" y="{margin_top + plot_h}" class="tick" text-anchor="end">{sig_nm[0]:.1f}</text>
  <text x="{margin_left - 10}" y="{margin_top + plot_h/2}" class="tick" text-anchor="end">{sig_nm[n_pts//2]:.1f}</text>
  <text x="{margin_left - 10}" y="{margin_top + 10}" class="tick" text-anchor="end">{sig_nm[-1]:.1f}</text>

</svg>
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(svg)


def generate_hom_dip_svg(
    delays_fs: np.ndarray,
    coincidences: np.ndarray,
    filepath: Path,
    title: str = "Hong-Ou-Mandel Dip",
    visibility: float = 1.0,
):
    """Generates vector SVG curve of Hong-Ou-Mandel coincidence probability dip."""
    width = 600
    height = 400
    margin_left = 70
    margin_right = 40
    margin_top = 50
    margin_bottom = 60

    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    t_min = float(delays_fs[0])
    t_max = float(delays_fs[-1])

    # Convert curve points to SVG path
    points = []
    for t, p in zip(delays_fs, coincidences):
        x = margin_left + ((t - t_min) / (t_max - t_min)) * plot_w
        # y: 0 coincidence at bottom (plot_h), 1.0 coincidence at top (0)
        y = margin_top + (1.0 - p) * plot_h
        points.append(f"{x:.1f},{y:.1f}")

    path_d = "M " + " L ".join(points)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <style>
    .title {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 16px; font-weight: bold; fill: #1e293b; text-anchor: middle; }}
    .subtitle {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; fill: #059669; text-anchor: middle; }}
    .axis-label {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; font-weight: 600; fill: #475569; text-anchor: middle; }}
    .tick {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 10px; fill: #64748b; }}
  </style>
  <rect width="{width}" height="{height}" fill="#ffffff"/>
  <text x="{width/2}" y="24" class="title">{title}</text>
  <text x="{width/2}" y="42" class="subtitle">Interference Visibility V = {visibility*100:.1f}%</text>

  <!-- Plot Background & Grid -->
  <g transform="translate({margin_left}, {margin_top})">
    <rect width="{plot_w}" height="{plot_h}" fill="#f8fafc" stroke="#cbd5e1"/>
    <!-- Grid line at P = 0.5 -->
    <line x1="0" y1="{plot_h/2}" x2="{plot_w}" y2="{plot_h/2}" stroke="#e2e8f0" stroke-dasharray="4,4"/>
  </g>

  <!-- Dip Curve -->
  <path d="{path_d}" fill="none" stroke="#2563eb" stroke-width="2.5"/>

  <!-- X-Axis Labels -->
  <text x="{margin_left + plot_w/2}" y="{height - 15}" class="axis-label">Relative Delay τ (fs)</text>
  <text x="{margin_left}" y="{height - 40}" class="tick" text-anchor="middle">{t_min:.0f}</text>
  <text x="{margin_left + plot_w/2}" y="{height - 40}" class="tick" text-anchor="middle">0</text>
  <text x="{margin_left + plot_w}" y="{height - 40}" class="tick" text-anchor="middle">{t_max:.0f}</text>

  <!-- Y-Axis Labels -->
  <text x="20" y="{margin_top + plot_h/2}" class="axis-label" transform="rotate(-90, 20, {margin_top + plot_h/2})">Coincidence Probability P_c(τ)</text>
  <text x="{margin_left - 8}" y="{margin_top + plot_h + 4}" class="tick" text-anchor="end">0.0</text>
  <text x="{margin_left - 8}" y="{margin_top + plot_h/2 + 4}" class="tick" text-anchor="end">0.5</text>
  <text x="{margin_left - 8}" y="{margin_top + 4}" class="tick" text-anchor="end">1.0</text>

</svg>
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(svg)


def batch_export_all_presets(output_dir: Path):
    """Executes all catalog presets, computing JSA, Schmidt decomposition, and HOM dips,
    and exports SVGs and CSV matrices to output_dir.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_records = []

    print(f"Batch exporting SPDC simulations to: {output_dir}")
    for key, preset in PRESETS.items():
        print(f"  Processing preset: {key} ({preset.crystal})...")
        engine = preset.build_engine()
        res = engine.compute_jsa(signal_span_nm=12.0, idler_span_nm=12.0, n_points=50)

        schmidt = SchmidtDecomposition(res["jsa"])
        purity = schmidt.purity
        k_num = schmidt.schmidt_number

        hom = HongOuMandelDip(res)
        delays_fs = np.linspace(-400.0, 400.0, 81)
        hom_res = hom.compute_dip_curve(delays_fs=delays_fs)

        # Export files
        csv_jsi = output_dir / f"{key.lower()}_jsi.csv"
        csv_hom = output_dir / f"{key.lower()}_hom.csv"
        svg_jsi = output_dir / f"{key.lower()}_jsi.svg"
        svg_hom = output_dir / f"{key.lower()}_hom.svg"

        export_jsi_csv(res, csv_jsi)
        export_hom_csv(delays_fs, hom_res["coincidences"], csv_hom)
        generate_jsi_svg(res, svg_jsi, title=f"JSI - {preset.crystal} ({preset.name})", purity=purity, schmidt_k=k_num)
        generate_hom_dip_svg(delays_fs, hom_res["coincidences"], svg_hom, title=f"HOM Dip - {preset.name}", visibility=hom_res.get("pair_visibility", 1.0))

        summary_records.append({
            "key": key,
            "name": preset.name,
            "crystal": preset.crystal,
            "purity": round(purity, 4),
            "schmidt_k": round(k_num, 3),
            "hom_visibility": round(hom_res.get("pair_visibility", 1.0), 4),
            "svg_jsi": svg_jsi.name,
            "svg_hom": svg_hom.name,
        })

    print(f"Batch export completed: {len(summary_records)} presets generated.")
    return summary_records
