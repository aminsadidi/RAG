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
            evidence_verified=normalize(record.evidence) in source_text,
            value_in_source=normalize(record.value_text) in source_text,
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
