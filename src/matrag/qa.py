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
{extra_rules}
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
    label = f"{meta.get('citation') or meta.get('doc_id', '?')}, p. {meta.get('pages') or '?'}"
    if meta.get("content_type") == "table":
        label += ", table"
    return label


def format_context(nodes: list[NodeWithScore]) -> str:
    return "\n\n".join(
        f"[{i}] ({format_source_label(n)})\n{n.get_content()}" for i, n in enumerate(nodes, start=1)
    )


def build_rag_prompt(question: str, nodes: list[NodeWithScore], extra_rules: list[str] = ()) -> str:
    return RAG_PROMPT.format(
        not_found=NOT_FOUND,
        extra_rules="".join(f"- {rule}\n" for rule in extra_rules),
        context=format_context(nodes),
        question=question,
    )


def _language_rules(language: str | None) -> list[str]:
    if not language:
        return []
    return [f"Write the answer in {language}; keep symbols, units and numbers as in the sources."]


def answer_with_rag(question: str, retriever: BaseRetriever, llm: LLM, language: str | None = None) -> Answer:
    nodes = retriever.retrieve(question)
    if not nodes:
        return Answer(question, NOT_FOUND)
    prompt = build_rag_prompt(question, nodes, _language_rules(language))
    return Answer(question, llm.complete(prompt).text.strip(), nodes)


def build_context_pack(
    question: str, nodes: list[NodeWithScore], about: dict[str, str], language: str | None = None
) -> str:
    """A self-contained prompt file to upload to any chat assistant.

    Retrieval is done by this system; generation by whatever model reads the
    file. The prompt is the same one ``answer_with_rag`` sends, so answers
    obtained either way are comparable.
    """
    # Chat apps turn "[2]" into their own file-citation widget, which hides the
    # page; asking for plain-text citations keeps them visible.
    rules = ["Write citations as plain text with the page, e.g. (Source 2, p. 5), not as links or footnotes."]
    rules += _language_rules(language)
    about_lines = "\n".join(f"- {key}: {value}" for key, value in about.items())
    references = dict.fromkeys(n.metadata.get("reference") or n.metadata.get("doc_id", "?") for n in nodes)
    reference_lines = "\n".join(f"- {ref}" for ref in references)
    return (
        build_rag_prompt(question, nodes, rules)
        + "\n\n---\nAbout this file (for the reader; not part of the sources):\n"
        + about_lines
        + "\n\nPapers the sources come from:\n"
        + reference_lines
        + "\n"
    )


def answer_without_rag(question: str, llm: LLM, language: str | None = None) -> Answer:
    prompt = NO_RAG_PROMPT.format(not_found=NOT_FOUND, question=question)
    if language:
        prompt = prompt.replace("\nQuestion:", f"Write the answer in {language}.\n\nQuestion:", 1)
    return Answer(question, llm.complete(prompt).text.strip())
