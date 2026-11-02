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
import json
import os
import re
import uuid
from collections.abc import Callable, Iterable

from matrag.config import Settings
from matrag.crystal_names import CRYSTAL_NAMES

DENSE, SPARSE = "dense", "bm25"
BM25_MODEL = "qdrant/bm25"
# Chemical formulas extracted from PDFs often come out with subscripts spaced
# out ("LiB 3 O 5"); BM25 then misses "LiB3O5". Both the indexed text and the
# query are normalized the same way (web/src/text.js runs this same pattern from shared.json). Word characters
# and digits are spelled out ASCII: Python's \w, \d and \b are Unicode, JavaScript's ASCII, so "LiNbO 3λ=1"
# was joined by one and not the other.
_SPACED_FORMULA = re.compile(
    r"(?<![A-Za-z0-9_])(?:[A-Z][a-z]?)+(?:\s+[0-9]{1,3}(?:\s+(?:[A-Z][a-z]?)+(?![a-z]))?)+(?![A-Za-z0-9_.])")

# Every name of every crystal (crystal_names.py) -> its formula; scripts/quality and the site read it from shared.json.
SYNONYMS = {name: formula for formula, names in CRYSTAL_NAMES.items() for name in names}


# Subscript (LiNbO₃), Persian (LiNbO۳), Arabic-Indic and full-width digits, read as ASCII digits.
_DIGITS = {start + i: str(i) for start in (0x2080, 0x06F0, 0x0660, 0xFF10) for i in range(10)}


def normalize_formulas(text: str) -> str:
    """Join spaced-out subscripts of chemical formulas: 'LiB 3 O 5' -> 'LiB3O5', 'KTiOPO 4' -> 'KTiOPO4'.

    Only runs with at least two capital letters are joined, so 'Eq 5' or 'N 2' stay as they are.
    Subscript and Persian digits become ASCII digits first: 'LiNbO₃' -> 'LiNbO3'.
    """
    def join(m: re.Match) -> str:
        s = m.group(0)
        return re.sub(r"\s+", "", s) if sum(c.isupper() for c in s) >= 2 else s

    return _SPACED_FORMULA.sub(join, text.translate(_DIGITS))


def expand_query(query: str) -> str:
    """The query with chemical formulas normalized and every crystal it names, under any of its names, spelled out
    as its formula ('beta barium borate' -> + BaB2O4). Adding the abbreviation too (LiNbO3 -> + LN) lowered the
    MRR@10 on 200 gold questions, so it is not done."""
    from matrag.crystal_names import find_crystals

    query = normalize_formulas(query)
    extra = [f for f in find_crystals(query)[0] if f not in query]
    return " ".join([query, *dict.fromkeys(extra)])


_FORMULA = re.compile(r"\b(?:[A-Z][a-z]?\d*(?:\.\d+)?){2,}\b")
_ELEMENTS = set("""H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr
Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re
Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu""".split())


def query_materials(query: str) -> list[str]:
    """Chemical formulas and crystal abbreviations of a query (the formula part of text.js queryTerms)."""
    from matrag.crystal_names import find_crystals

    named, text = find_crystals(normalize_formulas(query))
    formulas = [w for w in _FORMULA.findall(text)
                if all(e in _ELEMENTS for e in re.findall(r"[A-Z][a-z]?", w)) and re.search(r"[\da-z]", w)]
    return list(dict.fromkeys(named + formulas))


def point_id(node_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"matrag:{node_id}"))


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


# Fields other scripts add to the points after the export (scripts/quality: enrich.py, enrich_docs.py,
# passage_basis.py, tag_handbooks.py). The export never makes them, so it must not wipe them.
ENRICHED_KEYS = ("crystals", "junk", "basis_p", "has")

PAYLOAD_KEYS = ("doc_id", "citation", "reference", "pages", "first_page", "boxes", "source_file", "source_type",
                "content_type", "headings", "category", "material", "year", "doi", "conversion", "pdf_mismatch")


def client(url: str | None = None, api_key: str | None = None):
    from qdrant_client import QdrantClient

    url = url or os.environ["QDRANT_URL"]
    api_key = api_key or os.environ["QDRANT_API_KEY"]
    # Port 443: Qdrant Cloud also serves its REST API there (6333 is often blocked).
    return QdrantClient(url=url, port=443, api_key=api_key, cloud_inference=True, timeout=120)


