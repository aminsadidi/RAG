"""Extraction of dispersion formulas (n as a function of λ) from papers.

Instead of reading refractive indices off plots, the fitted formula a paper
reports (e.g. Sellmeier coefficients in a table, or an equation in the text)
is extracted and evaluated, which yields n(λ) at any wavelength.

Candidates, per paper:
- every table whose caption or content mentions a dispersion formula, given
  whole in compact form (``tables.compact_table``), and
- runs of consecutive text chunks that contain an explicit formula.
A few chunks that define the formula ("a Sellmeier model of the form ...")
are added as context, since tables often list coefficients only.

Each extracted formula is checked three ways: are its numbers in the source
text, is it physically sensible (``dispersion.check_formula``), and how far
is it from refractiveindex.info when the database has the same paper.
"""

import json
import re
from pathlib import Path

import numpy as np
from docling_core.types.doc import DoclingDocument
from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM
from llama_index.core.schema import BaseNode
from pydantic import BaseModel, Field

from matrag.dispersion import DispersionFormula, check_formula
from matrag.llm import Throttle
from matrag.tables import compact_table
from matrag.textfix import clean_text

FORMULA_PROMPT = PromptTemplate("""\
You extract dispersion formulas (refractive index versus wavelength) from scientific papers.

Represent every formula in this general form:
  n² = A + Σ_i B_i·λ^p_i / (λ² − C_i) + Σ_j E_j·λ^q_j      (squared = true)
or, for Cauchy-type formulas that give n directly:
  n  = A + Σ_j E_j·λ^q_j                                  (squared = false)

How to map common forms:
- "n² − 1 = Σ B_i λ²/(λ² − C_i)": constant A = 1 (the 1 moves to the right side), numerator_power = 2.
- "n² = A + B/(λ² − C) − D·λ²": one pole term with numerator_power = 0, and a power term E = −D, power = 2.
- A denominator λ² − λ_i² with a resonance wavelength λ_i: put λ_i in 'pole' and set pole_is_wavelength = true.
- Code such as sqrt(1 + x.^2*B./(x.^2 - C)) is the same Sellmeier form (A = 1).
- Temperature-dependent coefficients given as polynomials (rows like "constant term, T term, T² term"):
  put the values for T^0, T^1, T^2, ... in coefficient_T / pole_T, and the T^0 value also in coefficient / pole.
- Different axes or polarizations (o, e, x, y, z) and different materials are separate formulas.

Rules:
- Only use numbers written in the text. Never fill in coefficients from memory.
- Keep the wavelength unit of the formula (um or nm); give the stated validity range in µm.
- equation_text: copy the formula and its coefficients verbatim.
- If the text has no dispersion formula with numerical coefficients, return an empty list.

Context from the same paper (how the formula is defined):
{context}

Text to extract from ({source}):
\"\"\"
{text}
\"\"\"
""")

# Coefficient tables of a fitted formula (not tables of dn/dλ or dn/dT values).
_TABLE_HINT = re.compile(r"sellmeier|cauchy|dispersion (formula|equation|relation)|coefficients? (for|of) the|fit", re.I)
_TABLE_EXCLUDE = re.compile(r"dn\s*/\s*d[λT]|thermo-optic|spectral dispersion", re.I)
# A formula written out with its numbers (equation or code), not just mentioned.
_FORMULA_TEXT = re.compile(
    r"refracind|sqrt\s*\(|\.\^\s*2|n\s*\^?\s*2\s*(\(λ\))?\s*[-−]?\s*1?\s*=|n²\s*[-−=]|λ\s*\^?\s*2\s*[-−]\s*\d",
    re.I)
_DEFINITION = re.compile(r"sellmeier (model|equation|formula|relation)|of the form|dispersion (formula|equation)", re.I)
_NUMBER = re.compile(r"[-−]?\d+(?:\.\d+)?(?:\s*[eE]\s*[-+−]?\s*\d+)?")


class FormulaResult(BaseModel):
    formulas: list[DispersionFormula] = Field(default_factory=list)


class FormulaRecord(BaseModel):
    formula: DispersionFormula
    doc_id: str
    pages: str
    source: str  # e.g. "table 5" or "text arxiv_2111.01212::80-81"
    boxes: str = "[]"  # page boxes of the source, for the PDF viewer
    llm: str = ""
    numbers_in_source: float = 0.0  # share of the formula's coefficients found in the source text
    problems: list[str] = Field(default_factory=list)  # physical sanity problems
    reference_entry: str = ""  # matching refractiveindex.info entry, if any
    reference_max_dn: float | None = None  # max |n_extracted − n_reference| over the common range


# --- candidates ---------------------------------------------------------------


class Candidate(BaseModel):
    doc_id: str
    source: str
    pages: str
    text: str
    boxes: str = "[]"


def table_candidates(doc: DoclingDocument, doc_id: str) -> list[Candidate]:
    from matrag.ingest import chunk_boxes

    out = []
    for i, table in enumerate(doc.tables):
        text = compact_table(table, doc)
        caption = table.caption_text(doc) or ""
        if text and _TABLE_HINT.search(text) and not _TABLE_EXCLUDE.search(caption):
            pages = sorted({p.page_no for p in table.prov})
            out.append(Candidate(doc_id=doc_id, source=f"table {i + 1}", pages=",".join(map(str, pages)),
                                 text=text, boxes=json.dumps(chunk_boxes(doc, [table]))))
    return out


