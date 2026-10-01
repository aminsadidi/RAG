"""The Workspace facade on a synthetic paper (offline)."""

from matrag import pipeline
from matrag.pipeline import Workspace, _safe_name, list_corpora


def test_safe_name():
    assert _safe_name("Leviton CaF2 (2008).PDF") == "Leviton_CaF2_2008.pdf"


def test_ingest_list_pack_and_remove(settings, embed_model, tokenizer, sample_paper, monkeypatch):
    import matrag.ingest

    monkeypatch.setattr(pipeline, "_embed_model", lambda *a: embed_model)
    real_chunker = matrag.ingest.make_chunker
    monkeypatch.setattr(matrag.ingest, "make_chunker", lambda s, t=None: real_chunker(s, tokenizer))
    backup = settings.storage_dir.parent / "backup"
    ws = Workspace(settings.model_copy(update={"fetch_metadata": False, "storage_backup_dir": backup}), corpus="test")

    [path] = ws.add_files([sample_paper])
    [result] = ws.ingest([path])
    assert result.chunks > 0 and not result.error
    assert ws.ingest([path])[0].skipped  # second run: already indexed
    assert (backup / "test" / "docstore.json").exists()
    assert list_corpora(ws.settings) == ["test"]

    [(paper, chunks)] = ws.papers()
    assert paper.title.startswith("Air-broadening of CO2") and chunks == result.chunks

    text = ws.pack("air-broadened half-width of R(10)", language="Persian", top_k=2)
    assert "Write the answer in Persian" in text and "Question: air-broadened" in text

    ws.remove_paper("sample_paper")
    assert ws.papers() == [] and not path.exists()


def test_add_files_never_overwrites_a_different_paper(settings, tmp_path):
    ws = Workspace(settings, corpus="dup")
    a, b = tmp_path / "a" / "paper.pdf", tmp_path / "b" / "paper.pdf"
    for f, text in ((a, "first"), (b, "second")):
        f.parent.mkdir()
        f.write_text(text)
    [first] = ws.add_files([a])
    [same] = ws.add_files([a])  # same content again: same file
    [second] = ws.add_files([b])  # different content, same name
    assert first == same and first.name == "paper.pdf" and second.name == "paper_2.pdf"
    assert first.read_text() == "first" and second.read_text() == "second"


def test_listed_papers_are_reconverted(settings, embed_model, tokenizer, sample_paper, monkeypatch):
    """A paper added to ocr_papers.txt is converted again (with OCR) on the next ingest, once."""
    import matrag.ingest

    monkeypatch.setattr(pipeline, "_embed_model", lambda *a: embed_model)
    real_chunker = matrag.ingest.make_chunker
    monkeypatch.setattr(matrag.ingest, "make_chunker", lambda s, t=None: real_chunker(s, tokenizer))
    ws = Workspace(settings.model_copy(update={"fetch_metadata": False}), corpus="ocr")
    [path] = ws.add_files([sample_paper])
    ws.ingest([path])
    (ws.settings.data_dir / "ocr" / "ocr_papers.txt").write_text("# scanned\nsample_paper\n", encoding="utf-8")
    ws.__dict__.pop("_paper_lists", None)
    assert ws.conversion_of("sample_paper") == "ocr" and ws.conversion_of("other") == ""
    [again] = ws.ingest([path])
    assert not again.skipped and again.chunks > 0
    assert ws.kb.doc_conversions() == {"sample_paper": "ocr"}
    assert (ws.settings.processed_dir.parent / "docling_ocr" / "sample_paper.json.gz").exists()
    assert ws.ingest([path])[0].skipped