# keyword indexes for the site's filters (``crystals``: its focused search, web/src/index.js)
INDEXED_KEYS = ("doc_id", "source_type", "material", "category", "crystals")


def create_collection(qc, name: str, dim: int, recreate: bool = False) -> None:
    from qdrant_client import models

    if qc.collection_exists(name):
        if not recreate:
            # a collection made before an index was added gets it now
            have = set((qc.get_collection(name).payload_schema or {}).keys())
            for key in INDEXED_KEYS:
                if key not in have:
                    qc.create_payload_index(name, key, field_schema=models.PayloadSchemaType.KEYWORD)
            return
        qc.delete_collection(name)
    qc.create_collection(
        name,
        vectors_config={DENSE: models.VectorParams(size=dim, distance=models.Distance.COSINE, on_disk=False)},
        sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
        on_disk_payload=True,  # chunk texts stay on disk: the free cluster has 1 GB of RAM
    )
    for key in INDEXED_KEYS:
        qc.create_payload_index(name, key, field_schema=models.PayloadSchemaType.KEYWORD)


def drive_id(path: str) -> str | None:
    """Google Drive file id of a file on Colab's mounted Drive (exposed as an extended attribute), if any."""
    try:
        return os.getxattr(path, "user.drive.id").decode() or None
    except (OSError, AttributeError):
        return None


def node_payload(node, root: str | None = None) -> dict:
    """The payload the export writes for a chunk (not the fields of ENRICHED_KEYS, added later by other scripts)."""
    meta = node.metadata
    payload = {k: meta[k] for k in PAYLOAD_KEYS if k in meta and meta[k] not in (None, "")}
    payload["node_id"] = node.node_id
    payload["text"] = node.get_content()
    payload["text_hash"] = text_hash(payload["text"])
    if root and payload.get("source_file"):
        file_id = drive_id(os.path.join(root, payload["source_file"]))
        if file_id:
            payload["drive_id"] = file_id  # the site links the PDF on Drive
    return payload


def meta_hash(payload: dict) -> str:
    """Hash of a payload's metadata (PAYLOAD_KEYS and the text hash): what decides that a point needs new metadata."""
    keys = sorted(k for k in (*PAYLOAD_KEYS, "node_id", "text_hash") if payload.get(k) not in (None, ""))
    return hashlib.sha1(json.dumps({k: payload[k] for k in keys}, sort_keys=True, ensure_ascii=False, default=str)
                        .encode("utf-8")).hexdigest()[:16]


def sparse_vector(text: str):
    """The chunk's BM25 vector, computed by Qdrant's own model on the server (cloud inference)."""
    from qdrant_client import models

    return models.Document(text=normalize_formulas(text), model=BM25_MODEL)


def iter_points(nodes, embeddings: dict[str, list[float]], root: str | None = None, keep: dict[str, dict] | None = None):
    """Points of the chunks; ``keep``: point id -> payload fields to carry over (the ENRICHED_KEYS of the old point)."""
    from qdrant_client import models

    for node in nodes:
        vector = embeddings.get(node.node_id)
        if vector is None:
            continue
        payload = node_payload(node, root)
        pid = point_id(node.node_id)
        payload.update((keep or {}).get(pid, {}))
        yield models.PointStruct(id=pid, vector={DENSE: list(vector), SPARSE: sparse_vector(node.get_content())}, payload=payload)


def chroma_embeddings(kb, ids: list[str]) -> dict[str, list[float]]:
    """Stored embeddings of the given chunks (nothing is re-computed)."""
    collection = kb.vector_store._collection
    got = collection.get(ids=ids, include=["embeddings"])
    return {i: e for i, e in zip(got["ids"], got["embeddings"])}


