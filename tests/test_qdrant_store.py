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


def test_point_ids_are_stable():
    assert point_id("a::1") == point_id("a::1") != point_id("a::2")


def test_web_app_constants_are_up_to_date():
    """web/src/shared.json must be regenerated (python -m matrag.web_shared) when the Python texts change."""
    assert json.loads(web_shared.SHARED_JSON.read_text(encoding="utf-8")) == web_shared.shared()
