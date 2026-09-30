"""Publishing the knowledge base to Qdrant Cloud, for the web app.

The web app (``web/``, a Cloudflare Worker) searches a Qdrant collection
holding, for every chunk:

- ``dense``: the chunk's embedding, copied from the local database, so the
  vectors are exactly those the evaluations were run with (nothing is
  re-embedded);
- ``bm25``: a sparse BM25 vector computed by Qdrant's own ``qdrant/bm25``
  model (tokenizer, stop words and stemmer run on the server). The web app
  sends its query text to the same model, so both sides are always tokenized
  identically;
- the chunk text and its metadata (paper, pages, boxes, ...) as payload.

The hybrid query (both lists fused with Reciprocal Rank Fusion) runs inside
Qdrant, so a search is a single request.
"""

import hashlib
import os
import re
import uuid
from collections.abc import Callable, Iterable

from matrag.config import Settings

DENSE, SPARSE = "dense", "bm25"
BM25_MODEL = "qdrant/bm25"
# Chemical formulas extracted from PDFs often come out with subscripts spaced
# out ("LiB 3 O 5"); BM25 then misses "LiB3O5". Both the indexed text and the
# query are normalized the same way (web/src/text.js has the same rule).
_SPACED_FORMULA = re.compile(r"\b(?:[A-Z][a-z]?)+(?:\s+\d{1,3}(?:\s+(?:[A-Z][a-z]?)+(?![a-z]))?)+(?![\w.])")

# Common names of optical crystals, added to a query that uses one of them.
SYNONYMS = {
    "BBO": "BaB2O4", "LBO": "LiB3O5", "BIBO": "BiB3O6", "CLBO": "CsLiB6O10", "CBO": "CsB3O5",
    "KBBF": "KBe2BO3F2", "KTP": "KTiOPO4", "KTA": "KTiOAsO4", "RTP": "RbTiOPO4", "KDP": "KH2PO4",
    "DKDP": "KD2PO4", "ADP": "NH4H2PO4", "LN": "LiNbO3", "PPLN": "LiNbO3", "LT": "LiTaO3", "PPLT": "LiTaO3",
    "ZGP": "ZnGeP2", "CSP": "CdSiP2", "AGS": "AgGaS2", "AGSe": "AgGaSe2", "BGS": "BaGa4S7", "BGSe": "BaGa4Se7",
    "LGS": "LiGaS2", "LIS": "LiInS2", "YAG": "Y3Al5O12", "YVO": "YVO4", "SBN": "SrxBa1-xNb2O6",
}


def normalize_formulas(text: str) -> str:
    """Join spaced-out subscripts of chemical formulas: 'LiB 3 O 5' -> 'LiB3O5', 'KTiOPO 4' -> 'KTiOPO4'.

    Only runs with at least two capital letters are joined, so 'Eq 5' or 'N 2' stay as they are.
    """
    def join(m: re.Match) -> str:
        s = m.group(0)
        return re.sub(r"\s+", "", s) if sum(c.isupper() for c in s) >= 2 else s

    return _SPACED_FORMULA.sub(join, text)


def expand_query(query: str) -> str:
    """The query with chemical formulas normalized and common crystal names spelled out."""
    query = normalize_formulas(query)
    extra = [formula for name, formula in SYNONYMS.items()
             if re.search(rf"\b{re.escape(name)}\b", query) and formula not in query]
    return " ".join([query, *extra])


def point_id(node_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"matrag:{node_id}"))


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


PAYLOAD_KEYS = ("doc_id", "citation", "reference", "pages", "first_page", "boxes", "source_file", "source_type",
                "content_type", "headings", "category", "material", "year", "doi")


def client(url: str | None = None, api_key: str | None = None):
    from qdrant_client import QdrantClient

    url = url or os.environ["QDRANT_URL"]
    api_key = api_key or os.environ["QDRANT_API_KEY"]
    # Port 443: Qdrant Cloud also serves its REST API there (6333 is often blocked).
    return QdrantClient(url=url, port=443, api_key=api_key, cloud_inference=True, timeout=120)


def create_collection(qc, name: str, dim: int, recreate: bool = False) -> None:
    from qdrant_client import models

    if qc.collection_exists(name):
        if not recreate:
            return
        qc.delete_collection(name)
    qc.create_collection(
        name,
        vectors_config={DENSE: models.VectorParams(size=dim, distance=models.Distance.COSINE, on_disk=False)},
        sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
        on_disk_payload=True,  # chunk texts stay on disk: the free cluster has 1 GB of RAM
    )
    for key, kind in (("doc_id", models.PayloadSchemaType.KEYWORD), ("source_type", models.PayloadSchemaType.KEYWORD),
                      ("material", models.PayloadSchemaType.KEYWORD), ("category", models.PayloadSchemaType.KEYWORD)):
        qc.create_payload_index(name, key, field_schema=kind)


def drive_id(path: str) -> str | None:
    """Google Drive file id of a file on Colab's mounted Drive (exposed as an extended attribute), if any."""
    try:
        return os.getxattr(path, "user.drive.id").decode() or None
    except (OSError, AttributeError):
        return None


