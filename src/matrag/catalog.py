"""A paper collection kept in a folder (e.g. the RAG-Optics folder on Google Drive).

The folder is organised by category and material, with a master index of
every paper found by the harvester, including those without a PDF::

    RAG-Optics/
      01_Papers_by_Category/<category>/<material>/*.pdf
      02_Master_Index/rag_corpus.jsonl          (or papers_master_with_abstracts.jsonl,
                                                 or papers_master.csv)
      03_Processed/docling/                     (conversions, written by this program)

Each paper in the index becomes one item: its full text if a PDF is present,
otherwise its abstract (or only its title) so it can still be found by search,
labelled with ``source_type`` so answers can say what they are based on.
PDFs are matched to index entries by their stored path or by a DOI-based
file name (``10.1364/JOSAB.6.000616`` -> ``10.1364_josab.6.000616.pdf``).
"""

import csv
import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, field_validator

from matrag.metadata import PaperInfo

PAPERS_DIR = "01_Papers_by_Category"
INDEX_DIR = "02_Master_Index"
# Written by this program (conversions, logs); '_' keeps it out of the paper search.
PROCESSED_DIR = "_RAG_processed"
# Index files, most complete first.
INDEX_FILES = ("rag_corpus.jsonl", "papers_master_with_abstracts.jsonl", "papers_master.csv")
# Only PDFs count as papers (the folder also holds notes and Markdown cards).
PAPER_SUFFIXES = (".pdf",)
# Folders that never hold papers. Reference data (refractiveindex.info) must stay out of
# the searchable corpus: it is the answer key the extracted formulas are checked against.
_SKIP_DIRS = {INDEX_DIR, PROCESSED_DIR, "03_Paywalled_DOIs", "04_Dispersion_Formulas_Data", "03_Reference_Data"}
# Where organize() puts PDFs it cannot place in a category folder.
NOT_IN_INDEX_DIR, DUPLICATES_DIR = "99_Not_in_master_index", "98_Duplicate_copies"

FULL_TEXT, ABSTRACT, METADATA_ONLY = "full_text_pdf", "abstract", "metadata_only"


def doi_key(doi: str) -> str:
    """File-name and id form of a DOI: lower case, '/' and other symbols replaced by '_'."""
    return re.sub(r"[^a-z0-9.]+", "_", doi.strip().lower()).strip("_.")


