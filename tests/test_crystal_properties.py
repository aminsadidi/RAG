import json
from pathlib import Path

import yaml

from matrag.references.anisotropic import build_properties

YML = Path(__file__).parents[1] / "data/rag-optics/crystal_properties.yml"
ANISO = Path(__file__).parents[1] / "web/public/ri/aniso.json"


def test_properties_export(tmp_path):
    n = build_properties(tmp_path, YML)
    data = json.loads((tmp_path / "props.json").read_text(encoding="utf-8"))
    assert n == len(data) > 40
    assert data["BaB2O4"]["transparency_um"] == [0.189, 3.5]
    assert data["Li2B4O7"]["hygroscopic"] is False


def test_properties_name_crystals_of_the_site_and_cite_a_page():
    names = {c["material"] for c in json.loads(ANISO.read_text(encoding="utf-8"))}
    for r in yaml.safe_load(YML.read_text(encoding="utf-8")):
        assert r["material"] in names, r["material"]
        for s in r.get("sources", []):
            assert isinstance(s["doc_id"], str) and s["pdf_page"] > 0
