"""Hong-Ou-Mandel (HOM) Interference and Two-Photon Quantum Dip Module.
References:
  - Hong, Ou, Mandel (1987), Phys. Rev. Lett. 59, 2044.
  - Mosley et al. (2008), Phys. Rev. Lett. 100, 133601.
  - Evans et al. (2010), Phys. Rev. Lett. 105, 253601.
  - Bennink (2010), Phys. Rev. A 81, 053805.
"""

import numpy as np


class HongOuMandelDip:
    """Calculates Hong-Ou-Mandel two-photon quantum interference dip.
    Supports both:
      1) Signal-Idler pair interference from the same SPDC source (pair visibility).
      2) Interference between two independent heralded single photons (independent visibility = purity).
    """

    def __init__(self, jsa_dict: dict):
        """jsa_dict: dictionary returned by JSAEngine.compute_jsa()."""
        self.jsa = jsa_dict["jsa"]
        self.omega_s = jsa_dict["omega_s"]
        self.omega_i = jsa_dict["omega_i"]
        self.norm = float(np.sum(np.abs(self.jsa) ** 2))

    def pair_visibility(self) -> float:
        """Calculates HOM visibility V between signal and idler of the same pair.
        V = Re(Tr(F @ F^T*)) / Tr(F @ F^dag).
        For identical signal/idler polarizations and symmetric state, V = 1.0.
        """
        f_transposed_conj = np.conj(self.jsa.T)
        overlap = np.sum(self.jsa * f_transposed_conj)
        vis = np.real(overlap) / self.norm if self.norm > 0 else 0.0
        return float(np.clip(vis, 0.0, 1.0))

    def independent_heralded_visibility(self) -> float:
        """Calculates the HOM interference visibility between two independent single photons
        heralded from two identical SPDC sources.
        As established by Mosley et al. (2008) and Evans et al. (2010), this visibility is
        strictly equal to the single-photon spectral purity P = 1 / K:
          V_indep = Tr(rho_s^2) = P = sum(lambda_k^2).
        """
        # Reduced density matrix of signal photon: rho_s = JSA @ JSA^dag
        rho_s = self.jsa @ np.conj(self.jsa.T)
        if self.norm > 0:
            rho_s = rho_s / self.norm
        purity = np.real(np.trace(rho_s @ rho_s))
        return float(np.clip(purity, 0.0, 1.0))

    def visibility(self) -> float:
        """Default visibility returns pair_visibility."""
        return self.pair_visibility()

    def compute_dip_curve(self, delays_fs: np.ndarray) -> dict:
        """Computes the coincidence probability P_c(tau) as a function of delay tau (in femtoseconds)."""
        delays_s = delays_fs * 1e-15
        coincidences = []

        WS, WI = np.meshgrid(self.omega_s, self.omega_i, indexing="ij")
        d_omega = WS - WI
        f_transposed_conj = np.conj(self.jsa.T)
        base_overlap = self.jsa * f_transposed_conj

        for tau in delays_s:
            phase_factor = np.exp(1j * d_omega * tau)
            overlap_tau = np.sum(base_overlap * phase_factor)
            p_c = 0.5 * (1.0 - np.real(overlap_tau) / self.norm)
            coincidences.append(float(p_c))

        coincidences = np.array(coincidences)
        p_min = np.min(coincidences)
        p_max = np.max(coincidences)

        half_dip = (p_max + p_min) / 2.0
        indices_below = np.where(coincidences <= half_dip)[0]
        fwhm_fs = float(delays_fs[indices_below[-1]] - delays_fs[indices_below[0]]) if len(indices_below) >= 2 else 0.0

        return {
            "delays_fs": delays_fs,
            "coincidences": coincidences,
            "pair_visibility": self.pair_visibility(),
            "independent_visibility": self.independent_heralded_visibility(),
            "fwhm_fs": fwhm_fs,
            "dip_minimum": p_min,
        }


def hom_visibility(jsa_matrix: np.ndarray) -> float:
    """Convenience function returning the pair HOM visibility for a given JSA matrix."""
    norm = np.sum(np.abs(jsa_matrix) ** 2)
    if norm <= 0:
        return 0.0
    f_trans_conj = np.conj(jsa_matrix.T)
    overlap = np.sum(jsa_matrix * f_trans_conj)
    return float(np.clip(np.real(overlap) / norm, 0.0, 1.0))
