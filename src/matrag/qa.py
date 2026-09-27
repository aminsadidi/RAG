"""Stage 4: question answering grounded in retrieved sources.

The prompt is written out explicitly (rather than hidden in a library
default) so it can be reported in the paper and kept fixed across
experiments. ``answer_without_rag`` is the baseline: the same model
answering from its own memory, with no retrieved context.
"""

from dataclasses import dataclass, field

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.llms import LLM
from llama_index.core.schema import NodeWithScore

NOT_FOUND = "Not found in the provided sources."

RAG_PROMPT = """\
You are a scientific assistant for physics and materials science.
Answer the question using ONLY the numbered sources below.

Rules:
- Cite every statement with the number of its source, e.g. [2].
- Report numerical values exactly as written, with their units, uncertainties
  and measurement conditions (temperature, pressure, broadening gas, spectral band).
- Distinguish experimental from theoretical/computed values when the source does.
- If the sources do not contain the answer, reply exactly: "{not_found}"

Sources:
{context}

Question: {question}
Answer:"""

NO_RAG_PROMPT = """\
You are a scientific assistant for physics and materials science.
Answer the question. Report numerical values with their units.
If you do not know, reply exactly: "{not_found}"

Question: {question}
Answer:"""


@dataclass
class Answer:
    question: str
    text: str
    sources: list[NodeWithScore] = field(default_factory=list)


def format_source_label(node: NodeWithScore) -> str:
    meta = node.metadata
    label = f"{meta.get('doc_id', '?')}, p. {meta.get('pages') or '?'}"
    if meta.get("content_type") == "table":
        label += ", table"
    return label


def format_context(nodes: list[NodeWithScore]) -> str:
    return "\n\n".join(
        f"[{i}] ({format_source_label(n)})\n{n.get_content()}" for i, n in enumerate(nodes, start=1)
    )


def answer_with_rag(question: str, retriever: BaseRetriever, llm: LLM) -> Answer:
    nodes = retriever.retrieve(question)
    if not nodes:
        return Answer(question, NOT_FOUND)
    prompt = RAG_PROMPT.format(not_found=NOT_FOUND, context=format_context(nodes), question=question)
    return Answer(question, llm.complete(prompt).text.strip(), nodes)


def answer_without_rag(question: str, llm: LLM) -> Answer:
    prompt = NO_RAG_PROMPT.format(not_found=NOT_FOUND, question=question)
    return Answer(question, llm.complete(prompt).text.strip())
