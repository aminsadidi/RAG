"""Fresnel Optics & Anisotropic Wave Propagation.
Solves Fresnel's equation of wave normals for arbitrary biaxial and uniaxial crystals,
computing refractive eigen-indices, polarization eigenvectors, and spatial walk-off angles.
"""

import math
import numpy as np
from typing import Tuple, List, Union


def propagation_direction(plane: str, angle_rad: float) -> np.ndarray:
    """Returns the unit propagation vector s in a principal plane.
    
    Args:
        plane: 'xy', 'yz', or 'xz'
        angle_rad: Angle in radians (phi for xy, theta for yz and xz)
    """
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    if plane == "xy":
        # theta = pi/2, phi = angle
        return np.array([c, s, 0.0], dtype=float)
    elif plane == "yz":
        # phi = pi/2, theta = angle from z
        return np.array([0.0, s, c], dtype=float)
    elif plane == "xz":
        # phi = 0, theta = angle from z
        return np.array([s, 0.0, c], dtype=float)
    else:
        raise ValueError(f"Unknown principal plane: {plane}. Must be 'xy', 'yz', or 'xz'.")


def spherical_to_cartesian(theta_rad: float, phi_rad: float) -> np.ndarray:
    """Converts spherical angles (theta from z, phi from x) to unit propagation vector."""
    st = math.sin(theta_rad)
    ct = math.cos(theta_rad)
    cp = math.cos(phi_rad)
    sp = math.sin(phi_rad)
    return np.array([st * cp, st * sp, ct], dtype=float)


class FresnelOptics:
    """Optical index ellipsoid solver for anisotropic dielectric media."""

    def __init__(self, nx: float, ny: float, nz: float):
        self.nx = float(nx)
        self.ny = float(ny)
        self.nz = float(nz)
        self.is_uniaxial = abs(self.nx - self.ny) < 1e-5
        self.is_isotropic = self.is_uniaxial and abs(self.ny - self.nz) < 1e-5

    def eigen_indices(self, s: Union[np.ndarray, List[float]]) -> Tuple[float, float]:
        """Calculates the slow (higher index) and fast (lower index) refractive eigen-indices
        for propagation direction vector s.
        
        Returns:
            Tuple of (n_slow, n_fast) where n_slow >= n_fast.
        """
        sx, sy, sz = float(s[0]), float(s[1]), float(s[2])
        # Normalize s
        norm = math.sqrt(sx * sx + sy * sy + sz * sz)
        if norm > 0:
            sx, sy, sz = sx / norm, sy / norm, sz / norm

        ax = self.nx ** -2
        ay = self.ny ** -2
        az = self.nz ** -2

        b = sx * sx * (ay + az) + sy * sy * (ax + az) + sz * sz * (ax + ay)
        c = sx * sx * ay * az + sy * sy * ax * az + sz * sz * ax * ay

        disc = max(0.0, b * b - 4.0 * c)
        r = math.sqrt(disc)

        # 1/n^2 roots:
        u_slow = (b - r) / 2.0  # smaller 1/n^2 -> larger n (slow)
        u_fast = (b + r) / 2.0  # larger 1/n^2 -> smaller n (fast)

        n_slow = 1.0 / math.sqrt(max(1e-12, u_slow))
        n_fast = 1.0 / math.sqrt(max(1e-12, u_fast))

        return n_slow, n_fast

    def index_at(self, s: np.ndarray, polarization: str) -> float:
        """Returns refractive index for specified polarization eigenmode: 'slow' ('s') or 'fast' ('f')."""
        n_slow, n_fast = self.eigen_indices(s)
        pol = polarization.lower()
        if pol in ("s", "slow", "ordinary", "o"):
            return n_slow
        elif pol in ("f", "fast", "extraordinary", "e"):
            return n_fast
        else:
            raise ValueError(f"Unknown polarization: {polarization}. Use 'slow'/'s' or 'fast'/'f'.")

    def spatial_walkoff_angle_rad(self, theta_rad: float, plane: str = "xz", mode: str = "fast") -> float:
        """Calculates spatial walk-off angle rho between wavevector k and Poynting vector S.
        For uniaxial crystals in the xz plane:
        tan(rho) = (ne(theta)^2 / 2) * |1/ne^2 - 1/no^2| * sin(2*theta).
        """
        s = propagation_direction(plane, theta_rad)
        n_slow, n_fast = self.eigen_indices(s)
        n_curr = n_fast if mode in ("f", "fast") else n_slow

        # Exact Poynting walkoff for arbitrary direction:
        # In a principal plane (e.g. xz):
        # Ordinary ray has zero walk-off:
        if self.is_uniaxial:
            no = self.nx
            ne = self.nz
            # If ray is ordinary:
            if abs(n_curr - no) < 1e-5:
                return 0.0
            # Extraordinary ray:
            tan_rho = (n_curr ** 2 / 2.0) * abs(ne ** -2 - no ** -2) * math.sin(2.0 * theta_rad)
            return math.atan(tan_rho)

        # General biaxial approximation in principal plane:
        if plane == "xz":
            tan_rho = (n_curr ** 2 / 2.0) * abs(self.nz ** -2 - self.nx ** -2) * math.sin(2.0 * theta_rad)
            return math.atan(tan_rho)
        elif plane == "yz":
            tan_rho = (n_curr ** 2 / 2.0) * abs(self.nz ** -2 - self.ny ** -2) * math.sin(2.0 * theta_rad)
            return math.atan(tan_rho)
        else:  # xy
            tan_rho = (n_curr ** 2 / 2.0) * abs(self.ny ** -2 - self.nx ** -2) * math.sin(2.0 * theta_rad)
            return math.atan(tan_rho)
