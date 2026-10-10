"""Long PDFs get a longer conversion timeout; a timed-out conversion is not cached; reconvert.txt redoes one."""
import os
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from matrag import ingest


class FakeOptions:
    document_timeout = 900.0


class FakeConverter:
    def __init__(self, errors=()):
        from docling.datamodel.base_models import InputFormat

        self.format_to_options = {InputFormat.PDF: SimpleNamespace(pipeline_options=FakeOptions())}
        self.matrag_timeout_per_page_s = 30.0
        self.errors = list(errors)

    def convert(self, path, page_range=None):
        return SimpleNamespace(errors=self.errors, document=SimpleNamespace(export_to_dict=lambda: {}))


def test_timeout_grows_with_the_page_count(monkeypatch, tmp_path):
    from docling.datamodel.base_models import InputFormat

    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF")
    conv = FakeConverter()
    monkeypatch.setattr(ingest, "page_count", lambda p: 400)
    ingest.extend_timeout(conv, pdf)
    assert conv.format_to_options[InputFormat.PDF].pipeline_options.document_timeout == 12000
    monkeypatch.setattr(ingest, "page_count", lambda p: 10)  # a short paper never lowers it
    ingest.extend_timeout(conv, pdf)
    assert conv.format_to_options[InputFormat.PDF].pipeline_options.document_timeout == 12000


def test_a_timed_out_conversion_is_not_cached(monkeypatch, tmp_path):
    from docling.datamodel.base_models import FailureCategory

    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF")
    monkeypatch.setattr(ingest, "page_count", lambda p: 1)
    conv = FakeConverter(errors=[SimpleNamespace(category=FailureCategory.TIMEOUT)])
    with pytest.raises(RuntimeError, match="timed out"):
        ingest.convert(pdf, conv, tmp_path / "cache", "book")
    assert not ingest.is_cached(tmp_path / "cache", "book")


def test_reconvert_deletes_an_older_conversion_once(tmp_path):
    from matrag.pipeline import Workspace

    ws = Workspace.__new__(Workspace)
    processed = tmp_path / "docling"
    processed.mkdir()
    ws.settings = SimpleNamespace(data_dir=tmp_path / "data", corpus="c", processed_dir=processed)
    (tmp_path / "data" / "c").mkdir(parents=True)
    import datetime as dt

    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=5)
    (tmp_path / "data" / "c" / "reconvert.txt").write_text(f"# comment\nbook1 {since:%Y-%m-%dT%H:%M}\n", "utf-8")
    ws.conversion_of = lambda doc_id: ""
    cached = processed / "book1.json.gz"
    cached.write_bytes(b"x")
    old = time.time() - 3600  # converted an hour ago: before the date
    os.utime(cached, (old, old))
    item = SimpleNamespace(doc_id="book1", pdf=Path("book1.pdf"))
    assert ws._stale_conversion(item) and not cached.exists()
    cached.write_bytes(b"new")  # the new conversion is newer than the date: kept
    assert not ws._stale_conversion(item) and cached.exists()
    assert not ws._stale_conversion(SimpleNamespace(doc_id="other", pdf=Path("o.pdf")))
