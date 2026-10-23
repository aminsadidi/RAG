"""dij.json export: the nonlinear coefficients of nonlinear_coefficients.yml, with partial tensors flagged."""
import json
from pathlib import Path

from matrag.references.anisotropic import build_nonlinear

YML = Path(__file__).resolve().parents[1] / "data" / "rag-optics" / "nonlinear_coefficients.yml"


def test_partial_tensors_are_flagged(tmp_path):
    n = build_nonlinear(tmp_path, YML)
    data = json.loads((tmp_path / "dij.json").read_text(encoding="utf-8"))
    assert n == len(data)
    partial = {m for m, v in data.items() if v.get("partial")}
    assert partial == {"BaGa4S7", "NH4B4O6F", "BaGa2GeSe6"}  # BaGa4Se7: full tensor in the dielectric frame (Guo et al. 2022); ABF: only d32 measured; BaGa2GeSe6: only d11
    assert data["BaGa4Se7"]["d"]["23"] == -14.2 and data["BaGa4Se7"]["d"]["31"] == 1.5
    assert all("partial" not in v for m, v in data.items() if m not in partial)
    assert data["BaGa4S7"]["d"]["31"] == 5.1 and data["BaGa4S7"]["d"]["32"] == 5.7 and data["BaGa4S7"]["frame"]


def test_new_coefficients(tmp_path):
    build_nonlinear(tmp_path, YML)
    data = json.loads((tmp_path / "dij.json").read_text(encoding="utf-8"))
    # Sanford et al. (2005): χ31 = 5.7, χ33 = −9.2 pm/V with χ = 2d; 6mm + Kleinman
    gan = data["GaN"]["d"]
    assert gan["31"] == gan["32"] == gan["15"] == gan["24"] == 2.85 and gan["33"] == -4.6
    # Wagner et al. (1998): |d| = 52 pm/V at 1.321 µm; −43m
    assert data["ZnTe"]["point_group"] == "-43m" and set(data["ZnTe"]["d"].values()) == {52.0}


def test_every_entry_has_sources_with_pages(tmp_path):
    build_nonlinear(tmp_path, YML)
    for m, v in json.loads((tmp_path / "dij.json").read_text(encoding="utf-8")).items():
        assert v["d"], m
        assert v["sources"] and all("cite" in s for s in v["sources"]), m
