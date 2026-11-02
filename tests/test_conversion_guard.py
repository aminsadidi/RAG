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


def test_a_book_resumes_from_the_last_finished_part(monkeypatch, tmp_path):
    from docling_core.types.doc import DoclingDocument, Size

    def part(path, converter, page_range):
        calls.append(page_range)
        if page_range == (5, 6) and not resumed:
            raise KeyboardInterrupt  # a Colab disconnect
        doc = DoclingDocument(name="book")
        for n in range(page_range[0], page_range[1] + 1):
            doc.add_page(page_no=n, size=Size(width=1, height=1))
            doc.add_text(label="text", text=f"page {n}")
        return doc

    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF")
    monkeypatch.setattr(ingest, "page_count", lambda p: 7)
    monkeypatch.setattr(ingest, "PART_PAGES", 2)
    monkeypatch.setattr(ingest, "_convert_pages", part)
    calls, resumed = [], False
    with pytest.raises(KeyboardInterrupt):
        ingest.convert(pdf, FakeConverter(), tmp_path / "cache", "book")
    assert not ingest.is_cached(tmp_path / "cache", "book")
    calls, resumed = [], True
    doc = ingest.convert(pdf, FakeConverter(), tmp_path / "cache", "book")
    assert calls == [(5, 6), (7, 7)]  # pages 1-4 were not converted again
    assert sorted(doc.pages) == list(range(1, 8))
    assert [t.text for t in doc.texts] == [f"page {n}" for n in range(1, 8)]
    assert ingest.is_cached(tmp_path / "cache", "book") and not (tmp_path / "cache" / "parts" / "book").exists()


def test_sessions_split_a_book_and_the_join_converts_nothing_again(monkeypatch, tmp_path):
    from docling_core.types.doc import DoclingDocument, Size

    def part(path, converter, page_range):
        calls.append(page_range)
        doc = DoclingDocument(name="book")
        for n in range(page_range[0], page_range[1] + 1):
            doc.add_page(page_no=n, size=Size(width=1, height=1))
            doc.add_text(label="text", text=f"page {n}")
        return doc

    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF")
    monkeypatch.setattr(ingest, "page_count", lambda p: 7)
    monkeypatch.setattr(ingest, "PART_PAGES", 2)
    monkeypatch.setattr(ingest, "_convert_pages", part)
    calls = []
    assert ingest.convert_parts(pdf, FakeConverter(), tmp_path / "cache", "book", 0, 2) == (2, 2)
    assert calls == [(1, 2), (5, 6)]
    calls = []
    assert ingest.convert_parts(pdf, FakeConverter(), tmp_path / "cache", "book", 1, 2) == (2, 2)
    assert calls == [(3, 4), (7, 7)]
    assert ingest.convert_parts(pdf, FakeConverter(), tmp_path / "cache", "book", 1, 2) == (2, 0)  # a rerun
    calls = []
    doc = ingest.convert(pdf, FakeConverter(), tmp_path / "cache", "book")
    assert calls == [] and sorted(doc.pages) == list(range(1, 8))


def test_a_book_converted_in_parts_is_joined_whole_despite_max_pages(monkeypatch, tmp_path):
    from docling_core.types.doc import DoclingDocument, Size

    def part(path, converter, page_range):
        doc = DoclingDocument(name="book")
        for n in range(page_range[0], min(page_range[1], 7) + 1):
            doc.add_page(page_no=n, size=Size(width=1, height=1))
            doc.add_text(label="text", text=f"page {n}")
        return doc

    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF")
    monkeypatch.setattr(ingest, "page_count", lambda p: 7)
    monkeypatch.setattr(ingest, "PART_PAGES", 2)
    monkeypatch.setattr(ingest, "_convert_pages", part)
    cache = tmp_path / "cache"
    short = ingest.convert(pdf, FakeConverter(), cache, "book", max_pages=4)  # an older run: the first pages only
    assert sorted(short.pages) == [1, 2, 3, 4]
    ingest.convert_parts(pdf, FakeConverter(), cache, "book")
    doc = ingest.convert(pdf, FakeConverter(), cache, "book", max_pages=4)
    assert sorted(doc.pages) == list(range(1, 8))
    assert not (cache / "parts" / "book").exists()  # removed once every page is joined
    assert sorted(ingest.convert(pdf, FakeConverter(), cache, "book", max_pages=4).pages) == list(range(1, 8))


def test_a_thesis_cut_at_max_pages_is_not_taken_for_a_book(monkeypatch, tmp_path):
    """The parts a max_pages run leaves behind used to make the next run drop the cache and convert every page."""
    from docling_core.types.doc import DoclingDocument, Size

    def part(path, converter, page_range):
        calls.append(page_range)
        doc = DoclingDocument(name="thesis")
        for n in range(page_range[0], page_range[1] + 1):
            doc.add_page(page_no=n, size=Size(width=1, height=1))
            doc.add_text(label="text", text=f"page {n}")
        return doc

    pdf = tmp_path / "thesis.pdf"
    pdf.write_bytes(b"%PDF")
    monkeypatch.setattr(ingest, "page_count", lambda p: 40)  # a 40-page thesis, cut at 6 pages
    monkeypatch.setattr(ingest, "PART_PAGES", 2)
    monkeypatch.setattr(ingest, "_convert_pages", part)
    cache = tmp_path / "cache"
    calls = []
    first = ingest.convert(pdf, FakeConverter(), cache, "thesis", max_pages=6)
    assert sorted(first.pages) == list(range(1, 7)) and calls == [(1, 2), (3, 4), (5, 6)]
    assert (cache / "parts" / "thesis").is_dir()  # left behind: not every page is in
    assert not ingest.is_book(cache / "parts" / "thesis", 6)
    calls = []
    again = ingest.convert(pdf, FakeConverter(), cache, "thesis", max_pages=6)
    assert calls == [] and sorted(again.pages) == list(range(1, 7))  # the cached conversion, nothing converted


def test_book_marker_and_old_unmarked_books(tmp_path):
    parts = tmp_path / "parts" / "b"
    parts.mkdir(parents=True)
    (parts / "00001-00010.json.gz").write_bytes(b"x")
    assert not ingest.is_book(parts, 60)
    (parts / "00071-00080.json.gz").write_bytes(b"x")  # a part past max_pages: an old convert-book run
    assert ingest.is_book(parts, 60)
    marked = tmp_path / "parts" / "m"
    marked.mkdir()
    (marked / ingest.BOOK_MARKER).touch()
    assert ingest.is_book(marked, 60) and ingest.is_book(marked, None)
    assert not ingest.is_book(tmp_path / "parts" / "none", 60)