def iter_points(nodes, embeddings: dict[str, list[float]], root: str | None = None):
    from qdrant_client import models

    for node in nodes:
        vector = embeddings.get(node.node_id)
        if vector is None:
            continue
        meta = node.metadata
        payload = {k: meta[k] for k in PAYLOAD_KEYS if k in meta and meta[k] not in (None, "")}
        payload["node_id"] = node.node_id
        payload["text"] = node.get_content()
        payload["text_hash"] = text_hash(payload["text"])
        if root and payload.get("source_file"):
            file_id = drive_id(os.path.join(root, payload["source_file"]))
            if file_id:
                payload["drive_id"] = file_id  # the site links the PDF on Drive
        yield models.PointStruct(
            id=point_id(node.node_id),
            vector={DENSE: list(vector),
                    SPARSE: models.Document(text=normalize_formulas(node.get_content()), model=BM25_MODEL)},
            payload=payload,
        )


def chroma_embeddings(kb, ids: list[str]) -> dict[str, list[float]]:
    """Stored embeddings of the given chunks (nothing is re-computed)."""
    collection = kb.vector_store._collection
    got = collection.get(ids=ids, include=["embeddings"])
    return {i: e for i, e in zip(got["ids"], got["embeddings"])}


def export(kb, qc, name: str, recreate: bool = False, batch: int = 64, skip_existing: bool = True,
           prune: bool = True, root: str | None = None,
           on_progress: Callable[[int, int], None] | None = None) -> int:
    """Upload every chunk of ``kb`` to the Qdrant collection ``name``; returns the number uploaded.

    Resumable: with ``skip_existing`` chunks already in the collection with the same text are not
    sent again (a chunk whose text changed is); with ``prune`` points of chunks no longer in ``kb``
    are deleted, so the collection mirrors it.
    """
    nodes = kb.nodes()
    if not nodes:
        return 0
    first = chroma_embeddings(kb, [nodes[0].node_id])
    create_collection(qc, name, len(next(iter(first.values()))), recreate)
    existing: dict[str, str | None] = {}  # point id -> text hash
    if skip_existing and not recreate:
        offset = None
        while True:
            points, offset = qc.scroll(name, limit=1000, offset=offset, with_payload=["text_hash"], with_vectors=False)
            existing |= {str(p.id): (p.payload or {}).get("text_hash") for p in points}
            if offset is None:
                break
    wanted = {point_id(n.node_id) for n in nodes}
    stale = sorted(set(existing) - wanted)
    if prune and stale:
        from qdrant_client import models

        for start in range(0, len(stale), 1000):
            qc.delete(name, points_selector=models.PointIdsList(points=stale[start:start + 1000]), wait=True)
    todo = [n for n in nodes if existing.get(point_id(n.node_id)) != text_hash(n.get_content())]
    sent = 0
    for start in range(0, len(todo), batch):
        part = todo[start:start + batch]
        embeddings = chroma_embeddings(kb, [n.node_id for n in part])
        qc.upsert(name, points=list(iter_points(part, embeddings, root)), wait=True)
        sent += len(part)
        if on_progress:
            on_progress(sent, len(todo))
    return sent


def search(qc, name: str, query: str, query_vector: list[float], top_k: int = 8, mode: str = "hybrid",
           doc_ids: Iterable[str] | None = None, prefetch: int = 50):
    """The web app's search, in Python (for evaluation): hybrid = dense + BM25 fused with RRF in Qdrant."""
    from qdrant_client import models

    flt = None
    if doc_ids:
        flt = models.Filter(must=[models.FieldCondition(key="doc_id", match=models.MatchAny(any=list(doc_ids)))])
    sparse_query = models.Document(text=expand_query(query), model=BM25_MODEL)
    if mode == "vector":
        return qc.query_points(name, query=query_vector, using=DENSE, limit=top_k, query_filter=flt,
                               with_payload=True).points
    if mode == "bm25":
        return qc.query_points(name, query=sparse_query, using=SPARSE, limit=top_k, query_filter=flt,
                               with_payload=True).points
    return qc.query_points(
        name,
        prefetch=[models.Prefetch(query=query_vector, using=DENSE, limit=prefetch, filter=flt),
                  models.Prefetch(query=sparse_query, using=SPARSE, limit=prefetch, filter=flt)],
        query=models.FusionQuery(fusion=models.Fusion.RRF), limit=top_k, with_payload=True,
    ).points


MAX_ASSET_BYTES = 25 * 1024 * 1024  # Cloudflare's limit per static asset


def copy_pdfs(kb, root: str, dest: str) -> tuple[int, list[str]]:
    """Copy the PDF of every full-text paper in ``kb`` from ``root`` to ``dest`` (same relative paths),
    for the site's PDF Worker. Returns the number copied and the files skipped (missing or too large)."""
    import shutil

    files = sorted({n.metadata.get("source_file") for n in kb.nodes()
                    if n.metadata.get("source_type") == "full_text_pdf" and n.metadata.get("source_file")})
    copied, skipped = 0, []
    for rel in files:
        src, dst = os.path.join(root, rel), os.path.join(dest, rel)
        if not os.path.isfile(src) or os.path.getsize(src) > MAX_ASSET_BYTES:
            skipped.append(rel)
            continue
        if not (os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src)):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        copied += 1
    return copied, skipped


def collection_name(settings: Settings) -> str:
    return settings.corpus
