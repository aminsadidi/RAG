"""The OCR workflow puts a paper's new text on the site without ever leaving the paper without text."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "ocr_gh"))
import common  # noqa: E402


class _Node:
    def __init__(self, node_id, text, **meta):
        self.node_id, self._text = node_id, text
        self.metadata = {"doc_id": node_id.split("::")[0], "source_type": "full_text_pdf", **meta}

    def get_content(self, metadata_mode=None):
        return self._text


@pytest.fixture
def site(monkeypatch):
    qdrant_client = pytest.importorskip("qdrant_client")
    from qdrant_client import models

    from matrag import qdrant_store as qs

    monkeypatch.setattr(qs, "sparse_vector", lambda text: models.SparseVector(indices=[1], values=[1.0]))
    qc = qdrant_client.QdrantClient(":memory:")
    qs.create_collection(qc, common.NAME, 3)
    return qs, qc


def _points(qs, nodes):
    return list(qs.iter_points(nodes, {n.node_id: [0.1, 0.2, 0.3] for n in nodes}))


def _texts(qc, doc_id):
    return {p.payload["node_id"]: p.payload for p in common.full_text_points(qc, doc_id)}


def _old_paper(qs, qc):
    old = [_Node("p1::0", "garbled", citation="A (2000)", pdf_mismatch=True, conversion="ocr"),
           _Node("p1::1", "Sellmeier of LiNbO3", citation="A (2000)", pdf_mismatch=True, conversion="ocr"),
           _Node("p1::2", "references", citation="A (2000)", pdf_mismatch=True, conversion="ocr")]
    qc.upsert(common.NAME, points=_points(qs, old), wait=True)
    qc.set_payload(common.NAME, payload={"drive_id": "D1"}, points=[qs.point_id(n.node_id) for n in old])
    qc.set_payload(common.NAME, payload={"crystals": ["LiNbO3"], "junk": 0.1, "basis_p": "experimental", "has": ["n"]},
                   points=[qs.point_id("p1::1")])
    qc.set_payload(common.NAME, payload={"crystals": ["BaB2O4"], "junk": 0.9}, points=[qs.point_id("p1::0")])
    return common.full_text_points(qc, "p1")


def test_new_text_replaces_old_and_keeps_paper_and_passage_fields(site):
    qs, qc = site
    old = _old_paper(qs, qc)
    # the new conversion: two passages; the second holds the same text as the old p1::1, now at position 0
    new = [_Node("p1::0", "Sellmeier of LiNbO3", citation="A (2000)"), _Node("p1::1", "a new readable page", citation="A (2000)")]
    common.replace_points(qc, "p1", _points(qs, new), old, ocr=True)
    got = _texts(qc, "p1")
    assert set(got) == {"p1::0", "p1::1"}  # p1::2 is gone
    assert got["p1::0"]["text"] == "Sellmeier of LiNbO3" and got["p1::1"]["text"] == "a new readable page"
    for p in got.values():
        assert p["drive_id"] == "D1" and p["pdf_mismatch"] is True and p["conversion"] == "ocr" and p["ocr"] is True
    # enrichment follows the text, not the position: the old p1::0 (garbled, junk 0.9) does not label the new p1::0
    assert got["p1::0"]["crystals"] == ["LiNbO3"] and got["p1::0"]["junk"] == 0.1
    assert got["p1::0"]["basis_p"] == "experimental" and got["p1::0"]["has"] == ["n"]
    assert "crystals" not in got["p1::1"] and "junk" not in got["p1::1"]


def test_a_failed_upload_leaves_the_old_text_in_place(site, monkeypatch):
    qs, qc = site
    old = _old_paper(qs, qc)
    new = [_Node(f"p1::{i}", f"page {i}", citation="A (2000)") for i in range(5)]
    calls = []

    def upsert(name, points, wait):
        calls.append(len(points))
        if len(calls) == 2:
            raise ConnectionError("network down")
        return type(qc).upsert(qc, name, points=points, wait=wait)

    monkeypatch.setattr(qc, "upsert", upsert)
    with pytest.raises(ConnectionError):
        common.replace_points(qc, "p1", _points(qs, new), old, batch=2)
    got = _texts(qc, "p1")
    # nothing was deleted: the paper still has every passage (the first batch already new, the rest old)
    assert set(got) == {"p1::0", "p1::1", "p1::2"}
    assert got["p1::2"]["text"] == "references"


def test_other_papers_are_untouched(site):
    qs, qc = site
    old = _old_paper(qs, qc)
    qc.upsert(common.NAME, points=_points(qs, [_Node("p2::0", "other paper")]), wait=True)
    common.replace_points(qc, "p1", _points(qs, [_Node("p1::0", "only page")]), old)
    assert set(_texts(qc, "p2")) == {"p2::0"}
    assert set(_texts(qc, "p1")) == {"p1::0"} and "ocr" not in _texts(qc, "p1")["p1::0"]
