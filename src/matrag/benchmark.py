"""Automatic evaluation sets built from refractiveindex.info (no hand labelling).

refractiveindex.info cites, for each of its dispersion formulas, the paper the
formula comes from. For every such paper whose full text is in the corpus, the
correct answer is therefore known:

- **Formula benchmark**: extract the dispersion formula from the paper and
  compare n(λ) with the database entry over their common wavelength range
  (max |Δn|). This measures the system's main task end to end.
- **Retrieval questions**: "the dispersion formula of <material>" must retrieve
  a chunk from one of the papers the database cites for that material.

Only entries given as a formula count; entries with tabulated n only come from
papers that report measured values, not a formula.
"""

from collections import defaultdict
from pathlib import Path
from statistics import median

from matrag.catalog import doi_key
from matrag.evaluate import GoldQuestion
from matrag.references.refractiveindex import EntryData, iter_entries, load_entry

TOLERANCES = (1e-4, 1e-3, 1e-2)


def formula_references(database_dir: Path, doc_ids: set[str]) -> dict[str, list[EntryData]]:
    """Formula entries of refractiveindex.info, grouped by the corpus paper they cite.

    Papers are matched by DOI (corpus doc ids are DOIs in file-name form) or by
    arXiv id (doc ids like ``arxiv_2111.01212``).
    """
    data_root = database_dir / "data"
    found: dict[str, list[EntryData]] = defaultdict(list)
    for entry in iter_entries(database_dir):
        if "formula" not in entry.data_types:
            continue
        keys = []
        if entry.doi:
            keys.append(doi_key(entry.doi))
        if entry.arxiv_id:
            keys += [f"arxiv_{entry.arxiv_id}", "arxiv_" + doi_key(entry.arxiv_id)]
        for key in keys:
            if key in doc_ids:
                try:
                    found[key].append(load_entry(data_root / entry.path, data_root))
                except Exception:  # a malformed entry must not stop the scan
                    pass
                break
    return dict(found)


def retrieval_questions(references: dict[str, list[EntryData]]) -> list[GoldQuestion]:
    """One question per material: any chunk of a paper the database cites for it is relevant."""
    by_material: dict[str, set[str]] = defaultdict(set)
    for doc_id, entries in references.items():
        for e in entries:
            by_material[e.entry.material].add(doc_id)
    return [
        GoldQuestion(id=f"rii-{material}", doc_id=";".join(sorted(docs)), pages=[], expected=[],
                     question=f"What is the dispersion formula (Sellmeier coefficients) for the refractive index of "
                              f"{material}?")
        for material, docs in sorted(by_material.items())
    ]


def paper_row(doc_id: str, citation: str, entries: list[EntryData], records) -> dict:
    """Benchmark result of one paper: how close the best extracted formula comes to the database."""
    diffs = [r.reference_max_dn for r in records if r.reference_max_dn is not None]
    best = min(diffs) if diffs else None
    return {
        "doc_id": doc_id,
        "citation": citation,
        "materials": ";".join(sorted({e.entry.material for e in entries})),
        "reference_entries": ";".join(e.entry.path for e in entries),
        "formulas_extracted": len(records),
        "formulas_compared": len(diffs),
        "best_max_dn": best,
        **{f"within_{tol:g}": best is not None and best <= tol for tol in TOLERANCES},
    }


def summarize(rows: list[dict]) -> dict:
    """Shares of papers with a formula extracted and matching the database within each tolerance."""
    n = len(rows)
    if not n:
        return {"papers": 0}
    share = lambda k: round(sum(bool(r[k]) for r in rows) / n, 3)  # noqa: E731
    best = [r["best_max_dn"] for r in rows if r["best_max_dn"] is not None]
    return {
        "papers": n,
        "formula extracted": round(sum(r["formulas_extracted"] > 0 for r in rows) / n, 3),
        **{f"|Δn| ≤ {tol:g}": share(f"within_{tol:g}") for tol in TOLERANCES},
        "median best |Δn|": round(median(best), 6) if best else "",
    }
