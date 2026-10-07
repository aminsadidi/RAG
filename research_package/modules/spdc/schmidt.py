"""Schmidt Decomposition and Single-Photon Spectral Purity for SPDC.
References:
  - Law, Walmsley, Eberly (2000), Phys. Rev. Lett. 84, 5304.
  - Mosley et al. (2008), Phys. Rev. Lett. 100, 133601.
  - Evans et al. (2010), Opt. Express 18, 22498.
"""

import math
import numpy as np


class SchmidtDecomposition:
    """Performs Singular Value Decomposition on the Joint Spectral Amplitude matrix."""

    def __init__(self, jsa_matrix: np.ndarray):
        """jsa_matrix: complex 2D array of shape (N_s, N_i)."""
        self.jsa = jsa_matrix
        # Perform SVD: JSA = U @ diag(S) @ Vh
        u, s, vh = np.linalg.svd(jsa_matrix, full_matrices=False)
        self.u = u
        self.singular_values = s
        self.vh = vh

        # Probabilities of the Schmidt modes: lambda_k = s_k^2 / sum(s_j^2)
        s_squared = s ** 2
        total_power = np.sum(s_squared)
        self.mode_weights = s_squared / total_power if total_power > 0 else s_squared

    @property
    def purity(self) -> float:
        """Heralded single-photon spectral purity P = 1 / K = sum(lambda_k^2).
        For an unentangled, factorable state: P = 1.0 (Schmidt number K = 1).
        """
        return float(np.sum(self.mode_weights ** 2))

    @property
    def schmidt_number(self) -> float:
        """Effective number of frequency modes K = 1 / sum(lambda_k^2)."""
        p = self.purity
        return 1.0 / p if p > 0 else float("inf")

    @property
    def entanglement_entropy(self) -> float:
        """Von Neumann entropy of entanglement S = - sum(lambda_k * log2(lambda_k))."""
        entropy = 0.0
        for w in self.mode_weights:
            if w > 1e-15:
                entropy -= w * math.log2(w)
        return float(entropy)

    def leading_modes(self, n_modes: int = 3) -> dict:
        """Returns the leading Schmidt mode profiles and weights."""
        n = min(n_modes, len(self.mode_weights))
        return {
            "weights": self.mode_weights[:n],
            "singular_values": self.singular_values[:n],
            "signal_modes": self.u[:, :n],
            "idler_modes": self.vh[:n, :].T,
        }


def schmidt_purity(jsa_matrix: np.ndarray) -> float:
    """Convenience function returning the spectral purity P = 1 / K."""
    return SchmidtDecomposition(jsa_matrix).purity


def entanglement_entropy(jsa_matrix: np.ndarray) -> float:
    """Convenience function returning the Von Neumann entanglement entropy in bits."""
    return SchmidtDecomposition(jsa_matrix).entanglement_entropy
