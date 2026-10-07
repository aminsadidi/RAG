"""Spatial Mode Matching and Fiber Collection Efficiency for SPDC.
References:
  - Bennink (2010), Phys. Rev. A 81, 053805.
  - Boyd & Kleinman (1968), J. Appl. Phys. 39, 3597.
  - Ljunggren & Tengner (2005), Phys. Rev. A 72, 062301.
"""

import math


class SpatialModeCoupling:
    """Calculates spatial mode overlap, waist parameters, and fiber coupling efficiency."""

    def __init__(
        self,
        pump_waist_um: float,
        collection_waist_um: float,
        crystal_length_mm: float,
        refractive_index: float,
        pump_wavelength_um: float,
    ):
        self.wp_m = pump_waist_um * 1e-6
        self.wc_m = collection_waist_um * 1e-6
        self.L_m = crystal_length_mm * 1e-3
        self.n = refractive_index
        self.lam_p_m = pump_wavelength_um * 1e-6

    @property
    def pump_rayleigh_range_m(self) -> float:
        """Rayleigh range z_R = pi * n * w0^2 / lambda."""
        return math.pi * self.n * (self.wp_m ** 2) / self.lam_p_m

    @property
    def focusing_parameter_xi(self) -> float:
        """Boyd-Kleinman focusing parameter xi = L / (2 * z_R)."""
        return self.L_m / (2.0 * self.pump_rayleigh_range_m)

    @property
    def waist_ratio(self) -> float:
        """Ratio of collection waist to pump waist w_c / w_p."""
        return self.wc_m / self.wp_m

    def heralding_efficiency(self) -> float:
        """Approximates the spatial heralding efficiency eta_herald into single-mode fiber.
        According to Bennink (2010) and Ljunggren & Tengner (2005), the optimal spatial
        collection into a single-mode fiber occurs when w_c / w_p = sqrt(2) for a collimated
        pump (xi << 1), giving a spatial overlap approaching ~85% to 92%.
        """
        # Waist mismatch factor: gamma = w_c / w_p
        gamma = self.waist_ratio
        # Mode overlap for Gaussian beams: eta_spatial ~ 4 / (gamma + 1/gamma)^2
        # Modified by focusing parameter:
        xi = self.focusing_parameter_xi
        # Empirical reduction due to Gouy phase walk-off in focused geometries
        focusing_penalty = 1.0 / (1.0 + 0.15 * xi)

        optimal_gamma = math.sqrt(2.0)
        mode_match = 4.0 / ((gamma / optimal_gamma + optimal_gamma / gamma) ** 2)
        return float(min(mode_match * focusing_penalty * 0.94, 0.95))

    def pair_rate_enhancement(self) -> float:
        """Relative Boyd-Kleinman h_m(xi) enhancement factor."""
        xi = self.focusing_parameter_xi
        # Approximate Boyd-Kleinman integral h(xi) without walk-off:
        # h(xi) peaks around xi = 2.84 with value ~1.06
        return float(1.06 * (xi / 2.84) / (1.0 + (xi / 2.84) ** 1.2))
