"""Metadata helpers (offline: no arXiv/Crossref requests)."""

from matrag.metadata import Library, PaperInfo, _strip_markup, find_identifiers, resolve


def test_short_citation_forms():
    assert PaperInfo(doc_id="x").short_citation() == "x"
    assert PaperInfo(doc_id="x", authors=["Tan"], year=2019).short_citation() == "Tan (2019)"
    assert PaperInfo(doc_id="x", authors=["Tan", "Gordon"], year=2019).short_citation() == "Tan & Gordon (2019)"
    assert PaperInfo(doc_id="x", authors=["Tan", "Kochanov", "Gordon"]).short_citation() == "Tan et al."


def test_strip_crossref_and_latex_markup():
    assert _strip_markup("Part I—CO\n    <sub>2</sub>\n    , N\n <sub>2</sub>\n O") == "Part I—CO2, N2O"
    assert _strip_markup("Astronomy &amp; Astrophysics") == "Astronomy & Astrophysics"
    assert _strip_markup(r"$\beta$-BBO in the 0.188-6.22 $\mu$m range") == "β-BBO in the 0.188-6.22 μm range"


def test_identifiers_from_file_name_and_first_page(settings, sample_paper):
    from matrag.ingest import convert, make_converter

    doc = convert(sample_paper, make_converter(settings), settings.processed_dir)
    assert find_identifiers(doc, "arxiv_2111.01212.pdf") == (None, "2111.01212")
    assert find_identifiers(doc, "paper.pdf") == (None, None)
    info = resolve(doc, "sample_paper", "sample_paper.md", online=False)
    assert info.title.startswith("Air-broadening of CO2 lines")


def test_library_round_trip(tmp_path):
    lib = Library(tmp_path / "papers.json")
    lib.put(PaperInfo(doc_id="p", authors=["Tan"], year=2019))
    assert Library(tmp_path / "papers.json").get("p").short_citation() == "Tan (2019)"
    assert Library(tmp_path / "papers.json").get("missing").doc_id == "missing"
