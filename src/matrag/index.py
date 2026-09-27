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
    )


class KnowledgeBase:
    def __init__(self, settings: Settings, embed_model: BaseEmbedding):
        self.settings = settings
        settings.storage_dir.mkdir(parents=True, exist_ok=True)

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

    def add_document(self, doc_id: str, nodes: list[BaseNode]) -> None:
        """Add (or replace) all chunks of one paper."""
        self.remove_document(doc_id)
        self.index.insert_nodes(nodes, show_progress=len(nodes) > 50)
        self.docstore.add_documents(nodes)
        self._persist()

    def remove_document(self, doc_id: str) -> None:
        self.vector_store.delete(ref_doc_id=doc_id)
        for node in self.nodes(doc_ids=[doc_id]):
            self.docstore.delete_document(node.node_id)
        self._persist()

    def nodes(self, doc_ids: list[str] | None = None) -> list[BaseNode]:
        nodes = list(self.docstore.docs.values())
        if doc_ids is not None:
            nodes = [n for n in nodes if n.metadata.get("doc_id") in doc_ids]
        return sorted(nodes, key=_node_order)

    def doc_ids(self) -> list[str]:
        return sorted({n.metadata["doc_id"] for n in self.docstore.docs.values()})

    def _persist(self) -> None:
        self.docstore.persist(str(self.settings.docstore_path))


def _node_order(node: BaseNode) -> tuple[str, int]:
    doc_id, _, n = node.node_id.rpartition("::")
    return (doc_id, int(n) if n.isdigit() else 0)
