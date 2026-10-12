"""Dispersion formulas: refractive index n(λ) from a few coefficients.

Papers often report optical constants only as plots, but give the fitted
dispersion formula (e.g. Sellmeier) as coefficients in a table or equation.
Those coefficients can be extracted as text and turned into a table of n(λ)
at any wavelength, instead of reading values off a figure.

Two representations are used:

- ``DispersionFormula``: the general form extracted from papers,
      n^2 (or n) = A + Σ_i B_i λ^p_i / (λ^2 − C_i) + Σ_j E_j λ^q_j,
  with λ in the paper's unit and C_i either given directly or as a resonance
  wavelength λ_i (then C_i = λ_i^2).
- The nine formula types of the refractiveindex.info database, with λ in µm,
  implemented from the database's own definition document
  (database/doc/Dispersion formulas.pdf).
"""

from typing import Literal

import numpy as np
from pydantic import BaseModel, Field

# --- formulas as extracted from papers --------------------------------------------


class PoleTerm(BaseModel):
    coefficient: float = Field(description="B_i, the term's numerator coefficient (its constant part if it depends on T).")
    numerator_power: int = Field(2, description="Power of λ in the numerator: 2 for B·λ²/(λ²−C), 0 for B/(λ²−C).")
    pole: float = Field(description="C_i in the denominator (λ² − C_i), or the resonance wavelength λ_i "
                                    "(its constant part if it depends on T).")
    pole_is_wavelength: bool = Field(False, description="True if 'pole' is a resonance wavelength λ_i (denominator λ² − λ_i²).")
    coefficient_T: list[float] = Field(default_factory=list, description=(
        "Only for temperature-dependent coefficients: polynomial coefficients of B_i(T) for T^0, T^1, T^2, ... "
        "(T in kelvin). Leave empty if B_i is a constant."))
    pole_T: list[float] = Field(default_factory=list, description=(
        "Only for temperature-dependent poles: polynomial coefficients of C_i(T) or λ_i(T) for T^0, T^1, T^2, ..."))

    def values_at(self, temperature_K: float | None) -> tuple[float, float]:
        """(B_i, C_i) at a temperature, with C_i as the squared pole."""
        def poly(constant, coefficients):
            if not coefficients:
                return constant
            if temperature_K is None:
                raise ValueError("This formula depends on temperature: give temperature_K.")
            return sum(c * temperature_K ** j for j, c in enumerate(coefficients))

        b = poly(self.coefficient, self.coefficient_T)
        c = poly(self.pole, self.pole_T)
        return b, (c ** 2 if self.pole_is_wavelength else c)


class PowerTerm(BaseModel):
    coefficient: float = Field(description="E_j in E_j·λ^q (e.g. −0.01 for '− 0.01 λ²').")
    power: float = Field(description="q, e.g. 2 for λ², −2 for 1/λ², −4 for 1/λ⁴.")


class DispersionFormula(BaseModel):
    material: str = Field(description="Material, e.g. 'BBO', 'CaF2', 'LiNbO3'.")
    axis: str = Field("", description="Polarization or axis: 'o', 'e', 'x', 'y', 'z', or '' if isotropic.")
    squared: bool = Field(True, description="True if the formula gives n² (Sellmeier), False if it gives n (Cauchy).")
    constant: float = Field(description="A: the constant term of n² (or n). For 'n² − 1 = …' forms use 1 + (constant on the right).")
    pole_terms: list[PoleTerm] = Field(default_factory=list)
    power_terms: list[PowerTerm] = Field(default_factory=list)
    wavelength_unit: Literal["um", "nm"] = Field("um", description="Unit of λ in the formula.")
    wavelength_min_um: float | None = Field(None, description="Lower end of the stated validity range, in µm.")
    wavelength_max_um: float | None = Field(None, description="Upper end of the stated validity range, in µm.")
    temperature_K: float | None = Field(None, description="Temperature the coefficients apply to, if stated.")
    equation_text: str = Field(description="The formula and coefficients copied verbatim from the text.")

    @property
    def temperature_dependent(self) -> bool:
        return any(t.coefficient_T or t.pole_T for t in self.pole_terms)

    def refractive_index(self, wavelength_um, temperature_K: float | None = None) -> np.ndarray:
        """n(λ); temperature-dependent formulas use ``temperature_K`` (default: the formula's own)."""
        temperature_K = temperature_K if temperature_K is not None else self.temperature_K
        lam = np.asarray(wavelength_um, dtype=float) * (1000.0 if self.wavelength_unit == "nm" else 1.0)
        value = np.full_like(lam, self.constant)
        for t in self.pole_terms:
            b, pole = t.values_at(temperature_K)
            value = value + b * lam ** t.numerator_power / (lam ** 2 - pole)
        for t in self.power_terms:
            value = value + t.coefficient * lam ** t.power
        if not self.squared:
            return value
        with np.errstate(invalid="ignore"):
            return np.sqrt(value)  # NaN where n² < 0 (non-physical)

    def valid_range_um(self, default: tuple[float, float] = (0.4, 2.0)) -> tuple[float, float]:
        return (self.wavelength_min_um or default[0], self.wavelength_max_um or default[1])