class CatalogEntry(BaseModel):
    """One paper of the master index (field names follow the harvester's files)."""

    id: str = ""
    doi: str = ""
    arxiv_id: str = ""
    openalex_id: str = ""
    title: str = ""
    authors: list[str] = []  # full names
    year: int | None = None
    journal: str = ""
    category: str = ""
    material: str = ""
    abstract: str = ""
    tldr: str = ""
    keywords: list[str] = []
    pdf_path: str = ""  # relative to the collection folder
    status: str = ""
    oa_status: str = ""

    @field_validator("authors", "keywords", mode="before")
    @classmethod
    def _split(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [p.strip() for p in re.split(r";|\|", v) if p.strip()]
        return [a.get("name", "") if isinstance(a, dict) else str(a) for a in v]

    @field_validator("year", mode="before")
    @classmethod
    def _year(cls, v):
        try:
            return int(float(v)) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    @field_validator("doi", "arxiv_id", "openalex_id", "title", "journal", "category", "material",
                     "abstract", "tldr", "pdf_path", "status", "oa_status", "id", mode="before")
    @classmethod
    def _text(cls, v):
        return "" if v is None else str(v).strip()

    @property
    def key(self) -> str:
        """Stable id: the DOI (file-name form), else arXiv or OpenAlex id, else the index's own id."""
        if self.doi:
            return doi_key(self.doi.removeprefix("https://doi.org/"))
        if self.arxiv_id:
            return "arxiv_" + doi_key(self.arxiv_id)
        if self.openalex_id:
            return "openalex_" + self.openalex_id.rstrip("/").rsplit("/", 1)[-1]
        if self.id:
            return doi_key(self.id)
        return "title_" + hashlib.sha1(self.title.lower().encode()).hexdigest()[:12]

    def paper_info(self, doc_id: str) -> PaperInfo:
        return PaperInfo(
            doc_id=doc_id, title=clean_title(self.title) or None, authors=[_family_name(a) for a in self.authors],
            year=self.year, journal=self.journal or None, doi=self.doi or None,
            arxiv_id=self.arxiv_id or None, source="catalog",
        )

    def summary_text(self) -> str:
        """Searchable text for a paper without a PDF: title, authors, abstract, summary, keywords."""
        line = ", ".join(self.authors[:6]) + (" et al" if len(self.authors) > 6 else "")
        venue = ", ".join(p for p in (self.journal, str(self.year) if self.year else "") if p)
        parts = [clean_title(self.title), ". ".join(p for p in (line, venue) if p)]
        if self.abstract:
            parts.append(f"Abstract: {self.abstract}")
        if self.tldr:
            parts.append(f"Summary: {self.tldr}")
        if self.keywords:
            parts.append("Keywords: " + ", ".join(self.keywords))
        return "\n".join(p for p in parts if p)


_ALIASES = {"venue": "journal", "drive_path": "pdf_path", "arxiv": "arxiv_id"}


def clean_title(title: str) -> str:
    """Undo subscript markup of index titles: 'LiB_3O_5' -> 'LiB3O5', 'KBe_{2}BO_3F_2' -> 'KBe2BO3F2'."""
    return re.sub(r"(?<=[A-Za-z0-9)\]])_\{?(\d+)\}?", r"\1", title)


def _family_name(name: str) -> str:
    name = name.strip()
    if "," in name:  # "Chen, Chuangtian"
        return name.split(",", 1)[0].strip()
    return name.split()[-1] if name.split() else name


def _normalise(row: dict) -> dict:
    row = {k.lstrip("﻿").strip(): v for k, v in row.items()}
    for alias, name in _ALIASES.items():
        if alias in row and not row.get(name):
            row[name] = row[alias]
    return row


def index_file(root: Path) -> Path | None:
    for name in INDEX_FILES:
        path = root / INDEX_DIR / name
        if path.exists():
            return path
    return None


def load_catalog(root: Path) -> list[CatalogEntry]:
    """Entries of the collection's master index (empty if it has none); duplicates are dropped."""
    path = index_file(root)
    if path is None:
        return []
    if path.suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    else:
        rows = [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]
    entries, seen = [], set()
    for row in rows:
        entry = CatalogEntry(**_normalise(row))
        if entry.key not in seen and (entry.title or entry.doi):
            seen.add(entry.key)
            entries.append(entry)
    return entries


def find_pdfs(root: Path) -> list[Path]:
    """All PDFs under the collection folder, except in the index/processed folders and hidden or
    '_'-prefixed folders (caches, cards)."""
    found = []
    # os.walk with pruning: skipped folders (e.g. thousands of conversions) are never
    # listed, which matters on a Google Drive mount where every listing is a network call.
    for folder, dirs, files in os.walk(root):
        top = Path(folder) == root
        dirs[:] = [d for d in dirs if not d.startswith((".", "_")) and not (top and d in _SKIP_DIRS)]
        found += [Path(folder) / f for f in files if Path(f).suffix.lower() in PAPER_SUFFIXES]
    return sorted(found)


@dataclass
class Item:
    """One paper to index."""

    doc_id: str
    pdf: Path | None
    entry: CatalogEntry | None

    @property
    def source_type(self) -> str:
        if self.pdf is not None:
            return FULL_TEXT
        return ABSTRACT if self.entry and (self.entry.abstract or self.entry.tldr) else METADATA_ONLY


@dataclass
class Plan:
    items: list[Item]
    duplicates: list[Path]  # extra PDFs of a paper that already has one


def plan(root: Path) -> Plan:
    """Pair every PDF with its index entry; papers without a PDF are kept as abstract/metadata items."""
    entries = load_catalog(root)
    by_path = {e.pdf_path.replace("\\", "/").lower(): e for e in entries if e.pdf_path}
    by_key = {e.key: e for e in entries}
    matched: dict[str, Item] = {}
    unmatched: dict[str, Item] = {}
    duplicates = []
    # "name (1).pdf" is a second copy saved by Drive or a browser: originals come first.
    copy_suffix = re.compile(r"\s*\(\d+\)$")
    for pdf in sorted(find_pdfs(root), key=lambda p: (bool(copy_suffix.search(p.stem)), str(p))):
        rel = pdf.relative_to(root).as_posix().lower()
        stem = copy_suffix.sub("", pdf.stem)
        entry = by_path.get(rel) or by_key.get(doi_key(stem))
        if entry is not None:
            if entry.key in matched:
                duplicates.append(pdf)
            else:
                matched[entry.key] = Item(entry.key, pdf, entry)
            continue
        doc_id = re.sub(r"[^\w.-]+", "_", pdf.stem).strip("_")[:80] or "paper"
        base, n = doc_id, 2
        while doc_id in unmatched or doc_id in by_key:
            doc_id, n = f"{base}_{n}", n + 1
        unmatched[doc_id] = Item(doc_id, pdf, None)
    items = [matched.get(e.key) or Item(e.key, None, e) for e in entries]
    return Plan(items + list(unmatched.values()), duplicates)


def _category_dir(root: Path, entry: CatalogEntry) -> Path | None:
    if not (entry.category and entry.material):
        return None
    safe = lambda s: re.sub(r'[\\/:*?"<>|]+', "_", s).strip()  # noqa: E731
    return root / PAPERS_DIR / safe(entry.category) / safe(entry.material)


def _free_target(folder: Path, name: str) -> Path:
    target, n = folder / name, 2
    while target.exists():
        target = folder / f"{Path(name).stem}_{n}{Path(name).suffix}"
        n += 1
    return target


def organize(root: Path, move: bool = False, reference_dois: set[str] | None = None) -> list[dict]:
    """Sort the collection's PDFs into ``01_Papers_by_Category/<category>/<material>/``.

    PDFs found by their DOI file name (e.g. a folder of downloads) are moved to
    their paper's category folder; PDFs of papers missing from the master index
    go to ``99_Not_in_master_index`` and extra copies of a paper to
    ``98_Duplicate_copies``. Nothing is ever deleted, and files already in place
    stay. With ``move=False`` nothing changes: the rows only say what would
    happen. Every row is also written to ``02_Master_Index/pdf_inventory.csv``,
    with ``in_refractiveindex`` marking papers that refractiveindex.info cites
    as a data source (``reference_dois``), i.e. those with a known answer.
    """
    result = plan(root)
    reference_keys = {doi_key(d) for d in reference_dois or ()}
    rows = []

    def place(pdf: Path, folder: Path | None, entry: CatalogEntry | None, doc_id: str, kind: str):
        target = pdf
        if folder is not None and pdf.parent != folder:
            target = _free_target(folder, pdf.name)
            if move:
                folder.mkdir(parents=True, exist_ok=True)
                shutil.move(str(pdf), str(target))
        rows.append({
            "doc_id": doc_id, "doi": entry.doi if entry else "", "title": clean_title(entry.title) if entry else "",
            "year": entry.year if entry and entry.year else "", "category": entry.category if entry else "",
            "material": entry.material if entry else "", "kind": kind,
            "in_refractiveindex": doc_id in reference_keys,
            "file": target.relative_to(root).as_posix(),
            "moved_from": pdf.relative_to(root).as_posix() if target != pdf else "",
        })

    for item in result.items:
        if item.pdf is None:
            continue
        if item.entry is None:
            in_papers_dir = item.pdf.relative_to(root).parts[0] == PAPERS_DIR
            place(item.pdf, None if in_papers_dir else root / PAPERS_DIR / NOT_IN_INDEX_DIR, None,
                  item.doc_id, "not_in_index")
            continue
        # Files the harvester stored itself (found by their index path) are already in place.
        stored = item.entry.pdf_path and item.pdf.relative_to(root).as_posix().lower() == item.entry.pdf_path.lower()
        place(item.pdf, None if stored else _category_dir(root, item.entry), item.entry, item.doc_id, "indexed")
    for pdf in result.duplicates:
        place(pdf, root / PAPERS_DIR / DUPLICATES_DIR, None, doi_key(pdf.stem), "duplicate")

    report = root / INDEX_DIR / "pdf_inventory.csv"
    if move and rows:
        report.parent.mkdir(parents=True, exist_ok=True)
        with report.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return rows


def shard_of(doc_id: str, shards: int) -> int:
    """Stable assignment of a paper to one of ``shards`` parallel workers."""
    return int(hashlib.sha1(doc_id.encode()).hexdigest(), 16) % shards
