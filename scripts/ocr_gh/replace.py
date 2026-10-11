"""Join each paper's converted units, re-chunk and embed it with the pipeline's own chunker and model, and
replace its full-text points on the site when the new text is better. Replaced papers are added to
data/rag-optics/external_points.txt (export-qdrant then leaves them alone); report.json gets the numbers.

usage: replace.py [--dry]
"""
import json
import sys
from pathlib import Path

from docling_core.types.doc import DoclingDocument, Size
from llama_index.core.schema import MetadataMode
from qdrant_client import models

from common import DATA, NAME, full_text_points, listed, quality
from matrag import qdrant_store
from matrag.config import Settings
from matrag.index import make_embed_model
from matrag.ingest import cached_document, chunk_document, make_chunker

dry = "--dry" in sys.argv
plan = json.load(open("plan.json"))
s = Settings()
qc, chunker, embed = qdrant_store.client(), make_chunker(s), None
report = {}
for doc_id, paper in sorted(plan["papers"].items()):
    parts = []
    for u in sorted((u for u in plan["units"] if u["doc_id"] == doc_id), key=lambda u: u["start"]):
        part = cached_document(Path("units") / doc_id, f"{u['start']:05d}-{u['end']:05d}")
        if part is None:
            break
        # concatenate() numbers a part's pages on from the previous part's last page: an empty page
        # Docling left out would shift every later page number, so missing pages are put back.
        for n in set(range(u["start"], u["end"] + 1)) - set(part.pages):
            part.add_page(page_no=n, size=Size(width=1, height=1))
        parts.append(part)
    if not parts or len(parts) != sum(u["doc_id"] == doc_id for u in plan["units"]):
        report[doc_id] = {"skipped": "units missing (a shard failed)"}
        print(doc_id, report[doc_id], flush=True)
        continue
    doc = DoclingDocument.concatenate(parts)
    old = full_text_points(qc, doc_id)
    ref = old[0].payload if old else {}
    nodes = chunk_document(doc, doc_id=doc_id, chunker=chunker, source_file=ref.get("source_file") or paper["source_file"],
                           extra={k: ref[k] for k in ("category", "material", "year", "doi") if k in ref})
    for n in nodes:
        n.metadata["citation"], n.metadata["reference"] = ref.get("citation"), ref.get("reference")
    oc, os_ = quality([p.payload.get("text", "") for p in old])
    nc, ns = quality([n.get_content() for n in nodes])
    # OCR'd text must read as prose and hold more of the paper (or read better). A full conversion keeps the
    # PDF's own text, so it only has to hold more and not be garbled: its later pages (reference lists, data
    # tables) have fewer common words than the first 60, which is no sign of worse text.
    if paper["mode"] == "ocr":
        better = ns >= 0.15 and (nc > 1.05 * oc or ns > os_ + 0.02)
    else:
        better = nc > 1.05 * oc and ns >= 0.1
    better = bool(nodes) and better
    row = {"mode": paper["mode"], "pages": paper["pages"], "old_chunks": len(old), "new_chunks": len(nodes),
           "old_chars": oc, "new_chars": nc, "old_stop": round(os_, 3), "new_stop": round(ns, 3), "better": better}
    if better and not dry:
        if not ref:
            row["skipped"] = "no full-text points on the site to take the metadata from"
        else:
            embed = embed or make_embed_model(s)
            texts = [n.get_content(metadata_mode=MetadataMode.EMBED) for n in nodes]
            vectors = embed.get_text_embedding_batch(texts, show_progress=False)
            points = list(qdrant_store.iter_points(nodes, {n.node_id: v for n, v in zip(nodes, vectors)}))
            for p in points:
                if ref.get("drive_id"):
                    p.payload["drive_id"] = ref["drive_id"]
                if paper["mode"] == "ocr":
                    p.payload["ocr"] = True
            qc.delete(NAME, points_selector=models.FilterSelector(filter=models.Filter(must=[
                models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id)),
                models.FieldCondition(key="source_type", match=models.MatchValue(value="full_text_pdf"))])), wait=True)
            for i in range(0, len(points), 64):
                qc.upsert(NAME, points=points[i:i + 64], wait=True)
            row["replaced"] = True
    report[doc_id] = row
    print(doc_id, row, flush=True)

json.dump(report, open("report.json", "w"), indent=1)
replaced = sorted(k for k, r in report.items() if r.get("replaced"))
new = [k for k in replaced if k not in listed("external_points")]
if new:
    with open(DATA / "external_points.txt", "a", encoding="utf-8") as f:
        f.write("".join(f"{k}\n" for k in new))
print(f"{len(replaced)} of {len(report)} papers replaced", flush=True)
