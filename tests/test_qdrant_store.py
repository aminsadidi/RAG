"""Text handling shared by the Qdrant export and the web app, and the export itself."""

import json

import pytest

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


# --- export: what reaches the site's collection when the knowledge base changes

class _Node:
    def __init__(self, node_id, text, **meta):
        self.node_id, self._text, self.metadata = node_id, text, {"doc_id": node_id.split("::")[0], **meta}

    def get_content(self):
        return self._text


class _KB:
    def __init__(self, nodes):
        self._nodes = nodes

    def nodes(self):
        return self._nodes


def _memory_collection(monkeypatch):
    qdrant_client = pytest.importorskip("qdrant_client")
    from qdrant_client import models

    from matrag import qdrant_store as qs

    # in memory there is no server-side BM25 model: a fixed sparse vector stands in for it
    monkeypatch.setattr(qs, "sparse_vector", lambda text: models.SparseVector(indices=[1], values=[1.0]))
    monkeypatch.setattr(qs, "chroma_embeddings", lambda kb, ids: {i: [0.1, 0.2, 0.3] for i in ids})
    return qs, qdrant_client.QdrantClient(":memory:")


def _payloads(qc, name="c"):
    points, _ = qc.scroll(name, limit=100, with_payload=True)
    return {p.payload["node_id"]: p.payload for p in points}


def test_export_keeps_enrichment_and_sends_metadata_fixes(monkeypatch):
    qs, qc = _memory_collection(monkeypatch)
    a = _Node("p1::0", "LiNbO3 Sellmeier text", citation="Old (2000)", pages="3", doi="10.1/x")
    b = _Node("p2::0", "BBO table", citation="B (2001)", pages="1")
    assert qs.export(_KB([a, b]), qc, "c") == 2
    # the enrichment scripts add their fields afterwards
    qc.set_payload("c", payload={"crystals": ["LiNbO3"], "junk": 0.1, "basis_p": "experimental"}, points=[qs.point_id("p1::0")])
    qc.set_payload("c", payload={"crystals": ["BaB2O4"]}, points=[qs.point_id("p2::0")])
    assert qs.export(_KB([a, b]), qc, "c") == 0  # nothing changed: nothing sent
    # a metadata fix (citation, removed DOI) on p1, a text change on p2
    a2 = _Node("p1::0", "LiNbO3 Sellmeier text", citation="Fixed (2000)", pages="3")
    b2 = _Node("p2::0", "BBO table, corrected", citation="B (2001)", pages="1")
    assert qs.export(_KB([a2, b2]), qc, "c") == 2
    got = _payloads(qc)
    assert got["p1::0"]["citation"] == "Fixed (2000)" and "doi" not in got["p1::0"]
    assert got["p1::0"]["crystals"] == ["LiNbO3"] and got["p1::0"]["junk"] == 0.1 and got["p1::0"]["basis_p"] == "experimental"
    assert got["p1::0"]["text"] == "LiNbO3 Sellmeier text"
    assert got["p2::0"]["text"] == "BBO table, corrected" and got["p2::0"]["crystals"] == ["BaB2O4"]
    assert qs.export(_KB([a2, b2]), qc, "c") == 0


def test_collection_indexes_crystals(monkeypatch):
    qs, qc = _memory_collection(monkeypatch)
    qs.create_collection(qc, "c", 3)
    # an older collection without the index gets it on the next export
    qc.delete_collection("c")
    from qdrant_client import models

    qc.create_collection("c", vectors_config={qs.DENSE: models.VectorParams(size=3, distance=models.Distance.COSINE)},
                         sparse_vectors_config={qs.SPARSE: models.SparseVectorParams()})
    created = []
    monkeypatch.setattr(qc, "create_payload_index", lambda name, key, field_schema: created.append(key))
    qs.create_collection(qc, "c", 3)
    assert "crystals" in created and "crystals" in qs.INDEXED_KEYS
