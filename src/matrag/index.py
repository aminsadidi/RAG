"""Stage 2: the knowledge base (vector database + chunk store).

Chunk embeddings live in ChromaDB (persistent, on disk). A copy of every
chunk is also kept in a LlamaIndex docstore so the keyword (BM25) retriever
can work on the same chunks as the vector retriever.
"""

import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import BaseNode
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.vector_stores.chroma import ChromaVectorStore

from matrag.config import Settings


def make_embed_model(settings: Settings) -> BaseEmbedding:
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    return HuggingFaceEmbedding(
        model_name=settings.embed_model,
        query_instruction=settings.embed_query_instruction or None,
        max_length=settings.chunk_max_tokens,
        embed_batch_size=settings.embed_batch_size,
    )


class KnowledgeBase:
    def __init__(self, settings: Settings, embed_model: BaseEmbedding):
        self.settings = settings
        settings.docstore_path.parent.mkdir(parents=True, exist_ok=True)

        client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        # Cosine distance is the standard choice for normalized sentence embeddings.
        collection = client.get_or_create_collection(
            settings.collection_name, metadata={"hnsw:space": "cosine"}
        )
        self.vector_store = ChromaVectorStore(chroma_collection=collection)
        self.index = VectorStoreIndex.from_vector_store(self.vector_store, embed_model=embed_model)

        if settings.docstore_path.exists():
            self.docstore = SimpleDocumentStore.from_persist_path(str(settings.docstore_path))
        else:
            self.docstore = SimpleDocumentStore()

        # Bumped on every change, so callers can cache things built from the chunks (BM25).
        self.revision = 0

    def add_document(self, doc_id: str, nodes: list[BaseNode], persist: bool = True) -> None:
        """Add (or replace) all chunks of one paper."""
        self.add_documents({doc_id: nodes}, persist)

    def add_documents(self, docs: dict[str, list[BaseNode]], persist: bool = True) -> None:
        """Add (or replace) several papers at once (one embedding batch).

        With ``persist=False`` the chunk store is only written by a later
        ``persist()``: rewriting it after each of thousands of papers would
        make a large ingest quadratic.
        """
        indexed = self._doc_node_ids()
        for doc_id in docs:
            if doc_id in indexed:
                self.remove_document(doc_id, persist=False, _node_ids=indexed[doc_id])
        nodes = [n for doc_nodes in docs.values() for n in doc_nodes]
        if nodes:
            self.index.insert_nodes(nodes, show_progress=len(nodes) > 50)
            self.docstore.add_documents(nodes)
        self.revision += 1
        if persist:
            self.persist()

    def remove_document(self, doc_id: str, persist: bool = True, _node_ids: list[str] | None = None) -> None:
        self.vector_store.delete(ref_doc_id=doc_id)
        node_ids = _node_ids if _node_ids is not None else self._doc_node_ids().get(doc_id, [])
        for node_id in node_ids:
            self.docstore.delete_document(node_id, raise_error=False)
        self.revision += 1
        if persist:
            self.persist()

    def _doc_node_ids(self) -> dict[str, list[str]]:
        found: dict[str, list[str]] = {}
        for node_id, node in self.docstore.docs.items():
            found.setdefault(node.metadata.get("doc_id"), []).append(node_id)
        return found

    def nodes(self, doc_ids: list[str] | None = None) -> list[BaseNode]:
        nodes = list(self.docstore.docs.values())
        if doc_ids is not None:
            wanted = set(doc_ids)
            nodes = [n for n in nodes if n.metadata.get("doc_id") in wanted]
        return sorted(nodes, key=_node_order)

    def doc_ids(self) -> list[str]:
        return sorted({n.metadata["doc_id"] for n in self.docstore.docs.values()})

    def doc_versions(self) -> dict[str, int]:
        """Ingest version each paper was indexed with (0 if unknown)."""
        return {n.metadata["doc_id"]: n.metadata.get("ingest_version", 0) for n in self.docstore.docs.values()}

    def doc_source_types(self) -> dict[str, str]:
        """What each paper was indexed from: full text, abstract or metadata only."""
        return {n.metadata["doc_id"]: n.metadata.get("source_type", "full_text_pdf")
                for n in self.docstore.docs.values()}

    def doc_source_files(self) -> dict[str, str]:
        """The file each paper was indexed from (relative to the corpus folder)."""
        return {n.metadata["doc_id"]: n.metadata.get("source_file", "") for n in self.docstore.docs.values()}

    def persist(self) -> None:
        self.docstore.persist(str(self.settings.docstore_path))


def _node_order(node: BaseNode) -> tuple[str, int]:
    doc_id, _, n = node.node_id.rpartition("::")
    return (doc_id, int(n) if n.isdigit() else 0)
