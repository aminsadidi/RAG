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
