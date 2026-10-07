"""Birefringent Phase Matching (BPM) Solver.
Finds exact phase-matching angles theta_pm, acceptance bandwidths (angular, spectral, temperature),
and Poynting vector walk-off for three-wave mixing (SHG, SFG, OPO, DFG, SPDC).
"""

import math
import numpy as np
from typing import Callable, Dict, List, Optional, Tuple, Union
from .fresnel import FresnelOptics, propagation_direction

TWO_PI = 2.0 * math.pi
SINC_HALF_WIDTH = 2.78312  # FWHM factor where sinc^2(Delta_k * L / 2) = 0.5 -> |Delta_k * L| = 2.78312


class ThreeWaveProcess:
    """Represents a parametric three-wave mixing process: 1/lambda3 = 1/lambda1 + 1/lambda2."""

    def __init__(self, process_type: str, lam_a_um: float, lam_b_um: Optional[float] = None):
        self.process_type = process_type.lower()
        if self.process_type == "shg":
            self.l1 = float(lam_a_um)
            self.l2 = float(lam_a_um)
            self.l3 = float(lam_a_um) / 2.0
        elif self.process_type in ("sfg", "sum_frequency"):
            if lam_b_um is None:
                raise ValueError("SFG requires two input wavelengths (lam_a, lam_b)")
            self.l1 = float(lam_a_um)
            self.l2 = float(lam_b_um)
            self.l3 = 1.0 / (1.0 / self.l1 + 1.0 / self.l2)
        elif self.process_type in ("opo", "dfg", "spdc"):
            # lam_a is pump, lam_b is signal
            if lam_b_um is None:
                raise ValueError("OPO/DFG/SPDC requires pump and signal wavelengths")
            self.l3 = float(lam_a_um)  # pump
            self.l1 = float(lam_b_um)  # signal
            if 1.0 / self.l3 <= 1.0 / self.l1:
                raise ValueError(f"Pump wavelength {self.l3} µm must be shorter than signal {self.l1} µm")
            self.l2 = 1.0 / (1.0 / self.l3 - 1.0 / self.l1)  # idler
        else:
            raise ValueError(f"Unknown process type: {process_type}")


