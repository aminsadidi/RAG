"""Stage 5: structured extraction of property values.

For each candidate chunk the LLM returns ``PropertyRecord`` objects (JSON
constrained by the Pydantic schema). Every record is then checked against
the chunk text, so values the model invented can be detected and counted.

Candidate chunks come either from retrieval (cheap: only chunks relevant to
the requested properties) or from every chunk of the selected papers
(``exhaustive``: higher recall, many more LLM calls).
"""

import csv
import json
import math
import re
import unicodedata
from collections.abc import Iterable
from pathlib import Path

from llama_index.core import PromptTemplate
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.llms import LLM
from llama_index.core.schema import BaseNode

from matrag.llm import Throttle
from matrag.schema import ExtractedRecord, ExtractionResult

EXTRACT_PROMPT = PromptTemplate("""\
You extract physical property data from scientific papers.

Extract every numerical value of these properties reported in the text:
{properties}

Rules:
- Only extract values explicitly stated in the text. Never infer, compute or
  recall values from memory.
- One record per value. A table row with several values gives several records.
- Values cited from other works still count; set method to "compiled".
- The value must be the property itself. Do NOT extract counts (e.g. "182 lines"),
  quantum-number ranges, years, figure/equation numbers or fit-validity limits.
- "material" is the substance (e.g. "CO2"), never the property name.
- "evidence" must be copied verbatim from the text.
- If the text reports none of these properties, return an empty list.

Text (from {source}):
\"\"\"
{text}
\"\"\"
""")

_DASHES = dict.fromkeys(map(ord, "−‒–—‐‑"), "-")


def normalize(text: str) -> str:
    """Normalize for literal comparison: Unicode forms, dashes, case, whitespace."""
    text = unicodedata.normalize("NFKC", text).translate(_DASHES).lower()
    return re.sub(r"\s+", "", text)


# A number in normalized text (whitespace removed) only counts where it stands alone: no digit, "." or "<digit>,"
# just before it, and no digit or ".<digit>" / ",<digit>" just after. So "0.07" is not found in "0.0712", "2.3"
# not in "12.35", "96k" not in "296k".
_BEFORE = re.compile(r"(?:\d|\.|\d,)$")
_AFTER = re.compile(r"^(?:\d|[.,]\d)")
_SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
MIN_EVIDENCE = 20  # characters: a few words or a lone number "verify" against almost any passage


def value_in_text(value_text: str, source_text: str) -> bool:
    """``value_text`` (as written in the paper) occurs in the normalized ``source_text`` as a whole number, not inside
    a longer one; a value without a digit never does."""
    needle = normalize(value_text)
    if not re.search(r"\d", needle):
        return False
    start = source_text.find(needle)
    while start != -1:
        end = start + len(needle)
        if not _BEFORE.search(source_text[:start]) and not _AFTER.match(source_text[end:]):
            return True
        start = source_text.find(needle, start + 1)
    return False


def parse_value(value_text: str) -> float | None:
    """The number a value is written as: "0.0712(3)" -> 0.0712, "1.23 × 10^-22" -> 1.23e-22, "2.5·10⁻³" -> 0.0025,
    "1.5e-4", "−3.2" -> -3.2; None when no number can be read."""
    t = unicodedata.normalize("NFKC", value_text).translate(_DASHES).replace("−", "-").translate(_SUPERSCRIPT)
    t = re.sub(r"\s+", "", t).replace("−", "-")
    m = re.match(r"([-+]?)(\d+(?:\.\d*)?|\.\d+)(?:\(\d+\))?(?:(?:[x×*·]|\\times)10\^?\{?([-+]?\d+)\}?|[eE]([-+]?\d+))?", t)
    if not m:
        return None
    number = float(m.group(1) + m.group(2))
    exponent = m.group(3) or m.group(4)
    return number * 10 ** int(exponent) if exponent else number


def value_checks(record, source_text: str) -> tuple[bool, bool]:
    """(evidence_verified, value_in_source) of an extracted record against the normalized text of its chunk.

    evidence_verified: the evidence, at least MIN_EVIDENCE characters, is in the text verbatim.
    value_in_source: value_text stands alone in the text (value_in_text) and says the same number as ``value``.
    """
    evidence = (record.evidence or "").strip()
    evidence_ok = len(evidence) >= MIN_EVIDENCE and normalize(evidence) in source_text
    parsed = parse_value(record.value_text or "")
    same = parsed is not None and math.isclose(parsed, record.value, rel_tol=1e-6, abs_tol=1e-300)
    return evidence_ok, same and value_in_text(record.value_text or "", source_text)


def extract_from_node(node: BaseNode, properties: list[str], llm: LLM) -> list[ExtractedRecord]:
    meta = node.metadata
    result = llm.structured_predict(
        ExtractionResult,
        EXTRACT_PROMPT,
        properties="\n".join(f"- {p}" for p in properties),
        source=f"{meta.get('doc_id')}, p. {meta.get('pages')}",
        text=node.get_content(),
    )
    source_text = normalize(node.get_content())
    out = []
    for record in result.records:
        evidence_ok, value_ok = value_checks(record, source_text)
        out.append(ExtractedRecord(**record.model_dump(), doc_id=meta.get("doc_id", ""), node_id=node.node_id,
                                   pages=meta.get("pages", ""), evidence_verified=evidence_ok, value_in_source=value_ok))
    return out


def candidate_nodes(
    properties: list[str], retriever: BaseRetriever | None, nodes: list[BaseNode] | None
) -> list[BaseNode]:
    """Chunks to run extraction on: all given ``nodes``, else retrieved ones."""
    if nodes is not None:
        return nodes
    if retriever is None:
        raise ValueError("Pass either a retriever or a list of nodes.")
    seen: dict[str, BaseNode] = {}
    # One query per property, so each property gets its own relevant chunks.
    for prop in properties:
        for hit in retriever.retrieve(prop):
            seen.setdefault(hit.node.node_id, hit.node)
    return list(seen.values())


def extract(
    properties: list[str],
    llm: LLM,
    retriever: BaseRetriever | None = None,
    nodes: list[BaseNode] | None = None,
    min_interval_s: float = 0.0,
) -> list[ExtractedRecord]:
    throttle = Throttle(min_interval_s)
    records: list[ExtractedRecord] = []
    for node in candidate_nodes(properties, retriever, nodes):
        throttle.wait()
        records.extend(extract_from_node(node, properties, llm))
    return deduplicate(records)


def deduplicate(records: Iterable[ExtractedRecord]) -> list[ExtractedRecord]:
    """Drop repeats of the same value, e.g. when overlapping chunks both contain it."""
    unique: dict[tuple, ExtractedRecord] = {}
    for r in records:
        key = (r.doc_id, normalize(r.material), normalize(r.property), r.value,
               normalize(r.spectral_position or ""), normalize(r.broadener or ""))
        # Prefer the copy whose evidence could be verified.
        if key not in unique or (r.evidence_verified and not unique[key].evidence_verified):
            unique[key] = r
    return list(unique.values())


def save_records(records: list[ExtractedRecord], path: Path) -> None:
    """Write records as CSV or JSON Lines, chosen by the file extension."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [r.model_dump() for r in records]
    if path.suffix == ".jsonl":
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), "utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ExtractedRecord.model_fields))
        writer.writeheader()
        writer.writerows(rows)
