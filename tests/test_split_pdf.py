import json

import pypdfium2 as pdfium

from matrag import qdrant_store


def test_a_long_pdf_goes_in_parts_of_whole_pages(tmp_path, monkeypatch):
    src = tmp_path / "book.pdf"
    doc = pdfium.PdfDocument.new()
    for _ in range(7):
        doc.new_page(595, 842)
    doc.save(str(src))
    monkeypatch.setattr(qdrant_store, "MAX_ASSET_BYTES", 10 ** 6)
    dst = tmp_path / "out" / "book.pdf"
    m = qdrant_store.split_pdf(str(src), str(dst), pages_per_part=3)
    assert m["pages"] == 7 and [p[:2] for p in m["parts"]] == [[1, 3], [4, 6], [7, 7]]
    assert len(pdfium.PdfDocument(str(dst.parent / m["parts"][1][2]))) == 3
    assert json.loads((tmp_path / "out" / "book.pdf.parts.json").read_text()) == m
    # the same source again: the parts are kept
    assert qdrant_store.split_pdf(str(src), str(dst), pages_per_part=3) == m
