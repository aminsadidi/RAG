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


def _text_pdf(path, lines):
    """A one-page PDF whose text layer holds ``lines`` (Helvetica, one per line)."""
    body = "BT /F1 10 Tf 40 800 Td 12 TL " + " ".join(f"({t}) Tj T*" for t in lines) + " ET"
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            f"<< /Length {len(body)} >>\nstream\n{body}\nendstream"]
    out, offsets = "%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    path.write_bytes(out.encode("latin-1"))


def test_shows_title_tells_a_file_saved_under_the_wrong_doi(tmp_path):
    from matrag.new_papers import shows_title
    filler = ["The index of refraction of the crystal was measured with a prism at several wavelengths"] * 6
    sapphire = tmp_path / "s.pdf"
    _text_pdf(sapphire, ["Temperature dependence of the infrared", "refractive index of sapphire", *filler])
    bto = tmp_path / "b.pdf"  # the subscript 3 lost from the text layer, the title split over two lines
    _text_pdf(bto, ["Refractive Indices of Single Domain BaTiO, for Different", "Wavelengths and Temperatures", *filler])
    assert shows_title(sapphire, "Temperature dependence of the infrared refractive index of sapphire")
    assert shows_title(bto, "Refractive indices of single domain BaTiO<sub>3</sub> for different wavelengths and temperatures")
    # a paper of the same group with a close title, and another crystal's paper, are not this one
    assert shows_title(sapphire, "Frequency and temperature dependence of the refractive index of sapphire") is False
    assert shows_title(sapphire, "Refractive index dispersion and its temperature dependence in GaS") is False
    blank = tmp_path / "blank.pdf"
    _text_pdf(blank, [])
    assert shows_title(blank, "Anything at all here") is None
    assert shows_title(tmp_path / "missing.pdf", "Anything at all here") is None


def test_auto_papers_leaves_out_a_file_with_another_papers_title(tmp_path):
    req = tmp_path / "req.json"
    req.write_text(json.dumps([{"doi": "10.1016/0375-9601(83)90952-0", "crystal": "GaS", "need": "dndt", "category": "04_X",
                                "material": "GaSe", "title": "Refractive index dispersion and its temperature dependence in GaS",
                                "authors": "A", "year": 1983, "journal": "Phys. Lett. A"}]))
    d = tmp_path / "dl"
    d.mkdir()
    _text_pdf(d / "10.1016-0375-9601(83)90952-0.pdf", ["Temperature dependence of the infrared", "refractive index of sapphire",
                                                       *["Infrared domes on guided missiles are aerodynamically heated"] * 8])
    papers, unmatched = auto_papers(d, req)
    assert papers == {} and unmatched[0].startswith("10.1016-0375-9601(83)90952-0.pdf (its first pages")
