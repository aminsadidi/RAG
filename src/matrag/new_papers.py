"""Papers downloaded by hand into a folder (proDownloads on Drive), matched to the papers asked for.

The requested papers (data/<corpus>/requested_papers.json: the candidates found for crystals and quantities
the site lacks, with their exact DOI, crystal, collection folder and bibliographic data) are matched by file
name: a PDF named after its DOI in any of the usual forms (``10.1063_1.1790952.pdf``, with '/', ':' and other
symbols written as '_') is that paper, if its first pages show that paper's title (``shows_title``). ``needs_ocr`` tells a scanned PDF (no usable text layer) from one with
text, so only those go through OCR.
"""

from __future__ import annotations

import json
import re
import unicodedata
from difflib import SequenceMatcher
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
        if shows_title(pdf, r["title"]) is False:  # a file saved under the wrong DOI
            unmatched.append(f"{pdf.name} (its first pages do not show the title of {r['doi']})")
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


def _letters(text: str) -> str:
    text = unicodedata.normalize("NFKC", re.sub(r"<[^>]+>", "", text)).lower()
    return "".join(c for c in text if c.isalnum())


def shows_title(pdf: Path, title: str, pages: int = 2, min_share: float = 0.9) -> bool | None:
    """Whether the first pages of ``pdf`` hold ``title`` (letters and digits only, so line breaks, hyphens and
    case do not matter): around the longest run of the title found in the text, the title's characters found
    there in order must be at least ``min_share`` of it (a subscript lost in the text layer, as BaTiO3 read as
    BaTiO, costs one character). None when it cannot tell (no text layer, or the file does not open)."""
    import pypdfium2 as pdfium

    try:
        doc = pdfium.PdfDocument(str(pdf))
    except Exception:  # noqa: BLE001 - not a readable PDF: leave the decision to the conversion
        return None
    try:
        text = "".join(doc[i].get_textpage().get_text_range() for i in range(min(len(doc), pages)))
    finally:
        doc.close()
    want, have = _letters(title), _letters(text)
    if len(have) < 300 or len(want) < 10:
        return None
    match = SequenceMatcher(None, want, have, autojunk=False).find_longest_match(0, len(want), 0, len(have))
    start = max(0, match.b - match.a - 20)
    window = have[start:start + len(want) + 40]
    found = sum(m.size for m in SequenceMatcher(None, want, window, autojunk=False).get_matching_blocks())
    return found >= min_share * len(want)