def check_formula(formula: DispersionFormula, n_min: float = 1.0, n_max: float = 5.0,
                  max_slope_per_um: float = 1.0) -> list[str]:
    """Physical sanity problems of a formula over its validity range (empty list: looks fine)."""
    if not formula.pole_terms and not formula.power_terms:
        return ["no wavelength-dependent terms (only a constant)"]
    lo, hi = formula.valid_range_um()
    lam = np.linspace(lo, hi, 400)
    try:
        n = formula.refractive_index(lam)
    except ValueError as e:  # e.g. temperature-dependent without a temperature
        return [str(e)]
    problems = []
    if np.isnan(n).any():
        problems.append("n² < 0 somewhere in the range")
    finite = n[np.isfinite(n)]
    if finite.size and (finite.min() < n_min or finite.max() > n_max):
        problems.append(f"n outside [{n_min}, {n_max}]: {finite.min():.3f}–{finite.max():.3f}")
    # Away from absorption edges n changes slowly with λ (|dn/dλ| is typically < 0.3 µm⁻¹ in the
    # visible and infrared); a much steeper curve usually means a misread formula.
    visible_ir = lam >= max(lo, 0.4)
    if visible_ir.sum() > 2 and np.isfinite(n[visible_ir]).all():
        slope = np.abs(np.gradient(n[visible_ir], lam[visible_ir])).max()
        if slope > max_slope_per_um:
            problems.append(f"unusually steep dispersion: |dn/dλ| up to {slope:.2f} µm⁻¹")
    scale = 1000.0 if formula.wavelength_unit == "nm" else 1.0
    for t in formula.pole_terms:
        _, pole = t.values_at(formula.temperature_K)
        if pole > 0 and lo * scale < np.sqrt(pole) < hi * scale:
            problems.append(f"resonance at {np.sqrt(pole) / scale:.3f} µm inside the range")
    return problems


def table(formula_or_fn, wavelengths_um) -> list[dict]:
    """[{wavelength_um, n}, ...] for a formula (or any callable λ -> n)."""
    fn = formula_or_fn.refractive_index if hasattr(formula_or_fn, "refractive_index") else formula_or_fn
    lam = np.asarray(wavelengths_um, dtype=float)
    return [{"wavelength_um": round(float(l), 6), "n": round(float(v), 6)} for l, v in zip(lam, fn(lam))]


# --- refractiveindex.info formula types (λ in µm) ---------------------------------


def _pad(c, size=17):
    c = list(c) + [0.0] * (size - len(c))
    return np.array(c, dtype=float)


def refractiveindex_info(formula_type: int, coefficients, wavelength_um) -> np.ndarray:
    """n(λ) for refractiveindex.info formula types 1-9 (coefficients C1..Cn as in the YAML files), and type 10
    (two poles with free exponents, for formulas read from papers: data/<corpus>/paper_formulas.yml)."""
    lam = np.asarray(wavelength_um, dtype=float)
    c = _pad(coefficients)
    C = lambda i: c[i - 1]  # noqa: E731  (1-based, as in the definition document)
    l2 = lam ** 2
    if formula_type in (1, 2):  # Sellmeier; type 1 has squared poles
        n2 = 1 + C(1)
        for i in range(2, 17, 2):
            pole = C(i + 1) ** 2 if formula_type == 1 else C(i + 1)
            if C(i):
                n2 = n2 + C(i) * l2 / (l2 - pole)
        return np.sqrt(n2)
    if formula_type == 3:  # polynomial
        n2 = C(1) + sum(C(i) * lam ** C(i + 1) for i in range(2, 17, 2) if C(i))
        return np.sqrt(n2)
    if formula_type == 4:  # RefractiveIndex.INFO
        # a term with C2 or C6 = 0 is absent (its pole C4^C5 or C8^C9 would be 0^0 = 1, a 0/0 at λ = 1 µm)
        n2 = C(1) + sum(C(i) * lam ** C(i + 1) / (l2 - C(i + 2) ** C(i + 3)) for i in (2, 6) if C(i))
        n2 = n2 + sum(C(i) * lam ** C(i + 1) for i in range(10, 17, 2) if C(i))
        return np.sqrt(n2)
    if formula_type == 5:  # Cauchy
        return C(1) + sum(C(i) * lam ** C(i + 1) for i in range(2, 11, 2) if C(i))
    if formula_type == 6:  # gases
        return 1 + C(1) + sum(C(i) / (C(i + 1) - lam ** -2) for i in range(2, 11, 2) if C(i))
    if formula_type == 7:  # Herzberger
        d = 1 / (l2 - 0.028)
        return C(1) + C(2) * d + C(3) * d ** 2 + C(4) * l2 + C(5) * l2 ** 2 + C(6) * l2 ** 3
    if formula_type == 8:  # Retro: (n²−1)/(n²+2) = …
        r = C(1) + C(2) * l2 / (l2 - C(3)) + C(4) * l2
        return np.sqrt((1 + 2 * r) / (1 - r))
    if formula_type == 9:  # Exotic
        n2 = C(1) + C(2) / (l2 - C(3)) + C(4) * (lam - C(5)) / ((lam - C(5)) ** 2 + C(6))
        return np.sqrt(n2)
    if formula_type == 10:  # not a refractiveindex.info type: poles with free exponents (Fève et al. 2000)
        n2 = C(1) + C(2) * lam ** C(3) / (lam ** C(3) - C(4)) + C(5) * lam ** C(6) / (lam ** C(6) - C(7))
        return np.sqrt(n2)
    raise ValueError(f"Unknown refractiveindex.info formula type {formula_type}")
