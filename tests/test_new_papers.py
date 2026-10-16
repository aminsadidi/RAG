import json

from matrag.new_papers import auto_papers, needs_ocr


def test_auto_papers_matches_doi_named_files(tmp_path):
    req = tmp_path / "req.json"
    req.write_text(json.dumps([
        {"doi": "10.1002/(sici)1097-4555(199807)29:7<645::aid-jrs273>3.0.co;2-s", "crystal": "Gd2(MoO4)3", "need": "new",
         "category": "03_X", "material": "SBN", "title": "T", "authors": "A, B", "year": 1998, "journal": "J"},
        {"doi": "10.1063/1.1790952", "crystal": "POM", "need": "new", "category": "06_O", "material": "DAST",
         "title": "U", "authors": "C", "year": 2004, "journal": "K"}]))
    d = tmp_path / "dl"
    d.mkdir()
    for name in ("10.1002_(sici)1097-4555(199807)29_7_645__aid-jrs273_3.0.co;2-s.pdf", "10.1063_1.1790952.pdf", "other.pdf"):
        (d / name).write_bytes(b"%PDF")
    papers, unmatched = auto_papers(d, req, skip={"10.1063_1.1790952.pdf"})
    assert unmatched == ["other.pdf"]
    doi, cat, mat, meta = papers["10.1002_(sici)1097-4555(199807)29_7_645__aid-jrs273_3.0.co;2-s.pdf"]
    assert doi.startswith("10.1002/(sici)") and (cat, mat) == ("03_X", "SBN") and meta["authors"] == "A; B"


def test_requested_papers_have_existing_folders():
    from pathlib import Path
    rows = json.loads(Path("data/rag-optics/requested_papers.json").read_text(encoding="utf-8"))
    papers = json.loads(Path("web/src/papers.json").read_text(encoding="utf-8"))
    folders = {(p.get("category"), p.get("material")) for p in papers}
    assert all((r["category"], r["material"]) in folders for r in rows)


def test_needs_ocr(tmp_path):
    import pypdfium2 as pdfium
    blank = tmp_path / "blank.pdf"
    doc = pdfium.PdfDocument.new()
    doc.new_page(595, 842)
    doc.save(str(blank))
    assert needs_ocr(blank)