class PhaseMatchingSolver:
    """Numerical solver for birefringent phase-matching angles and tolerances."""

    def __init__(
        self,
        index_fn: Callable[[float], Tuple[float, float, float]],
        temperature_c: float = 25.0,
        temp_derivative_fn: Optional[Callable[[float], Tuple[float, float, float]]] = None,
    ):
        """
        Args:
            index_fn: Function mapping wavelength in µm -> (nx, ny, nz)
            temperature_c: Ambient crystal temperature in Celsius
            temp_derivative_fn: Optional function mapping wavelength in µm -> (dnx/dT, dny/dT, dnz/dT)
        """
        self.index_fn = index_fn
        self.temperature_c = temperature_c
        self.temp_derivative_fn = temp_derivative_fn

    def delta_k(
        self,
        plane: str,
        angle_rad: float,
        waves: ThreeWaveProcess,
        pm_type: str = "Type-I",
    ) -> float:
        """Calculates phase mismatch Delta_k = k3 - k1 - k2 in µm^-1.
        Under normal dispersion:
            Type-I:  s + s -> f
            Type-II: s + f -> f (or f + s -> f)
        """
        s = propagation_direction(plane, angle_rad)
        optics1 = FresnelOptics(*self.index_fn(waves.l1))
        optics2 = FresnelOptics(*self.index_fn(waves.l2))
        optics3 = FresnelOptics(*self.index_fn(waves.l3))

        pm = pm_type.lower()
        if pm in ("type-i", "i", "type_1", "1"):
            p1, p2 = "s", "s"
        elif pm in ("type-iia", "iia"):
            p1, p2 = "s", "f"
        elif pm in ("type-iib", "iib"):
            p1, p2 = "f", "s"
        elif pm in ("type-ii", "ii"):
            # Default Type-II to s + f
            p1, p2 = "s", "f"
        else:
            raise ValueError(f"Unknown PM type: {pm_type}")

        n1 = optics1.index_at(s, p1)
        n2 = optics2.index_at(s, p2)
        n3 = optics3.index_at(s, "f")  # highest frequency travels in fast eigenmode

        k1 = TWO_PI * n1 / waves.l1
        k2 = TWO_PI * n2 / waves.l2
        k3 = TWO_PI * n3 / waves.l3

        return k3 - k1 - k2

    def solve_angle(
        self,
        plane: str,
        waves: ThreeWaveProcess,
        pm_type: str = "Type-I",
        angle_range_deg: Tuple[float, float] = (0.0, 90.0),
        n_scan: int = 180,
    ) -> Optional[float]:
        """Finds phase matching angle in degrees within specified plane.
        Returns angle in degrees, or None if no phase matching exists.
        """
        a_min = math.radians(angle_range_deg[0])
        a_max = math.radians(angle_range_deg[1])
        angles = np.linspace(a_min, a_max, n_scan)
        dk_vals = [self.delta_k(plane, a, waves, pm_type) for a in angles]

        # Look for zero crossings
        root = None
        for i in range(len(dk_vals) - 1):
            if dk_vals[i] * dk_vals[i + 1] <= 0:
                # Bracket found: use bisection
                left = angles[i]
                right = angles[i + 1]
                f_left = dk_vals[i]
                for _ in range(60):
                    mid = 0.5 * (left + right)
                    f_mid = self.delta_k(plane, mid, waves, pm_type)
                    if abs(f_mid) < 1e-10:
                        root = mid
                        break
                    if f_left * f_mid <= 0:
                        right = mid
                    else:
                        left = mid
                        f_left = f_mid
                root = 0.5 * (left + right)
                break

        return math.degrees(root) if root is not None else None

    def compute_bandwidths(
        self,
        plane: str,
        theta_pm_deg: float,
        waves: ThreeWaveProcess,
        pm_type: str = "Type-I",
        length_mm: float = 10.0,
    ) -> Dict[str, float]:
        """Calculates angular, spectral, and temperature acceptance bandwidths for crystal of length L.
        
        Returns:
            Dictionary with delta_theta_mrad, delta_lambda_nm, delta_temp_c, and walkoff_mrad.
        """
        l_um = length_mm * 1000.0
        theta_rad = math.radians(theta_pm_deg)

        # 1. Angular acceptance |d(Delta k) / d(theta)|
        d_theta = 1e-4  # rad
        dk_plus = self.delta_k(plane, theta_rad + d_theta, waves, pm_type)
        dk_minus = self.delta_k(plane, theta_rad - d_theta, waves, pm_type)
        grad_theta = abs(dk_plus - dk_minus) / (2.0 * d_theta)  # µm^-1 rad^-1

        delta_theta_rad = SINC_HALF_WIDTH / (grad_theta * l_um) if grad_theta > 1e-9 else float("inf")
        delta_theta_mrad = delta_theta_rad * 1000.0

        # 2. Spectral acceptance |d(Delta k) / d(lambda1)|
        d_lam = 1e-4  # µm
        w_plus = ThreeWaveProcess(waves.process_type, waves.l1 + d_lam, waves.l2 if waves.process_type != "shg" else None)
        w_minus = ThreeWaveProcess(waves.process_type, waves.l1 - d_lam, waves.l2 if waves.process_type != "shg" else None)
        dk_lp = self.delta_k(plane, theta_rad, w_plus, pm_type)
        dk_lm = self.delta_k(plane, theta_rad, w_minus, pm_type)
        grad_lam = abs(dk_lp - dk_lm) / (2.0 * d_lam)  # µm^-2

        delta_lam_um = SINC_HALF_WIDTH / (grad_lam * l_um) if grad_lam > 1e-9 else float("inf")
        delta_lam_nm = delta_lam_um * 1000.0

        # 3. Spatial walk-off for fast wave (generated wave)
        optics3 = FresnelOptics(*self.index_fn(waves.l3))
        walkoff_rad = optics3.spatial_walkoff_angle_rad(theta_rad, plane=plane, mode="fast")
        walkoff_mrad = walkoff_rad * 1000.0

        # 4. Temperature acceptance (if dn/dT provided)
        delta_temp_c = float("inf")
        if self.temp_derivative_fn:
            dt_step = 0.5  # °C
            # Perturb indices:
            dn1 = self.temp_derivative_fn(waves.l1)
            dn2 = self.temp_derivative_fn(waves.l2)
            dn3 = self.temp_derivative_fn(waves.l3)

            # d(Delta k) / dT = 2pi * [ (dn3/dT)/l3 - (dn1/dT)/l1 - (dn2/dT)/l2 ] (approximate along principal axis)
            dk_dt = TWO_PI * abs(dn3[0] / waves.l3 - dn1[0] / waves.l1 - dn2[0] / waves.l2)
            if dk_dt > 1e-12:
                delta_temp_c = SINC_HALF_WIDTH / (dk_dt * l_um)

        return {
            "theta_pm_deg": theta_pm_deg,
            "delta_theta_mrad": round(delta_theta_mrad, 3),
            "delta_lambda_nm": round(delta_lam_nm, 3),
            "walkoff_mrad": round(walkoff_mrad, 3),
            "delta_temp_c": round(delta_temp_c, 3) if not math.isinf(delta_temp_c) else None,
            "length_mm": length_mm,
        }
