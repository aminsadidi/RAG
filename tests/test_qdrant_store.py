"""Text handling shared by the Qdrant export and the web app."""

import json

from matrag import web_shared
from matrag.qdrant_store import expand_query, normalize_formulas, point_id


def test_spaced_formulas_are_joined():
    assert normalize_formulas("LiB 3 O 5 crystal") == "LiB3O5 crystal"
    assert normalize_formulas("KTiOPO 4 and Eq 5 and N 2") == "KTiOPO4 and Eq 5 and N 2"
    assert normalize_formulas("BaB 2 O 4") == "BaB2O4"


def test_common_names_are_expanded():
    assert expand_query("Sellmeier BBO") == "Sellmeier BBO BaB2O4"
    assert expand_query("PPLN and LiNbO3") == "PPLN and LiNbO3"  # formula already there
    assert expand_query("ZGP") == "ZGP ZnGeP2"
    # every name of a crystal finds it, the longest name first
    assert expand_query("beta barium borate") == "beta barium borate BaB2O4"
    assert expand_query("cesium lithium borate") == "cesium lithium borate CsLiB6O10"  # not LBO
    assert expand_query("alpha-BBO") .split()[1] == "alpha-BaB2O4"  # a different crystal from BBO
    assert expand_query("band gap of the gas") == "band gap of the gas"  # GaP, GaS only in their own case
    assert expand_query("cinnabar HgS") == "cinnabar HgS"  # HgS itself, not HGS (HgGa2S4) read in any case
    assert expand_query("mercury thiogallate") == "mercury thiogallate HgGa2S4"


def test_every_crystal_name_is_unique():
    from matrag.crystal_names import CRYSTAL_NAMES

    seen = {}
    for formula, names in CRYSTAL_NAMES.items():
        for n in names:
            assert seen.setdefault(n.lower(), formula) == formula, f"{n}: {seen[n.lower()]} and {formula}"


def test_point_ids_are_stable():
    assert point_id("a::1") == point_id("a::1") != point_id("a::2")


def test_web_app_constants_are_up_to_date():
    """web/src/shared.json must be regenerated (python -m matrag.web_shared) when the Python texts change."""
    assert json.loads(web_shared.SHARED_JSON.read_text(encoding="utf-8")) == web_shared.shared()
