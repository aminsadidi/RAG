"""Bibliographic metadata of the papers (title, authors, year, DOI).

Identifiers are found in the file name or on the first page of the paper,
then resolved with public services:

- arXiv: the abstract page's standard ``citation_*`` meta tags
- DOI:   the Crossref REST API (https://api.crossref.org)

Anything not found falls back to what Docling detected (the title) or to
the file name, so ingestion never fails because of a network problem. The
results are kept in ``data/<corpus>/papers.json``, where they can also be
corrected by hand.
"""

import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from docling_core.types.doc import DocItemLabel, DoclingDocument
from pydantic import BaseModel
from pylatexenc.latex2text import LatexNodes2Text

from matrag.textfix import clean_text

_USER_AGENT = "matrag/0.1 (student research project; https://github.com/aminsadidi/RAG)"
_TIMEOUT_S = 15

# New-style arXiv ids (2007+), e.g. 2111.01212 or 2111.01212v2.
_ARXIV_RE = re.compile(r"(?:arxiv[:_ .]?\s*)(\d{4}\.\d{4,5})(?:v\d+)?", re.IGNORECASE)
_DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>,;]+)", re.IGNORECASE)


class PaperInfo(BaseModel):
    doc_id: str
    title: str | None = None
    authors: list[str] = []  # family names, in order
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    source: str = "none"  # where the metadata came from

    def short_citation(self) -> str:
        """E.g. 'Tan et al. (2019)', 'Tan & Gordon (2019)'; the doc id if unknown."""
        if not self.authors:
            return self.doc_id
        if len(self.authors) == 1:
            names = self.authors[0]
        elif len(self.authors) == 2:
            names = f"{self.authors[0]} & {self.authors[1]}"
        else:
            names = f"{self.authors[0]} et al."
        return f"{names} ({self.year})" if self.year else names

    def reference(self) -> str:
        """One-line full reference for a bibliography."""
        parts = [", ".join(self.authors) if self.authors else None,
                 f"({self.year})" if self.year else None,
                 self.title, self.journal,
                 f"doi:{self.doi}" if self.doi else None,
                 f"arXiv:{self.arxiv_id}" if self.arxiv_id else None]
        return ". ".join(p for p in parts if p) or self.doc_id


def _raw_first_page(pdf_path: Path | None) -> str:
    """Text layer of page 1, including margins and stamps that Docling may drop."""
    if pdf_path is None or pdf_path.suffix.lower() != ".pdf":
        return ""
    try:
        import pypdfium2

        return pypdfium2.PdfDocument(str(pdf_path))[0].get_textpage().get_text_range()
    except Exception:
        return ""


def find_identifiers(
    doc: DoclingDocument, file_name: str, pdf_path: Path | None = None
) -> tuple[str | None, str | None]:
    """(doi, arxiv_id) from the file name or the first page.

    Only page 1 is searched: DOIs further on usually belong to cited works.
    """
    first_page = " ".join(
        item.text for item in doc.texts if item.prov and item.prov[0].page_no == 1
    ) + " " + _raw_first_page(pdf_path)
    arxiv = _ARXIV_RE.search(file_name) or _ARXIV_RE.search(first_page)
    doi = _DOI_RE.search(first_page)
    return (doi.group(1).rstrip(".)]") if doi else None, arxiv.group(1) if arxiv else None)


def _get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=_TIMEOUT_S) as response:
        return response.read().decode("utf-8", errors="replace")


def _strip_markup(text: str) -> str:
    """Plain text from Crossref JATS/HTML markup or arXiv LaTeX."""
    # Crossref pretty-prints markup: whitespace spanning a line break next to
    # a tag is layout, not content ("CO\n <sub>2</sub>\n , N" -> "CO2, N").
    text = re.sub(r"\s*\n\s*(?=<|[,.;:)])", "", text)
    # After a sub/superscript, a line break continues a formula ("N<sub>2</sub>\n O"
    # -> "N2O") before a capital letter not followed by lowercase; else it is a space.
    text = re.sub(r"(?<=>)\s*\n\s*(?=(.))",
                  lambda m: "" if re.match(r"[A-Z](?![a-z])", text[m.end():m.end() + 2]) else " ", text)
    text = re.sub(r"\s*<su([bp])>\s*(.*?)\s*</su\1>", r"\2", text)  # "CO <sub>2</sub>" -> "CO2"
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    if "$" in text or "\\" in text:
        text = LatexNodes2Text().latex_to_text(text)
    return " ".join(text.split())


