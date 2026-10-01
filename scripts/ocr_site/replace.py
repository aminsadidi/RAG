"""Re-chunk the OCR'd papers with the pipeline's own chunker and embedding model, and replace their
points in the site's Qdrant collection when the OCR text is better than the old text."""
import json, os, re, sys
from pathlib import Path
from llama_index.core.schema import MetadataMode
from matrag import qdrant_store
from matrag.config import Settings
from matrag.index import make_embed_model
from matrag.ingest import cached_document, chunk_document, make_chunker

STOP = set("the of and in to is a for with by are was on that as from be this at an which were it we or".split())
NAME = "rag-optics"
dry = "--dry" in sys.argv


def quality(texts):
    words = [w for t in texts for w in re.findall(r"[A-Za-z]+", t)]
    return sum(map(len, texts)), (sum(w.lower() in STOP for w in words) / max(1, len(words)))


s = Settings(); qc = qdrant_store.client(); chunker = make_chunker(s); embed = None
report = json.load(open("report.json")) if os.path.exists("report.json") else {}
for path in sorted(Path("cache").glob("*.json.gz")):
    doc_id = path.name.removesuffix(".json.gz")
    if report.get(doc_id, {}).get("replaced"):
        continue
    old, _ = qc.scroll(NAME, limit=1000, with_payload=True, with_vectors=False,
                       scroll_filter={"must": [{"key": "doc_id", "match": {"value": doc_id}}]})
    old = [p.payload for p in old]
    full = [p for p in old if p.get("source_type") == "full_text_pdf"]
    if not full:
        report[doc_id] = {"skipped": "no full-text points on the site"}; continue
    ref = full[0]
    nodes = chunk_document(cached_document(Path("cache"), doc_id), doc_id=doc_id, chunker=chunker,
                           source_file=ref.get("source_file"),
                           extra={k: ref[k] for k in ("category", "material", "year", "doi") if k in ref})
    for n in nodes:
        n.metadata["citation"], n.metadata["reference"] = ref.get("citation"), ref.get("reference")
    oc, os_ = quality([p["text"] for p in full]); nc, ns = quality([n.get_content() for n in nodes])
    force = set(json.load(open("force.json"))) if os.path.exists("force.json") else set()
    better = nodes and (doc_id in force or (ns >= 0.15 and (nc > 1.05 * oc or ns > os_ + 0.02)))
    row = {"citation": ref.get("citation"), "old_chunks": len(full), "new_chunks": len(nodes),
           "old_chars": oc, "new_chars": nc, "old_stop": round(os_, 3), "new_stop": round(ns, 3), "better": bool(better)}
    if better and not dry:
        embed = embed or make_embed_model(s)
        texts = [n.get_content(metadata_mode=MetadataMode.EMBED) for n in nodes]
        vectors = embed.get_text_embedding_batch(texts, show_progress=False)
        points = list(qdrant_store.iter_points(nodes, {n.node_id: v for n, v in zip(nodes, vectors)}))
        if ref.get("drive_id"):
            for p in points:
                p.payload["drive_id"] = ref["drive_id"]
        for p in points:
            p.payload["ocr"] = True
        from qdrant_client import models
        qc.delete(NAME, points_selector=models.FilterSelector(filter=models.Filter(must=[
            models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id)),
            models.FieldCondition(key="source_type", match=models.MatchValue(value="full_text_pdf"))])), wait=True)
        for i in range(0, len(points), 64):
            qc.upsert(NAME, points=points[i:i + 64], wait=True)
        row["replaced"] = True
    report[doc_id] = row
    print(doc_id, row, flush=True)
    json.dump(report, open("report.json", "w"), indent=1)