def export(kb, qc, name: str, recreate: bool = False, batch: int = 64, skip_existing: bool = True,
           prune: bool = True, root: str | None = None, keep: Iterable[str] = (),
           on_progress: Callable[[int, int], None] | None = None) -> int:
    """Upload every chunk of ``kb`` to the Qdrant collection ``name``; returns the number of points written.

    Resumable: with ``skip_existing`` chunks already in the collection with the same text and metadata are
    not sent again. A chunk whose text changed is sent again (new vectors); one whose metadata only changed
    gets its new metadata in place (no vectors sent). Either way the fields other scripts added
    (ENRICHED_KEYS: crystals, junk, ...) are kept. With ``prune`` points of chunks no longer in ``kb`` are
    deleted, so the collection mirrors it. Papers in ``keep`` are left as they are in the collection: their
    points were made elsewhere (scripts/ocr_gh, from a conversion ``kb`` lacks).
    """
    from qdrant_client import models

    keep = set(keep)
    nodes = [n for n in kb.nodes() if n.metadata.get("doc_id") not in keep]
    if not nodes:
        return 0
    first = chroma_embeddings(kb, [nodes[0].node_id])
    create_collection(qc, name, len(next(iter(first.values()))), recreate)
    existing: dict[str, dict] = {}  # point id -> its payload (without the text)
    if skip_existing and not recreate:
        offset = None
        fields = sorted({*PAYLOAD_KEYS, "node_id", "text_hash", *ENRICHED_KEYS})
        while True:
            points, offset = qc.scroll(name, limit=1000, offset=offset, with_payload=fields, with_vectors=False)
            existing |= {str(p.id): (p.payload or {}) for p in points if (p.payload or {}).get("doc_id") not in keep}
            if offset is None:
                break
    wanted = {point_id(n.node_id) for n in nodes}
    stale = sorted(set(existing) - wanted)
    if prune and stale:
        for start in range(0, len(stale), 1000):
            qc.delete(name, points_selector=models.PointIdsList(points=stale[start:start + 1000]), wait=True)
    enriched = {pid: {k: p[k] for k in ENRICHED_KEYS if k in p} for pid, p in existing.items()}
    resend, relabel = [], []
    for n in nodes:
        old = existing.get(point_id(n.node_id))
        if old is None or old.get("text_hash") != text_hash(n.get_content()):
            resend.append(n)
        elif meta_hash(old) != meta_hash(node_payload(n)):
            relabel.append(n)
    total, sent = len(resend) + len(relabel), 0
    for start in range(0, len(resend), batch):
        part = resend[start:start + batch]
        embeddings = chroma_embeddings(kb, [n.node_id for n in part])
        qc.upsert(name, points=list(iter_points(part, embeddings, root, keep=enriched)), wait=True)
        sent += len(part)
        if on_progress:
            on_progress(sent, total)
    for start in range(0, len(relabel), batch):
        ops = []
        for n in relabel[start:start + batch]:
            pid, payload = point_id(n.node_id), node_payload(n, root)
            payload.pop("text", None)  # the text is unchanged (same hash): not sent again
            ops.append(models.SetPayloadOperation(set_payload=models.SetPayload(payload=payload, points=[pid])))
            gone = [k for k in PAYLOAD_KEYS if k in existing[pid] and k not in payload]
            if gone:  # a metadata field removed from the chunk goes from the point too
                ops.append(models.DeletePayloadOperation(delete_payload=models.DeletePayload(keys=gone, points=[pid])))
        qc.batch_update_points(name, update_operations=ops, wait=True)
        sent += len(relabel[start:start + batch])
        if on_progress:
            on_progress(sent, total)
    return sent


def search(qc, name: str, query: str, query_vector: list[float], top_k: int = 8, mode: str = "hybrid",
           doc_ids: Iterable[str] | None = None, prefetch: int = 50):
    """The web app's search, in Python (for evaluation): hybrid = dense + BM25 fused with RRF in Qdrant."""
    from qdrant_client import models

    flt = None
    if doc_ids:
        flt = models.Filter(must=[models.FieldCondition(key="doc_id", match=models.MatchAny(any=list(doc_ids)))])
    sparse_query = models.Document(text=expand_query(query), model=BM25_MODEL)
    # The materials of the query also searched alone, so common words cannot outweigh them (as on the site).
    materials = query_materials(query)
    named = [models.Prefetch(query=models.Document(text=expand_query(" ".join(materials)), model=BM25_MODEL),
                             using=SPARSE, limit=prefetch, filter=flt)] if materials else []
    if mode == "vector":
        return qc.query_points(name, query=query_vector, using=DENSE, limit=top_k, query_filter=flt,
                               with_payload=True).points
    if mode == "bm25":
        if named:
            return qc.query_points(name, prefetch=[models.Prefetch(query=sparse_query, using=SPARSE, limit=prefetch,
                                                                   filter=flt), *named],
                                   query=models.FusionQuery(fusion=models.Fusion.RRF), limit=top_k,
                                   with_payload=True).points
        return qc.query_points(name, query=sparse_query, using=SPARSE, limit=top_k, query_filter=flt,
                               with_payload=True).points
    return qc.query_points(
        name,
        prefetch=[models.Prefetch(query=query_vector, using=DENSE, limit=prefetch, filter=flt),
                  models.Prefetch(query=sparse_query, using=SPARSE, limit=prefetch, filter=flt), *named],
        query=models.FusionQuery(fusion=models.Fusion.RRF), limit=top_k, with_payload=True,
    ).points


