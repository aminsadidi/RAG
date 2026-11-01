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


_NUMBER = re.compile(
    r"([+-]?\d+(?:\.\d+)?)(?:\(\d+\))?"  # 0.0712, with its uncertainty in brackets dropped: 0.0712(3)
    r"(?:(?:x|×|·|\*|\\times|\\cdot)10\^?\{?([+-]?\d+)\}?|e([+-]?\d+))?"  # × 10^-22, ·10⁻²², e-22
)


def parse_number(value_text: str) -> float | None:
    """The number a value is written as ("0.0712(3)", "1.23 × 10^-22", "1.23·10⁻²²"), or None."""
    m = _NUMBER.match(normalize(value_text))
    if not m:
        return None
    exponent = m.group(2) or m.group(3)
    return float(m.group(1)) * 10 ** int(exponent) if exponent else float(m.group(1))


def number_in(value_text: str, source_text: str) -> bool:
    """Whether the value, as written, stands in the (normalized) source on its own: not part of a longer number
    ("0.07" is not in "0.0712", "2.3" not in "12.35", "96 K" not in "296 K"). Text without a digit never is."""
    needle = normalize(value_text)
    if not re.search(r"\d", needle):
        return False
    for m in re.finditer(re.escape(needle), source_text):
        before = source_text[m.start() - 1] if m.start() else ""
        after = source_text[m.end():m.end() + 2]
        if before and (before.isdigit() or before == "."):
            continue
        if needle[-1].isdigit() and (after[:1].isdigit() or (after[:1] == "." and after[1:2].isdigit())):
            continue
        return True
    return False


def value_checked(value: float, value_text: str, source_text: str) -> bool:
    """The value as written is in the source on its own, and the number recorded is that one."""
    parsed = parse_number(value_text)
    return number_in(value_text, source_text) and parsed is not None and math.isclose(parsed, value, rel_tol=1e-6, abs_tol=1e-12)


def evidence_checked(evidence: str, source_text: str) -> bool:
    """A quote long enough to mean something (20 characters) that is in the source."""
    quote = normalize(evidence)
    return len(quote) >= 20 and quote in source_text


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
    return [
        ExtractedRecord(
            **record.model_dump(),
            doc_id=meta.get("doc_id", ""),
            node_id=node.node_id,
            pages=meta.get("pages", ""),
            evidence_verified=evidence_checked(record.evidence, source_text),
            value_in_source=value_checked(record.value, record.value_text, source_text),
        )
        for record in result.records
    ]


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