def fetch_arxiv(arxiv_id: str) -> dict:
    page = _get(f"https://arxiv.org/abs/{arxiv_id}")
    meta = lambda name: re.findall(rf'<meta name="citation_{name}" content="([^"]*)"', page)  # noqa: E731
    title, date, doi = meta("title"), meta("date"), meta("doi")
    return {
        "title": _strip_markup(title[0]) if title else None,
        "authors": [_strip_markup(a.split(",")[0]) for a in meta("author")],
        "year": int(date[0][:4]) if date else None,
        "doi": doi[0] if doi else None,
        "source": "arxiv",
    }


def fetch_crossref(doi: str) -> dict:
    work = json.loads(_get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"))["message"]
    issued = (work.get("issued") or {}).get("date-parts") or [[None]]
    return {
        "title": _strip_markup(work["title"][0]) if work.get("title") else None,
        "authors": [a["family"] for a in work.get("author", []) if a.get("family")],
        "year": issued[0][0],
        "journal": _strip_markup(work["container-title"][0]) if work.get("container-title") else None,
        "doi": work.get("DOI", doi),
        "source": "crossref",
    }


def search_crossref(title: str, min_similarity: float = 0.9) -> dict | None:
    """Look a paper up by title; accept only a near-identical title."""
    from difflib import SequenceMatcher

    query = urllib.parse.urlencode({"query.bibliographic": title, "rows": 3})
    items = json.loads(_get(f"https://api.crossref.org/works?{query}"))["message"]["items"]
    key = lambda t: re.sub(r"[^a-z0-9]", "", t.lower())  # noqa: E731  ("CaF 2" == "CaF2")
    for item in items:
        if item.get("title") and SequenceMatcher(None, key(title), key(item["title"][0])).ratio() >= min_similarity:
            return fetch_crossref(item["DOI"])
    return None


def docling_title(doc: DoclingDocument) -> str | None:
    """The title item, else the first substantial heading on page 1."""
    first_heading = None
    for item in doc.texts:
        if item.label == DocItemLabel.TITLE:
            return clean_text(item.text)
        if (first_heading is None and item.label == DocItemLabel.SECTION_HEADER
                and item.prov and item.prov[0].page_no == 1 and len(item.text) >= 15):
            first_heading = clean_text(item.text)
    return first_heading


def resolve(doc: DoclingDocument, doc_id: str, file_name: str, online: bool = True,
            pdf_path: Path | None = None) -> PaperInfo:
    doi, arxiv_id = find_identifiers(doc, file_name, pdf_path)
    info = PaperInfo(doc_id=doc_id, doi=doi, arxiv_id=arxiv_id, title=docling_title(doc), source="docling")
    if not online:
        return info
    if not (doi or arxiv_id) and info.title:
        try:
            found = search_crossref(info.title)
        except Exception:
            found = None
        if found:
            return info.model_copy(update={k: v for k, v in found.items() if v} | {"source": "crossref-search"})
    # arXiv first (it also reports the journal DOI), then Crossref, whose
    # published-version metadata takes precedence.
    steps = [(fetch_arxiv, lambda: info.arxiv_id), (fetch_crossref, lambda: info.doi)]
    for fetch, key in steps:
        if not key():
            continue
        try:
            found = fetch(key())
        except Exception:  # network or parsing problem: keep what we have
            continue
        info = info.model_copy(update={k: v for k, v in found.items() if v})
    return info

class Library:
    """The per-corpus papers.json file."""

    def __init__(self, path: Path):
        self.path = path
        raw = json.loads(path.read_text("utf-8")) if path.exists() else {}
        self.papers = {doc_id: PaperInfo(**info) for doc_id, info in raw.items()}

    def get(self, doc_id: str) -> PaperInfo:
        return self.papers.get(doc_id) or PaperInfo(doc_id=doc_id)

    def put(self, info: PaperInfo) -> None:
        self.papers[info.doc_id] = info
        self._save()

    def remove(self, doc_id: str) -> None:
        if self.papers.pop(doc_id, None) is not None:
            self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {k: v.model_dump() for k, v in sorted(self.papers.items())}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