MAX_ASSET_BYTES = 25 * 1024 * 1024  # Cloudflare's limit per static asset


def split_pdf(src: str, dst: str, pages_per_part: int = 60) -> dict | None:
    """A PDF too large for one static asset, written as parts of whole pages next to ``dst`` (book.pdf →
    book.p0001-0060.pdf, …) with a manifest ``dst + ".parts.json"``: {"source_bytes", "pages", "parts": [[first,
    last, file name], …]} (pages 1-based). A part still over the limit is halved. Kept as it is when the manifest
    already describes the same source. None when a single page is over the limit."""
    import json

    import pypdfium2 as pdfium

    manifest_path = dst + ".parts.json"
    size = os.path.getsize(src)
    if os.path.exists(manifest_path):
        old = json.loads(open(manifest_path, encoding="utf-8").read())
        folder = os.path.dirname(dst)
        if old.get("source_bytes") == size and all(os.path.exists(os.path.join(folder, f)) for *_, f in old["parts"]):
            return old
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    doc = pdfium.PdfDocument(src)
    try:
        n, stem, parts = len(doc), os.path.basename(dst)[:-4], []

        def write(a: int, b: int) -> bool:  # pages a..b (1-based); False if one page alone is too large
            name = f"{stem}.p{a:04d}-{b:04d}.pdf"
            part = pdfium.PdfDocument.new()
            part.import_pages(doc, list(range(a - 1, b)))
            path = os.path.join(os.path.dirname(dst), name)
            part.save(path)
            part.close()
            if os.path.getsize(path) <= MAX_ASSET_BYTES:
                parts.append([a, b, name])
                return True
            os.remove(path)
            if a == b:
                return False
            m = (a + b) // 2
            return write(a, m) and write(m + 1, b)

        for a in range(1, n + 1, pages_per_part):
            if not write(a, min(a + pages_per_part - 1, n)):
                return None
    finally:
        doc.close()
    manifest = {"source_bytes": size, "pages": n, "parts": parts}
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)
    return manifest


def copy_pdfs(kb, root: str, dest: str) -> tuple[int, list[str]]:
    """Copy the PDF of every full-text paper in ``kb`` from ``root`` to ``dest`` (same relative paths),
    for the site's PDF Worker; a PDF over the asset limit goes in parts (split_pdf). Returns the number copied and
    the files skipped (missing, or with a single page over the limit)."""
    import shutil

    files = sorted({n.metadata.get("source_file") for n in kb.nodes()
                    if n.metadata.get("source_type") == "full_text_pdf" and n.metadata.get("source_file")})
    copied, skipped = 0, []
    for rel in files:
        src, dst = os.path.join(root, rel), os.path.join(dest, rel)
        if not os.path.isfile(src):
            skipped.append(rel)
            continue
        if os.path.getsize(src) > MAX_ASSET_BYTES:  # a long book: served in parts the site's viewer joins
            if split_pdf(src, dst) is None:
                skipped.append(rel)
            else:
                copied += 1
            continue
        if not (os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src)):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        copied += 1
    return copied, skipped


def paper_list(qc, name: str) -> list[dict]:
    """One row per paper in the collection (for the site's collection browser), from the chunks' payloads."""
    keys = ["doc_id", "citation", "reference", "year", "material", "category", "source_type", "doi"]
    papers: dict[str, dict] = {}
    offset = None
    while True:
        points, offset = qc.scroll(name, limit=2000, offset=offset, with_payload=keys, with_vectors=False)
        for pt in points:
            meta = pt.payload or {}
            doc = meta.get("doc_id")
            if not doc:
                continue
            row = papers.setdefault(doc, {k: meta.get(k) for k in keys} | {"chunks": 0})
            row["chunks"] += 1
            if meta.get("source_type") == "full_text_pdf":
                row["source_type"] = "full_text_pdf"
        if offset is None:
            break
    return sorted(papers.values(), key=lambda r: (-(r.get("year") or 0), r["doc_id"]))


def collection_name(settings: Settings) -> str:
    return settings.corpus
