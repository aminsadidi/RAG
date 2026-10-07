"""Effective Nonlinear Coefficient (d_eff) Formulation for Optical Symmetries.
Computes d_eff for various crystallographic point groups (-42m, 3m, mm2, 6mm, 2, QPM)
as a function of polar angle theta and azimuthal angle phi.
"""

import math
from typing import Dict, Optional


def compute_deff(
    point_group: str,
    pm_type: str,
    theta_rad: float,
    phi_rad: float,
    d_dict: Dict[int, float],
    plane: Optional[str] = None,
) -> float:
    """Computes effective nonlinear optical coefficient d_eff in pm/V.
    
    Args:
        point_group: Crystal point group (e.g. '-42m', '3m', 'mm2', '6mm', '2', 'qpm')
        pm_type: 'type-I' ('I') or 'type-II' ('II', 'IIa', 'IIb')
        theta_rad: Polar propagation angle in radians (from z optic axis)
        phi_rad: Azimuthal propagation angle in radians (from x dielectric axis)
        d_dict: Dictionary of contracted d_ij tensor elements {ij: val_pm_V}
        plane: Optional principal plane ('xy', 'xz', 'yz') for biaxial crystals
    """
    pg = point_group.lower().strip()
    pm = pm_type.lower().strip()
    is_type_1 = pm in ("type-i", "i", "type_1", "1")

    # Helper to get d_ij with fallback
    def d(ij: int, default: float = 0.0) -> float:
        return float(d_dict.get(ij, default))

    st = math.sin(theta_rad)
    ct = math.cos(theta_rad)
    s2t = math.sin(2.0 * theta_rad)
    c2t = math.cos(2.0 * theta_rad)

    sp = math.sin(phi_rad)
    cp = math.cos(phi_rad)
    s2p = math.sin(2.0 * phi_rad)
    c2p = math.cos(2.0 * phi_rad)
    s3p = math.sin(3.0 * phi_rad)
    c3p = math.cos(3.0 * phi_rad)

    # 1. Tetragonal Chalcopyrite (-42m) (KDP, ZGP, AGS, CSP, CGA)
    if pg in ("-42m", "42m"):
        d36 = d(36, d(14, 0.0))
        if is_type_1:
            # Type-I: o + o -> e
            # deff = d36 * sin(theta) * sin(2*phi)
            return d36 * st * s2p
        else:
            # Type-II: o + e -> e
            # deff = d36 * sin(2*theta) * cos(2*phi)
            return d36 * s2t * c2p

    # 2. Trigonal (3m) (BBO, LiNbO3) - Negative Uniaxial
    elif pg == "3m":
        d22 = d(22, 0.0)
        d31 = d(31, d(15, 0.0))
        if is_type_1:
            # Type-I: o + o -> e
            # deff = d31 * sin(theta) - d22 * cos(theta) * sin(3*phi)
            return d31 * st - d22 * ct * s3p
        else:
            # Type-II: e + o -> e
            # deff = d22 * cos^2(theta) * cos(3*phi)
            return d22 * (ct ** 2) * c3p

    # 3. Orthorhombic (mm2) (KTP, LBO, KNbO3)
    elif pg == "mm2":
        d31 = d(31, 0.0)
        d32 = d(32, 0.0)
        d33 = d(33, 0.0)
        d15 = d(15, d31)
        d24 = d(24, d32)

        # In principal planes:
        if plane == "xy" or abs(ct) < 1e-4:
            # Theta = 90 deg (xy plane, propagation at azimuth phi from x)
            if is_type_1:
                # Type-I (z + z -> xy or fast):
                return d31 * (cp ** 2) + d32 * (sp ** 2)
            else:
                # Type-II in xy plane (e.g. KTP 1064 nm SHG):
                # deff = d15 * sin^2(phi) + d24 * cos^2(phi) (by Kleinman d31 sin^2 + d32 cos^2)
                return d15 * (sp ** 2) + d24 * (cp ** 2)

        elif plane == "xz" or abs(sp) < 1e-4:
            # Phi = 0 (xz plane, propagation at polar angle theta from z)
            if is_type_1:
                return d32 * st
            else:
                return d24 * st

        elif plane == "yz" or abs(cp) < 1e-4:
            # Phi = 90 deg (yz plane)
            if is_type_1:
                return d31 * st
            else:
                return d15 * st
        else:
            # General mm2 approximation
            return (d31 * (cp ** 2) + d32 * (sp ** 2)) * st

    # 4. Hexagonal (6mm) (CdS, CdSe, ZnO)
    elif pg == "6mm":
        d31 = d(31, 0.0)
        d15 = d(15, d31)
        if is_type_1:
            return d31 * st
        else:
            return d15 * s2t

    # 5. Monoclinic (2) (BiBO)
    elif pg == "2":
        d12 = d(12, 0.0)
        d22 = d(22, 0.0)
        d32 = d(32, 0.0)
        if plane == "xz" or abs(sp) < 1e-4:
            # Type-I in xz plane:
            return d12 * st + d32 * ct
        elif plane == "xy":
            return d22 * sp
        else:
            return math.sqrt((d12 * st)**2 + (d22 * sp)**2 + (d32 * ct)**2)

    # 6. Quasi-Phase Matching (QPM 1st-order)
    elif pg == "qpm":
        # 1st-order Fourier poling efficiency is 2/pi ~ 0.6366
        d_dom = d(33, d(36, d(14, 1.0)))
        return (2.0 / math.pi) * d_dom

    else:
        # Fallback heuristic: maximum d component
        max_d = max([abs(v) for v in d_dict.values()]) if d_dict else 1.0
        return max_d * st


class EffectiveNonlinearCoefficient:
    """Class wrapper for computing effective nonlinear coefficients across configurations."""

    def __init__(self, point_group: str, d_dict: Dict[int, float]):
        self.point_group = point_group
        self.d_dict = d_dict

    def evaluate(self, pm_type: str, theta_deg: float, phi_deg: float = 0.0, plane: Optional[str] = None) -> float:
        """Evaluates d_eff with angles in degrees."""
        theta_rad = math.radians(theta_deg)
        phi_rad = math.radians(phi_deg)
        return compute_deff(
            point_group=self.point_group,
            pm_type=pm_type,
            theta_rad=theta_rad,
            phi_rad=phi_rad,
            d_dict=self.d_dict,
            plane=plane,
        )
