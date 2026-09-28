import numpy as np

from matrag.dispersion import DispersionFormula, PoleTerm, PowerTerm, check_formula, refractiveindex_info, table

# refractiveindex.info BaB2O4/Tamosauskas-e (formula 2) and CaF2/Daimon-20 (formula 2).
BBO_E = [0, 1.151075, 0.007142, 0.21803, 0.02259, 0.656, 263]
CAF2 = [0, 0.443749998, 0.00178027854, 0.444930066, 0.00788536061, 0.150133991, 0.0124119491,
        8.85319946, 2752.28175]


def bbo_e_from_paper() -> DispersionFormula:
    # As written in arXiv:2111.01212: n_e = sqrt(1 + λ²·1.151075/(λ²−0.007142) + λ²·0.21803/(λ²−0.02259) + λ²·0.656/(λ²−263))
    return DispersionFormula(
        material="BBO", axis="e", constant=1.0, wavelength_min_um=0.188, wavelength_max_um=5.2,
        pole_terms=[PoleTerm(coefficient=b, pole=c) for b, c in [(1.151075, 0.007142), (0.21803, 0.02259), (0.656, 263)]],
        equation_text="RefracInd_e=sqrt(1+ inputValues.^2 *1.151075 ./ (inputValues.^2 -0.007142) + ...)",
    )


def test_known_values():
    # BBO n_e at 1064 nm: 1.5421 from this formula; other BBO formulas give ~1.5425
    assert abs(refractiveindex_info(2, BBO_E, 1.064) - 1.5421) < 2e-4
    assert abs(refractiveindex_info(2, CAF2, 0.5893) - 1.4338) < 2e-4  # CaF2 at the sodium D line


def test_paper_form_equals_database_form():
    lam = np.linspace(0.2, 5.0, 50)
    assert np.allclose(bbo_e_from_paper().refractive_index(lam), refractiveindex_info(2, BBO_E, lam), atol=1e-12)


def test_resonance_wavelength_and_nm_units():
    lam = np.array([0.5, 1.0, 1.5])
    squared_pole = DispersionFormula(material="x", constant=1.0, equation_text="",
                                     pole_terms=[PoleTerm(coefficient=0.6, pole=0.0081)])
    as_wavelength = DispersionFormula(material="x", constant=1.0, equation_text="",
                                      pole_terms=[PoleTerm(coefficient=0.6, pole=0.09, pole_is_wavelength=True)])
    in_nm = DispersionFormula(material="x", constant=1.0, equation_text="", wavelength_unit="nm",
                              pole_terms=[PoleTerm(coefficient=0.6, pole=90.0, pole_is_wavelength=True)])
    ref = squared_pole.refractive_index(lam)
    assert np.allclose(as_wavelength.refractive_index(lam), ref) and np.allclose(in_nm.refractive_index(lam), ref)


def test_cauchy_and_checks():
    cauchy = DispersionFormula(material="glass", squared=False, constant=1.5, equation_text="",
                               power_terms=[PowerTerm(coefficient=0.004, power=-2)])
    assert abs(cauchy.refractive_index(0.5) - 1.516) < 1e-12
    assert check_formula(bbo_e_from_paper()) == []
    broken = bbo_e_from_paper().model_copy(update={"constant": -5.0})
    assert check_formula(broken)
    assert table(cauchy, [0.5])[0] == {"wavelength_um": 0.5, "n": 1.516}


def leviton_caf2() -> DispersionFormula:
    """Leviton et al., arXiv:0805.0096, Table 5: n² − 1 = Σ S_i(T) λ² / (λ² − λ_i(T)²)."""
    S = [[1.04834, -2.21666E-04, -6.73446E-06, 1.50138E-08, -2.77255E-11],
         [-3.32723E-03, 2.34683E-04, 6.55744E-06, -1.47028E-08, 2.75023E-11],
         [3.72693, 1.49844E-02, -1.47511E-04, 5.54293E-07, -7.17298E-10]]
    L = [[7.94375E-02, -2.20758E-04, 2.07862E-06, -9.60254E-09, 1.31401E-11],
         [0.258039, -2.12833E-03, 1.20393E-05, -3.06973E-08, 2.79793E-11],
         [34.0169, 6.26867E-02, -6.14541E-04, 2.31517E-06, -2.99638E-09]]
    return DispersionFormula(
        material="CaF2", constant=1.0, wavelength_min_um=0.4, wavelength_max_um=5.6, equation_text="Table 5",
        pole_terms=[PoleTerm(coefficient=s[0], coefficient_T=s, pole=l[0], pole_T=l, pole_is_wavelength=True)
                    for s, l in zip(S, L)])


def test_temperature_dependent_sellmeier_reproduces_the_papers_table():
    caf2 = leviton_caf2()
    assert caf2.temperature_dependent
    # Table 1 of the same paper: n(0.40 µm, 295 K) = 1.44221, n(2.00 µm, 30 K) = 1.42611
    assert abs(caf2.refractive_index(0.40, 295) - 1.44221) < 2e-5
    assert abs(caf2.refractive_index(2.00, 30) - 1.42611) < 2e-5
    assert check_formula(caf2)  # no temperature given -> reported, not crashing
    assert check_formula(caf2.model_copy(update={"temperature_K": 295})) == []
