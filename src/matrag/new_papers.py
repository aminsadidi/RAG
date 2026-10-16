"""Papers downloaded by hand into a folder (proDownloads on Drive), matched to the papers asked for.

The requested papers (data/<corpus>/requested_papers.json: the candidates found for crystals and quantities
the site lacks, with their exact DOI, crystal, collection folder and bibliographic data) are matched by file
name: a PDF named after its DOI in any of the usual forms (``10.1063_1.1790952.pdf``, with '/', ':' and other
symbols written as '_') is that paper. ``needs_ocr`` tells a scanned PDF (no usable text layer) from one with
text, so only those go through OCR.
"""

from __future__ import annotations

import json
from pathlib import Path

from matrag.catalog import doi_key


def requested(path: Path) -> dict[str, dict]:
    """doi_key -> the requested paper's row."""
    return {doi_key(r["doi"]): r for r in json.loads(path.read_text(encoding="utf-8"))}


def auto_papers(downloads: Path, requested_path: Path, skip: set[str] = frozenset()) -> tuple[dict, list[str]]:
    """{file name: (doi, category, material, meta)} for the PDFs in ``downloads`` that are requested papers,
    in the form of the notebook's PAPERS table, and the names of the PDFs that match none (left as they are).
    ``skip``: file names already handled another way."""
    rows = requested(requested_path)
    papers, unmatched = {}, []
    for pdf in sorted(downloads.glob("*.pdf")):
        if pdf.name in skip:
            continue
        r = rows.get(doi_key(pdf.stem))
        if r is None:
            unmatched.append(pdf.name)
            continue
        meta = {"title": r["title"], "authors": r["authors"].replace(", ", "; "), "year": r["year"], "journal": r["journal"]}
        papers[pdf.name] = (r["doi"], r["category"], r["material"], meta)
    return papers, unmatched


def needs_ocr(pdf: Path, min_chars_per_page: int = 300, max_pages: int = 6) -> bool:
    """True for a scanned PDF: its first pages hold (almost) no extractable text, or mostly not letters."""
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(pdf))
    try:
        n = min(len(doc), max_pages)
        if n == 0:
            return False
        text = "".join(doc[i].get_textpage().get_text_range() for i in range(n))
    finally:
        doc.close()
    letters = sum(c.isalpha() for c in text)
    return len(text) / n < min_chars_per_page or letters < 0.5 * len(text)
