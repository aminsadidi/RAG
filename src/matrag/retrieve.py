"""Stage 3: retrieval.

Three modes are available so they can be compared experimentally:

- ``vector``: semantic similarity of embeddings (finds paraphrases).
- ``bm25``:   keyword matching (finds exact symbols like "γ_air", "ν3", "CO2").
- ``hybrid``: both, merged with Reciprocal Rank Fusion (Cormack et al., 2009).
"""

from enum import Enum

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.llms import MockLLM
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.vector_stores import FilterOperator, MetadataFilter, MetadataFilters
from llama_index.retrievers.bm25 import BM25Retriever

from matrag.index import KnowledgeBase


class RetrievalMode(str, Enum):
    vector = "vector"
    bm25 = "bm25"
    hybrid = "hybrid"


def make_retriever(
    kb: KnowledgeBase,
    mode: RetrievalMode = RetrievalMode.hybrid,
    top_k: int = 8,
    doc_ids: list[str] | None = None,
) -> BaseRetriever:
    """Build a retriever, optionally restricted to some papers."""
    nodes = kb.nodes(doc_ids=doc_ids)
    if not nodes:
        raise ValueError("The knowledge base is empty (or no chunks match the given doc_ids).")

    filters = None
    if doc_ids is not None:
        filters = MetadataFilters(
            filters=[MetadataFilter(key="doc_id", value=doc_ids, operator=FilterOperator.IN)]
        )
    vector = kb.index.as_retriever(similarity_top_k=top_k, filters=filters)
    # BM25 is built from the (already filtered) chunk list.
    bm25 = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=min(top_k, len(nodes)))

    if mode == RetrievalMode.vector:
        return vector
    if mode == RetrievalMode.bm25:
        return bm25
    return QueryFusionRetriever(
        [vector, bm25],
        mode="reciprocal_rerank",
        similarity_top_k=top_k,
        num_queries=1,  # use the question as-is; no LLM query rewriting
        # An LLM is only used for query rewriting, which is off; the placeholder
        # stops LlamaIndex from looking for a default (OpenAI) model.
        llm=MockLLM(),
        use_async=False,
    )
