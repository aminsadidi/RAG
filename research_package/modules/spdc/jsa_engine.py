"""Joint Spectral Amplitude (JSA) and Joint Spectral Intensity (JSI) Engine.
References:
  - Grice & Walmsley (1997), Phys. Rev. A 56, 1627.
  - Evans et al. (2010), Opt. Express 18, 22498.
"""

import math
import numpy as np

C_LIGHT_M_S = 299792458.0  # Speed of light in m/s


class GaussianPump:
    """Represents a Gaussian pulsed or CW laser pump."""

    def __init__(self, central_wavelength_um: float, fwhm_nm: float):
        self.lam0_um = central_wavelength_um
        self.lam0_m = central_wavelength_um * 1e-6
        self.omega0 = 2.0 * math.pi * C_LIGHT_M_S / self.lam0_m
        self.fwhm_nm = fwhm_nm
        # Convert FWHM in wavelength to standard deviation sigma_omega in angular frequency:
        # |d omega / d lambda| = 2 pi c / lambda^2
        domega_dlam = 2.0 * math.pi * C_LIGHT_M_S / (self.lam0_m ** 2)
        fwhm_m = fwhm_nm * 1e-9
        fwhm_omega = domega_dlam * fwhm_m
        # FWHM = 2 * sqrt(2 * ln(2)) * sigma = 2.35482 * sigma
        self.sigma_omega = fwhm_omega / (2.0 * math.sqrt(2.0 * math.log(2.0))) if fwhm_nm > 0 else 1e6

    def amplitude(self, omega: np.ndarray) -> np.ndarray:
        """Gaussian spectral amplitude alpha(omega)."""
        d_omega = omega - self.omega0
        return np.exp(-(d_omega ** 2) / (4.0 * (self.sigma_omega ** 2)))


class PhaseMatchingFunction:
    """Calculates phase-matching sinc function Phi(omega_s, omega_i)."""

    def __init__(
        self,
        length_mm: float,
        ng_p: float,
        ng_s: float,
        ng_i: float,
        poling_period_um: float = 0.0,
    ):
        self.length_m = length_mm * 1e-3
        self.ng_p = ng_p  # group index = c / u_p
        self.ng_s = ng_s  # group index = c / u_s
        self.ng_i = ng_i  # group index = c / u_i
        self.qpm_k = (2.0 * math.pi / (poling_period_um * 1e-6)) if poling_period_um > 0 else 0.0

    def delta_k(
        self,
        omega_s: np.ndarray,
        omega_i: np.ndarray,
        omega_s0: float,
        omega_i0: float,
    ) -> np.ndarray:
        """Linearized group-velocity mismatch approximation:
        Delta k = (u_p^-1 - u_s^-1)*(omega_s - omega_s0) + (u_p^-1 - u_i^-1)*(omega_i - omega_i0)
        u_j^-1 = ng_j / c
        """
        d_ws = omega_s - omega_s0
        d_wi = omega_i - omega_i0
        k_prime_p = self.ng_p / C_LIGHT_M_S
        k_prime_s = self.ng_s / C_LIGHT_M_S
        k_prime_i = self.ng_i / C_LIGHT_M_S

        # Delta k(ws, wi) = (k'_p - k'_s)*d_ws + (k'_p - k'_i)*d_wi
        return (k_prime_p - k_prime_s) * d_ws + (k_prime_p - k_prime_i) * d_wi

    def amplitude(self, delta_k_matrix: np.ndarray) -> np.ndarray:
        """Phi = sinc(Delta k * L / 2) * exp(i * Delta k * L / 2)."""
        arg = (delta_k_matrix * self.length_m) / 2.0
        # np.sinc in numpy is sin(pi*x)/(pi*x), so we divide by pi
        sinc_part = np.sinc(arg / math.pi)
        phase_part = np.exp(1j * arg)
        return sinc_part * phase_part


class JSAEngine:
    """Full Joint Spectral Amplitude calculation and analysis engine."""

    def __init__(
        self,
        pump: GaussianPump,
        pm: PhaseMatchingFunction,
        signal_lam0_um: float,
        idler_lam0_um: float,
    ):
        self.pump = pump
        self.pm = pm
        self.signal_lam0_um = signal_lam0_um
        self.idler_lam0_um = idler_lam0_um
        self.omega_s0 = 2.0 * math.pi * C_LIGHT_M_S / (signal_lam0_um * 1e-6)
        self.omega_i0 = 2.0 * math.pi * C_LIGHT_M_S / (idler_lam0_um * 1e-6)

    def compute_jsa(
        self,
        signal_span_nm: float = 30.0,
        idler_span_nm: float = 30.0,
        n_points: int = 120,
    ) -> dict:
        """Computes the 2D complex JSA matrix and intensity JSI on a meshgrid."""
        # Wavelength grid
        lam_s_m = (self.signal_lam0_um * 1e-6) + np.linspace(
            -signal_span_nm * 1e-9 / 2.0, signal_span_nm * 1e-9 / 2.0, n_points
        )
        lam_i_m = (self.idler_lam0_um * 1e-6) + np.linspace(
            -idler_span_nm * 1e-9 / 2.0, idler_span_nm * 1e-9 / 2.0, n_points
        )

        omega_s = 2.0 * math.pi * C_LIGHT_M_S / lam_s_m
        omega_i = 2.0 * math.pi * C_LIGHT_M_S / lam_i_m

        WS, WI = np.meshgrid(omega_s, omega_i, indexing="ij")

        # Pump envelope: alpha(ws + wi)
        pump_omega = WS + WI
        alpha = self.pump.amplitude(pump_omega)

        # Phase-matching function: Phi(ws, wi)
        delta_k = self.pm.delta_k(WS, WI, self.omega_s0, self.omega_i0)
        phi = self.pm.amplitude(delta_k)

        # JSA = alpha * phi
        jsa = alpha * phi

        # JSI = |JSA|^2
        jsi = np.abs(jsa) ** 2

        # Normalize JSI and JSA
        norm = np.sum(jsi)
        if norm > 0:
            jsa_normalized = jsa / math.sqrt(norm)
            jsi_normalized = jsi / norm
        else:
            jsa_normalized = jsa
            jsi_normalized = jsi

        return {
            "signal_lam_nm": lam_s_m * 1e9,
            "idler_lam_nm": lam_i_m * 1e9,
            "omega_s": omega_s,
            "omega_i": omega_i,
            "jsa": jsa_normalized,
            "jsi": jsi_normalized,
            "alpha": alpha,
            "phi": phi,
        }