def text_candidates(nodes: list[BaseNode]) -> list[Candidate]:
    """Consecutive chunks containing an explicit formula, merged (e.g. o- and e-ray lines)."""
    hits = [n for n in nodes if n.metadata.get("content_type") != "table" and _FORMULA_TEXT.search(n.get_content())
            and len(_numbers(n.get_content())) >= 3]
    groups: list[list[BaseNode]] = []
    for node in hits:
        index = int(node.node_id.rpartition("::")[2])
        if groups and int(groups[-1][-1].node_id.rpartition("::")[2]) == index - 1 and len(groups[-1]) < 3:
            groups[-1].append(node)
        else:
            groups.append([node])
    out = []
    for group in groups:
        first, last = group[0].node_id, group[-1].node_id.rpartition("::")[2]
        pages = sorted({p for n in group for p in n.metadata.get("pages", "").split(",") if p})
        boxes = [b for n in group for b in json.loads(n.metadata.get("boxes") or "[]")]
        out.append(Candidate(doc_id=group[0].metadata["doc_id"], source=f"text {first}" + (f"-{last}" if len(group) > 1 else ""),
                             pages=",".join(pages), text="\n".join(n.get_content() for n in group), boxes=json.dumps(boxes)))
    return out


def definition_context(nodes: list[BaseNode], limit: int = 2, max_chars: int = 1500) -> str:
    texts = [n.get_content()[:max_chars] for n in nodes if _DEFINITION.search(n.get_content())][:limit]
    return "\n\n".join(texts) or "(none)"


# --- extraction and checks ------------------------------------------------------


def _numbers(text: str) -> list[float]:
    out = []
    for m in _NUMBER.findall(clean_text(text).replace("−", "-")):
        try:
            out.append(float(re.sub(r"\s+", "", m)))
        except ValueError:
            continue
    return out


def numbers_in_source(formula: DispersionFormula, source_text: str) -> float:
    """Share of the formula's non-trivial coefficients that literally appear in the source."""
    values = [formula.constant]
    for t in formula.pole_terms:
        values += [t.coefficient, t.pole, *t.coefficient_T, *t.pole_T]
    values += [t.coefficient for t in formula.power_terms]
    values = [v for v in values if v not in (0.0, 1.0)]
    if not values:
        return 0.0
    # Compare magnitudes: in "(λ² − 0.007142)" the minus belongs to the formula, not the number.
    found = [abs(f) for f in _numbers(source_text)]
    ok = sum(any(abs(abs(v) - f) <= 1e-9 * max(1.0, abs(v)) for f in found) for v in values)
    return ok / len(values)


def extract_from_candidate(candidate: Candidate, context: str, llm: LLM) -> list[FormulaRecord]:
    result = llm.structured_predict(FormulaResult, FORMULA_PROMPT, context=context,
                                    source=f"{candidate.doc_id}, {candidate.source}, p. {candidate.pages}",
                                    text=candidate.text)
    return [
        FormulaRecord(formula=f, doc_id=candidate.doc_id, pages=candidate.pages, source=candidate.source,
                      boxes=candidate.boxes, numbers_in_source=round(numbers_in_source(f, candidate.text), 3),
                      problems=check_formula(f))
        for f in result.formulas
    ]


def compare_with_reference(record: FormulaRecord, entries, default_temperature_K: float = 295.0) -> None:
    """Fill reference_entry / reference_max_dn from the best-matching refractiveindex.info entry."""
    axis = record.formula.axis.lower()
    candidates = [e for e in entries if not axis or not e.direction or e.direction.lower() == axis] or entries
    lo, hi = record.formula.valid_range_um()
    temperature = record.formula.temperature_K or (default_temperature_K if record.formula.temperature_dependent else None)
    best = None
    for entry in candidates:
        a, b = max(lo, entry.wavelength_um[0]), min(hi, entry.wavelength_um[1])
        if b <= a:
            continue
        lam = np.linspace(a, b, 200)
        try:
            diff = np.abs(record.formula.refractive_index(lam, temperature) - entry.refractive_index(lam))
        except ValueError:
            continue
        if np.isfinite(diff).any():
            score = float(np.nanmax(diff))
            if best is None or score < best[0]:
                best = (score, entry.entry.path)
    if best:
        record.reference_max_dn, record.reference_entry = round(best[0], 6), best[1]


def extract_formulas(doc: DoclingDocument | None, nodes: list[BaseNode], llm: LLM,
                     min_interval_s: float = 0.0) -> list[FormulaRecord]:
    """All dispersion formulas of one paper (``doc``: its Docling document, for whole tables)."""
    doc_id = nodes[0].metadata["doc_id"] if nodes else ""
    candidates = (table_candidates(doc, doc_id) if doc is not None else []) + text_candidates(nodes)
    context = definition_context(nodes)
    throttle = Throttle(min_interval_s)
    records = []
    for candidate in candidates:
        throttle.wait()
        records += extract_from_candidate(candidate, context, llm)
    return deduplicate_formulas(records)


def _signature(f: DispersionFormula) -> tuple:
    terms = tuple((round(t.coefficient, 9), round(t.pole, 9), t.numerator_power) for t in f.pole_terms)
    return (f.material.lower(), f.axis.lower(), round(f.constant, 9), terms,
            tuple((round(t.coefficient, 9), t.power) for t in f.power_terms))


def deduplicate_formulas(records: list[FormulaRecord]) -> list[FormulaRecord]:
    """Keep one copy of formulas with identical coefficients (the best-supported one)."""
    best: dict[tuple, FormulaRecord] = {}
    for r in records:
        key = _signature(r.formula)
        if key not in best or r.numbers_in_source > best[key].numbers_in_source:
            best[key] = r
    return list(best.values())


def save_formulas(records: list[FormulaRecord], path: Path) -> None:
    """JSON Lines, one formula per line (nested coefficients kept intact)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(r.model_dump_json() + "\n" for r in records), encoding="utf-8")


def load_formulas(path: Path) -> list[FormulaRecord]:
    return [FormulaRecord.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
