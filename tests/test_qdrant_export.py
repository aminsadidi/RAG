"""export-qdrant keeps what other steps added to the points and sends a metadata fix without re-uploading."""
from types import SimpleNamespace

from matrag import qdrant_store as qs


class Node:
    def __init__(self, nid, text, **meta):
        self.node_id, self.text, self.metadata = nid, text, {"doc_id": "d1", **meta}

    def get_content(self, metadata_mode=None):
        return self.text


class FakeKB:
    def __init__(self, nodes):
        self._nodes = nodes
        self.vector_store = SimpleNamespace(_collection=SimpleNamespace(
            get=lambda ids, include: {"ids": ids, "embeddings": [[0.1, 0.2] for _ in ids]}))

    def nodes(self):
        return self._nodes


class FakeQdrant:
    def __init__(self, points):
        self.points = points  # id -> payload
        self.upserted, self.updated = [], []

    def collection_exists(self, name):
        return True

    def scroll(self, name, limit, offset, with_vectors, with_payload):
        return [SimpleNamespace(id=i, payload={k: v for k, v in p.items() if k in with_payload}) for i, p in self.points.items()], None

    def upsert(self, name, points, wait):
        self.upserted += points
        for p in points:
            self.points[str(p.id)] = p.payload

    def batch_update_points(self, name, update_operations, wait):
        for op in update_operations:
            for pid in op.set_payload.points:
                self.updated.append(pid)
                self.points[pid] = {**self.points[pid], **op.set_payload.payload}

    def delete(self, name, points_selector, wait):
        for i in points_selector.points:
            self.points.pop(i, None)


def site_point(node, **extra):
    return {**qs.point_payload(node), **extra}


def test_enrichment_kept_and_metadata_fix_sent_as_payload_update():
    same = Node("n1", "BBO text", year=1990)
    changed_meta = Node("n2", "LBO text", year=2001)
    changed_text = Node("n3", "new KTP text", year=1995)
    old_meta = Node("n2", "LBO text", year=2000)
    old_text = Node("n3", "old KTP text", year=1995)
    qc = FakeQdrant({
        qs.point_id("n1"): site_point(same, crystals=["BaB2O4"], junk=0.1),
        qs.point_id("n2"): site_point(old_meta, crystals=["LiB3O5"], basis_p="experimental"),
        qs.point_id("n3"): site_point(old_text, crystals=["KTiOPO4"], drive_id="D"),
    })
    sent = qs.export(FakeKB([same, changed_meta, changed_text]), qc, "c")
    assert sent == 1 and [str(p.id) for p in qc.upserted] == [qs.point_id("n3")]  # only the new text is re-sent
    assert qc.updated == [qs.point_id("n2")]  # the year fix as a payload update
    p2, p3 = qc.points[qs.point_id("n2")], qc.points[qs.point_id("n3")]
    assert p2["year"] == 2001 and p2["crystals"] == ["LiB3O5"] and p2["basis_p"] == "experimental"
    assert p3["text"] == "new KTP text" and p3["crystals"] == ["KTiOPO4"] and p3["drive_id"] == "D"
    assert qc.points[qs.point_id("n1")]["junk"] == 0.1


def test_download_arxiv_takes_only_arxiv_ids(tmp_path):
    import pytest

    pytest.importorskip("chromadb")  # the pipeline needs the index's packages
    from matrag.pipeline import Workspace

    ws = Workspace.__new__(Workspace)
    ws.settings = SimpleNamespace(raw_pdf_dir=tmp_path)
    for bad in ("paper.pdf", "../../etc/passwd", "2111.01212/../x", "abc"):
        with pytest.raises(ValueError, match="not an arXiv id"):
            ws.download_arxiv(bad)
    (tmp_path / "arxiv_hep-th_9901001.pdf").write_bytes(b"%PDF")  # cached: no download, no folder from the "/"
    assert ws.download_arxiv("hep-th/9901001") == tmp_path / "arxiv_hep-th_9901001.pdf"
