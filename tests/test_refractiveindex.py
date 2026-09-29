"""Reading the refractiveindex.info database, in its old (database/data/main) and new (database/main) layouts."""

import pytest

from matrag.benchmark import formula_references
from matrag.references.refractiveindex import find_entries, iter_entries

ENTRY = """REFERENCES: "C. Chen et al. New nonlinear-optical crystal: LiB<sub>3</sub>O<sub>5</sub>.
  <a href=\\"https://doi.org/10.1364/JOSAB.6.000616\\">J. Opt. Soc. Am. B <b>6</b>, 616 (1989)</a>"
DATA:
  - type: formula 4
    wavelength_range: 0.3 1.6
    coefficients: 2.4542 0.01125 0 0.01135 1 0 0 0 1 -0.01388 2
"""


@pytest.fixture(params=["old", "new"])
def database(tmp_path, request):
    shelves = tmp_path / "database" / ("data" if request.param == "old" else "")
    path = shelves / "main" / "LiB3O5" / "nk" / "Chen-alpha.yml"
    path.parent.mkdir(parents=True)
    path.write_text(ENTRY, encoding="utf-8")
    return tmp_path / "database"


def test_both_layouts_are_read(database):
    [entry] = list(iter_entries(database))
    assert entry.path == "main/LiB3O5/nk/Chen-alpha.yml" and entry.doi == "10.1364/JOSAB.6.000616"
    [data] = find_entries(database, doi="10.1364/JOSAB.6.000616")
    assert data.formula_type == 4 and data.refractive_index([1.064])[0] == pytest.approx(1.56478, abs=1e-4)
    refs = formula_references(database, {"10.1364_josab.6.000616", "other"})
    assert list(refs) == ["10.1364_josab.6.000616"]
