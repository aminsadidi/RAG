"""Reference-database helpers (offline)."""

from pathlib import Path

from matrag.references.hitran import HitranLine, branch_j, hitran_parameter, match_line
from matrag.references.refractiveindex import read_entry
from matrag.schema import ExtractedRecord


def test_property_to_hitran_parameter():
    assert hitran_parameter("air-broadened half-width") == "gamma_air"
    assert hitran_parameter("self-broadening coefficient") == "gamma_self"
    assert hitran_parameter("temperature exponent of the air-broadened half-width") == "n_air"
    assert hitran_parameter("air pressure shift") == "delta_air"
    assert hitran_parameter("line intensity") == "sw"
    assert hitran_parameter("line center wavenumber") == "nu"
    assert hitran_parameter("refractive index") is None


def test_branch_and_j():
    assert branch_j("R(50) of the 20012-00001 band") == ("R", 50)
    assert branch_j("     P 48e     ") == ("P", 48)
    assert branch_j("the ν3 band") is None


def test_match_line_prefers_strongest():
    weak = HitranLine(5007.8, 1e-29, 0.066, 0.075, 0.74, -0.006, "R 50e", "")
    strong = HitranLine(5007.787, 5e-23, 0.0658, 0.073, 0.74, -0.0068, "R 50e", "")
    other = HitranLine(5007.79, 3e-23, 0.066, 0.075, 0.74, -0.006, "P 48e", "")
    record = ExtractedRecord(material="CO2", property="air-broadened half-width", value_text="0.0671", value=0.0671,
                             spectral_position="R(50)", evidence="", doc_id="p", node_id="p::0", pages="5",
                             evidence_verified=True, value_in_source=True)
    assert match_line(record, [weak, strong, other]) is strong


def test_read_refractiveindex_entry(tmp_path):
    entry_file = tmp_path / "data" / "main" / "CaF2" / "nk" / "Daimon-20.yml"
    entry_file.parent.mkdir(parents=True)
    entry_file.write_text("""REFERENCES: |
    M. Daimon and A. Masumura. <a href="https://doi.org/10.1364/AO.41.005275"><i>Appl. Opt.</i> (2002)</a>
COMMENTS: |
    20 °C
DATA:
  - type: formula 2
    wavelength_range: 0.138 2.326
    coefficients: 0 0.443749998 0.00178027854
""", encoding="utf-8")
    e = read_entry(entry_file, tmp_path / "data")
    assert (e.material, e.page, e.doi, e.data_types, e.wavelength_um) == \
        ("CaF2", "Daimon-20", "10.1364/AO.41.005275", "formula 2", "0.138-2.326")
    assert "Daimon" in e.reference and "<" not in e.reference


def test_plausibility_ranges():
    from matrag.profiles import PropertySpec, plausibility

    specs = [PropertySpec("air-broadened half-width", "cm-1 atm-1", (0.001, 0.5)),
             PropertySpec("temperature exponent of the air-broadened half-width", "", (-0.5, 1.5)),
             PropertySpec("Sellmeier coefficients")]
    assert plausibility("air-broadened Lorentz half-width", 0.0712, specs) is True
    assert plausibility("air-broadened half-width", 182, specs) is False  # a line count, not a width
    assert plausibility("air-broadened half-width", 71.2, specs) is False  # 10^-3 units
    assert plausibility("temperature exponent n_air", 0.74, specs) is True
    assert plausibility("line intensity", 1e-22, specs) is None  # no spec


def test_builtin_profiles_load(settings):
    from matrag.profiles import load_profile

    names = [s.name for s in load_profile(settings.model_copy(update={"corpus": "hitran"}))]
    assert "air-broadened half-width" in names
    assert load_profile(settings.model_copy(update={"corpus": "unknown"})) == []


def test_spectrum_figure_layout():
    import numpy as np

    from matrag.webapp import spectrum_figure

    nu = np.linspace(5007.0, 5008.0, 50)
    base = np.exp(-((nu - 5007.5) / 0.01) ** 2)
    assert len(spectrum_figure(nu, base, None, "t").data) == 1
    fig = spectrum_figure(nu, base, base * 1.01, "t")
    assert [trace.name for trace in fig.data][0] == "HITRAN" and len(fig.data) == 3  # + paper, + difference
