"""The refractiveindex.info database as ground truth for optical constants.

Every entry (a YAML file) holds the source paper and the data taken from
it: a tabulated n(λ), k(λ) or the coefficients of a dispersion formula.
Database: https://github.com/polyanskiy/refractiveindex.info-database (CC0).
"""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

_DOI_RE = re.compile(r"doi\.org/(10\.\d{4,9}/[^\"'<>\s]+)", re.IGNORECASE)
_ARXIV_RE = re.compile(r"arxiv\.org/abs/(\d{4}\.\d{4,5})|arXiv[:.](\d{4}\.\d{4,5})", re.IGNORECASE)


@dataclass
class Entry:
    path: str          # relative to database/data, e.g. main/CaF2/nk/Daimon-20.yml
    shelf: str
    material: str      # "book", e.g. CaF2
    page: str          # e.g. Daimon-20
    reference: str     # citation text without HTML
    doi: str | None
    arxiv_id: str | None
    data_types: str    # e.g. "formula 2" or "tabulated nk"
    wavelength_um: str  # range covered, e.g. "0.138-2.326"
    comments: str


def _plain(html_text: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", "", html_text or "").split())


def read_entry(path: Path, data_root: Path) -> Entry:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    refs = doc.get("REFERENCES", "") or ""
    doi = _DOI_RE.search(refs)
    arxiv = _ARXIV_RE.search(refs)
    data = doc.get("DATA", []) or []
    ranges = []
    for block in data:
        if "wavelength_range" in block:
            ranges.append(block["wavelength_range"].replace(" ", "-"))
        elif "data" in block:
            rows = [r.split() for r in str(block["data"]).strip().splitlines() if r.strip()]
            if rows:
                ranges.append(f"{rows[0][0]}-{rows[-1][0]}")
    rel = path.relative_to(data_root)
    shelf, material, *_ = rel.parts
    return Entry(
        path=str(rel), shelf=shelf, material=material, page=path.stem,
        reference=_plain(refs), doi=doi.group(1).rstrip(".") if doi else None,
        arxiv_id=(arxiv.group(1) or arxiv.group(2)) if arxiv else None,
        data_types="; ".join(b.get("type", "") for b in data),
        wavelength_um="; ".join(ranges), comments=_plain(doc.get("COMMENTS", "") or ""),
    )


def iter_entries(database_dir: Path, shelves: tuple[str, ...] = ("main",)):
    data_root = database_dir / "data"
    for shelf in shelves:
        for path in sorted((data_root / shelf).rglob("*.yml")):
            try:
                yield read_entry(path, data_root)
            except Exception:  # a malformed file must not stop the scan
                continue


def open_access_candidates(database_dir: Path, workers: int = 6) -> list[dict]:
    """Source papers of the database with Crossref metadata and an open-access flag.

    A paper counts as open access when Crossref lists a Creative Commons license.
    """
    from concurrent.futures import ThreadPoolExecutor

    from matrag.metadata import fetch_crossref, _get
    import json

    entries = [e for e in iter_entries(database_dir) if e.doi]
    by_doi: dict[str, list[Entry]] = {}
    for e in entries:
        by_doi.setdefault(e.doi.lower(), []).append(e)

    def lookup(doi: str) -> dict:
        try:
            work = json.loads(_get(f"https://api.crossref.org/works/{doi}"))["message"]
            info = fetch_crossref(doi)
        except Exception:
            return {"doi": doi, "open_access": None}
        licenses = [l.get("URL", "") for l in work.get("license", [])]
        return {"doi": doi, "open_access": any("creativecommons.org" in u for u in licenses),
                "license": next((u for u in licenses if "creativecommons" in u), ""),
                "title": info.get("title"), "authors": ", ".join(info.get("authors", [])[:3]),
                "year": info.get("year"), "journal": info.get("journal"),
                "citations": work.get("is-referenced-by-count")}

    with ThreadPoolExecutor(workers) as pool:
        papers = list(pool.map(lookup, sorted(by_doi)))
    rows = []
    for paper in papers:
        group = by_doi[paper["doi"]]
        rows.append(paper | {
            "materials": "; ".join(sorted({e.material for e in group})),
            "entries": "; ".join(e.path for e in group),
            "data_types": "; ".join(sorted({e.data_types for e in group})),
            "wavelength_um": group[0].wavelength_um,
            "arxiv_id": next((e.arxiv_id for e in group if e.arxiv_id), ""),
        })
    return rows
