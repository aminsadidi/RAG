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
    assert data["LiB3O5"]["damage"]["threshold"] == "19 GW/cm²"
    assert "photorefractive" in data["LiNbO3"]["notes"][0]["fa"]
    assert data["BaB2O4"]["class"]["value"] == "basic" and data["CsB3O5"]["class"]["value"] == "rare"
    assert data["GaAs"]["min_pump_um"]["value"] == 1.73 and data["GaP"]["transparency_um"] == [0.57, 13.2]
    assert data["Li2B4O7"]["hygroscopic"] == "slight" and data["CsLiB6O10"]["hygroscopic"] == "strong"
    # a paper outside the collection, cited by its DOI (Nature 2026, ABF): read from the published page
    assert data["NH4B4O6F"]["damage"]["tier"] == "verified" and "79.8" in data["NH4B4O6F"]["thermal_expansion"]["value"]


def test_properties_name_crystals_of_the_site_and_cite_a_page():
    names = {c["material"] for c in json.loads(ANISO.read_text(encoding="utf-8"))}
    for r in yaml.safe_load(YML.read_text(encoding="utf-8")):
        assert r["material"] in names, r["material"]
        for s in r.get("sources", []) + r.get("notes", []) + [r[k] for k in ("hygroscopic_source", "damage", "min_pump_um", "thermal_conductivity", "class") if k in r]:
            assert isinstance(s.get("doc_id") or s.get("doi"), str) and s["pdf_page"] > 0
