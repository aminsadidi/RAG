"""Phase Matching & Quasi-Phase Matching Engine.
Provides comprehensive solvers for Birefringent Phase Matching (BPM) and Quasi-Phase Matching (QPM),
Fresnel optics, effective nonlinear coefficient (d_eff), and acceptance bandwidths.
"""

from .fresnel import FresnelOptics, propagation_direction
from .deff import EffectiveNonlinearCoefficient, compute_deff
from .bpm import PhaseMatchingSolver, ThreeWaveProcess
from .qpm import QPMCalculator

__all__ = [
    "FresnelOptics",
    "propagation_direction",
    "EffectiveNonlinearCoefficient",
    "compute_deff",
    "PhaseMatchingSolver",
    "ThreeWaveProcess",
    "QPMCalculator",
]
