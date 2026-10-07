"""Standalone Quantum Spontaneous Parametric Down-Conversion (SPDC) Engine.
Provides Joint Spectral Amplitude (JSA), Schmidt decomposition,
Hong-Ou-Mandel (HOM) interference, and spatial fiber coupling.
"""

from .jsa_engine import JSAEngine, GaussianPump, PhaseMatchingFunction
from .schmidt import SchmidtDecomposition, schmidt_purity, entanglement_entropy
from .hom_dip import HongOuMandelDip, hom_visibility
from .spatial_modes import SpatialModeCoupling
from .catalog import SPDCPreset, get_preset, PRESETS
from .entanglement import PolarizationEntanglement, bell_state_fidelity
from .export_viz import (
    export_jsi_csv,
    export_hom_csv,
    generate_jsi_svg,
    generate_hom_dip_svg,
    batch_export_all_presets,
)

__all__ = [
    "JSAEngine",
    "GaussianPump",
    "PhaseMatchingFunction",
    "SchmidtDecomposition",
    "schmidt_purity",
    "entanglement_entropy",
    "HongOuMandelDip",
    "hom_visibility",
    "SpatialModeCoupling",
    "SPDCPreset",
    "get_preset",
    "PRESETS",
    "PolarizationEntanglement",
    "bell_state_fidelity",
    "export_jsi_csv",
    "export_hom_csv",
    "generate_jsi_svg",
    "generate_hom_dip_svg",
    "batch_export_all_presets",
]
