"""Standalone Quantum Spontaneous Parametric Down-Conversion (SPDC) Engine.
Provides Joint Spectral Amplitude (JSA), Schmidt decomposition,
Hong-Ou-Mandel (HOM) interference, and spatial fiber coupling.
"""

from .jsa_engine import JSAEngine, GaussianPump, PhaseMatchingFunction
from .schmidt import SchmidtDecomposition, schmidt_purity, entanglement_entropy
from .hom_dip import HongOuMandelDip, hom_visibility
from .spatial_modes import SpatialModeCoupling

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
]
