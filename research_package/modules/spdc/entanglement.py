"""Polarization Entanglement, Concurrence, and Bell State Fidelity Engine.
References:
  - Kwiat et al. (1995), Phys. Rev. Lett. 75, 4337.
  - Wootters (1998), Phys. Rev. Lett. 80, 2245.
  - Rubin et al. (1994), Phys. Rev. A 50, 5122.
"""

import math
import numpy as np

C_LIGHT_M_S = 299792458.0


class PolarizationEntanglement:
    """Models polarization-entangled states produced by Type-II SPDC,
    including longitudinal birefringent walk-off and compensator crystals.
    """

    def __init__(
        self,
        crystal_length_mm: float,
        ng_o: float,
        ng_e: float,
        coherence_time_fs: float = 150.0,
        compensation_ratio: float = 0.0,
    ):
        """
        compensation_ratio:
          0.0: uncompensated (full walk-off)
          1.0: fully compensated (e.g. using a half-thickness crystal rotated by 90°)
        """
        self.L_m = crystal_length_mm * 1e-3
        self.ng_o = ng_o
        self.ng_e = ng_e
        self.tau_c_s = coherence_time_fs * 1e-15
        self.comp = compensation_ratio

    @property
    def raw_walkoff_fs(self) -> float:
        """Total uncompensated temporal walk-off in femtoseconds:
        Delta t = L * |ng_e - ng_o| / c
        """
        dt_s = self.L_m * abs(self.ng_e - self.ng_o) / C_LIGHT_M_S
        return float(dt_s * 1e15)

    @property
    def residual_walkoff_fs(self) -> float:
        """Net temporal walk-off after compensation."""
        return float(self.raw_walkoff_fs * abs(1.0 - self.comp))

    @property
    def coherence_parameter(self) -> float:
        """Degree of indistinguishability gamma = exp(-(Delta t / tau_c)^2 / 2)."""
        dt_s = self.residual_walkoff_fs * 1e-15
        arg = (dt_s / self.tau_c_s) ** 2 / 2.0
        return float(math.exp(-arg))

    def density_matrix(self) -> np.ndarray:
        """Constructs the two-qubit density matrix in the {|HH>, |HV>, |VH>, |VV>} basis:
        rho = 0.5 * (|HV><HV| + |VH><VH| - gamma |HV><VH| - gamma |VH><HV|)
        for the Bell singlet state |Psi-> = (|HV> - |VH>)/sqrt(2).
        """
        gamma = self.coherence_parameter
        rho = np.zeros((4, 4), dtype=complex)
        rho[1, 1] = 0.5
        rho[2, 2] = 0.5
        rho[1, 2] = -0.5 * gamma
        rho[2, 1] = -0.5 * gamma
        return rho

    @property
    def concurrence(self) -> float:
        """Wootters concurrence C in [0, 1]. For this state: C = gamma."""
        return float(self.coherence_parameter)

    @property
    def tangle(self) -> float:
        """Tangle T = C^2."""
        c = self.concurrence
        return float(c * c)

    @property
    def bell_singlet_fidelity(self) -> float:
        """Fidelity with the ideal Bell state |Psi->: F = (1 + gamma) / 2."""
        gamma = self.coherence_parameter
        return float((1.0 + gamma) / 2.0)


def bell_state_fidelity(crystal_length_mm: float, ng_o: float, ng_e: float, coherence_time_fs: float, compensated: bool = True) -> float:
    """Helper function to compute Bell state fidelity."""
    ratio = 1.0 if compensated else 0.0
    engine = PolarizationEntanglement(crystal_length_mm, ng_o, ng_e, coherence_time_fs, ratio)
    return engine.bell_singlet_fidelity
