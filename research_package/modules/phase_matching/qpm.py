"""Quasi-Phase Matching (QPM) Engineering & Thermal Poling Engine.
Calculates 1st and m-th order poling periods, temperature tuning rates,
and thermal expansion grating corrections for PPLN, PPKTP, PPMgLT, and OP-semiconductors.
"""

import math
from typing import Callable, Dict, Optional, Tuple


class QPMCalculator:
    """Quasi-Phase-Matching grating period and temperature tuning calculator."""

    # Thermal expansion coefficients (alpha: linear [1/°C], beta: quadratic [1/°C^2])
    THERMAL_EXPANSION = {
        "linbo3": {"alpha": 1.54e-5, "beta": 5.3e-9},
        "mgo-linbo3": {"alpha": 1.54e-5, "beta": 5.3e-9},
        "litao3": {"alpha": 1.60e-5, "beta": 4.0e-9},
        "ktiopo4": {"alpha": 6.7e-6, "beta": 1.1e-8},
        "gaas": {"alpha": 5.7e-6, "beta": 0.0},
    }

    def __init__(
        self,
        material: str,
        index_fn: Callable[[float, float], float],
        t0_c: float = 25.0,
    ):
        """
        Args:
            material: Crystal identifier (e.g. 'linbo3', 'ktiopo4', 'gaas')
            index_fn: Function mapping (wavelength_um, temperature_c) -> refractive index n
            t0_c: Reference temperature in °C
        """
        self.material = material.lower().strip()
        self.index_fn = index_fn
        self.t0_c = float(t0_c)

    def calculate_period_um(
        self,
        lam_pump_um: float,
        lam_signal_um: float,
        temperature_c: Optional[float] = None,
        order: int = 1,
    ) -> float:
        """Calculates exact QPM period Lambda in µm for a 3-wave mixing process.
        
        Args:
            lam_pump_um: Pump wavelength in µm (e.g. 0.532 for SHG, or 0.776 for SPDC)
            lam_signal_um: Signal wavelength in µm (e.g. 1.064 for SHG, or 1.552 for SPDC)
            temperature_c: Temperature in °C (defaults to t0_c)
            order: QPM order m (usually 1)
        """
        temp = self.t0_c if temperature_c is None else float(temperature_c)

        if abs(lam_signal_um - 2.0 * lam_pump_um) < 1e-4:
            # Second Harmonic Generation (SHG of signal -> pump)
            # or Degenerate SPDC/OPO
            lam1 = lam_signal_um
            lam2 = lam_signal_um
            lam3 = lam_pump_um
        else:
            # Non-degenerate process: 1/lam3 = 1/lam1 + 1/lam2
            lam3 = lam_pump_um
            lam1 = lam_signal_um
            if 1.0 / lam3 <= 1.0 / lam1:
                raise ValueError(f"Pump {lam3} µm must have higher energy than signal {lam1} µm")
            lam2 = 1.0 / (1.0 / lam3 - 1.0 / lam1)

        n1 = self.index_fn(lam1, temp)
        n2 = self.index_fn(lam2, temp)
        n3 = self.index_fn(lam3, temp)

        # Delta k_material = 2pi * (n3/lam3 - n1/lam1 - n2/lam2)
        dk_mat = 2.0 * math.pi * (n3 / lam3 - n1 / lam1 - n2 / lam2)
        if abs(dk_mat) < 1e-12:
            return float("inf")

        period = (2.0 * math.pi * order) / abs(dk_mat)
        return round(period, 4)

    def thermal_expansion_factor(self, temperature_c: float) -> float:
        """Computes grating thermal expansion multiplier [1 + alpha*dT + beta*dT^2]."""
        dt = temperature_c - self.t0_c
        coeffs = self.THERMAL_EXPANSION.get(self.material, {"alpha": 1.0e-5, "beta": 0.0})
        return 1.0 + coeffs["alpha"] * dt + coeffs["beta"] * (dt ** 2)

    def temperature_tuning_rate_nm_per_c(
        self,
        lam_pump_um: float,
        lam_signal_um: float,
        temperature_c: float = 25.0,
    ) -> float:
        """Calculates temperature tuning slope d(lambda_signal) / dT in nm/°C."""
        dt = 1.0  # 1 °C numerical perturbation
        t_high = temperature_c + dt
        t_low = temperature_c - dt

        lam_high = self.find_resonant_signal_nm(lam_pump_um, self.calculate_period_um(lam_pump_um, lam_signal_um, temperature_c), t_high)
        lam_low = self.find_resonant_signal_nm(lam_pump_um, self.calculate_period_um(lam_pump_um, lam_signal_um, temperature_c), t_low)

        return (lam_high - lam_low) / (2.0 * dt)

    def find_resonant_signal_nm(self, lam_pump_um: float, target_period_um: float, temp_c: float) -> float:
        """Helper to find signal wavelength that satisfies QPM for fixed grating period at temperature temp_c."""
        # Simple local search around 2 * lam_pump
        best_lam = 2.0 * lam_pump_um * 1000.0
        min_diff = float("inf")
        test_range = [best_lam + delta for delta in range(-50, 51)]
        for lam_nm in test_range:
            p = self.calculate_period_um(lam_pump_um, lam_nm / 1000.0, temp_c)
            diff = abs(p - target_period_um)
            if diff < min_diff:
                min_diff = diff
                best_lam = lam_nm
        return best_lam
