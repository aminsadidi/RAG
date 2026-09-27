"""End-to-end test of ingest -> index -> retrieve on a synthetic paper."""

import pytest

from matrag.index import KnowledgeBase
from matrag.ingest import chunk_document, convert, make_chunker, make_converter
from matrag.retrieve import RetrievalMode, make_retriever


@pytest.fixture
def kb(settings, embed_model, tokenizer, sample_paper):
    doc = convert(sample_paper, make_converter(settings), settings.processed_dir)
    nodes = chunk_document(doc, "sample_paper", make_chunker(settings, tokenizer))
    kb = KnowledgeBase(settings, embed_model)
    kb.add_document("sample_paper", nodes)
    return kb


def test_conversion_is_cached(settings, sample_paper):
    convert(sample_paper, make_converter(settings), settings.processed_dir)
    assert (settings.processed_dir / "sample_paper.json").exists()


def test_chunks_carry_provenance(kb):
    nodes = kb.nodes()
    assert nodes
    assert [n.node_id for n in nodes] == [f"sample_paper::{i}" for i in range(len(nodes))]
    assert all(n.metadata["doc_id"] == "sample_paper" for n in nodes)
    table_chunks = [n for n in nodes if n.metadata["content_type"] == "table"]
    assert table_chunks and "0.0698" in table_chunks[0].get_content()
    # Section headings are prepended to the chunk text.
    assert "Results" in table_chunks[0].get_content()


def test_knowledge_base_persists_and_replaces(settings, embed_model, kb):
    count = len(kb.nodes())
    reloaded = KnowledgeBase(settings, embed_model)
    assert reloaded.doc_ids() == ["sample_paper"]
    assert len(reloaded.nodes()) == count
    assert reloaded.vector_store._collection.count() == count

    reloaded.add_document("sample_paper", kb.nodes())  # re-ingesting must not duplicate
    assert reloaded.vector_store._collection.count() == count

    reloaded.remove_document("sample_paper")
    assert reloaded.doc_ids() == []
    assert reloaded.vector_store._collection.count() == 0


@pytest.mark.parametrize("mode", list(RetrievalMode))
def test_retrieval_modes(kb, mode):
    query = "Fourier transform spectrometer pressure"
    hits = make_retriever(kb, mode, top_k=3).retrieve(query)
    assert 0 < len(hits) <= 3
    assert "spectrometer" in hits[0].node.get_content()


def test_doc_filter(kb):
    with pytest.raises(ValueError):
        make_retriever(kb, doc_ids=["unknown_paper"])
    hits = make_retriever(kb, top_k=2, doc_ids=["sample_paper"]).retrieve("broadening")
    assert all(h.node.metadata["doc_id"] == "sample_paper" for h in hits)


def test_chunk_boxes_are_normalized(settings, tokenizer):
    """Boxes are fractions of the page from the top-left, whatever the PDF's coordinate origin."""
    from docling_core.types.doc import BoundingBox, CoordOrigin, DocItemLabel, DoclingDocument, ProvenanceItem, Size

    from matrag.ingest import chunk_boxes

    doc = DoclingDocument(name="x")
    doc.add_page(page_no=1, size=Size(width=600, height=800))
    item = doc.add_text(label=DocItemLabel.TEXT, text="hello", prov=ProvenanceItem(
        page_no=1, charspan=(0, 5),
        bbox=BoundingBox(l=60, t=720, r=300, b=640, coord_origin=CoordOrigin.BOTTOMLEFT)))
    assert chunk_boxes(doc, [item]) == [[1, 0.1, 0.1, 0.5, 0.2]]
