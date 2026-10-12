"""Join the OCR'd parts of the Dmitriev handbook (units/NNNNN-MMMMM.json.gz, global page numbers in the name,
part-relative inside), leave missing ranges as empty pages so page numbers stay right, re-chunk, embed and
replace the book's full-text points on the site."""
import sys
from pathlib import Path
sys.path.insert(0, "/home/user/RAG/scripts/ocr_gh")
from docling_core.types.doc import DoclingDocument, Size
from llama_index.core.schema import MetadataMode
from qdrant_client import models
from common import NAME, full_text_points, quality
from matrag import qdrant_store
from matrag.config import Settings
from matrag.index import make_embed_model
from matrag.ingest import cached_document, chunk_document, make_chunker

DOC, PAGES = "10.1007_978_3_540_46793_9", 426
units = Path(sys.argv[1])
have = {}
for f in units.glob("*.json.gz"):
    a, b = map(int, f.name[:-8].split("-"))
    have[a] = (b, f.name[:-8])
parts, page = [], 1
while page <= PAGES:
    if page in have:
        end, name = have[page]
        part = cached_document(units, name)
        assert len(part.pages) == end - page + 1, (name, len(part.pages))
    else:
        end = min(p for p in [*have, PAGES + 1] if p > page) - 1
        part = DoclingDocument(name="gap")
        for n in range(1, end - page + 2):
            part.add_page(page_no=n, size=Size(width=1, height=1))
        print(f"pages {page}-{end} missing: left empty")
    parts.append(part)
    page = end + 1
doc = DoclingDocument.concatenate(parts)
assert sorted(doc.pages) == list(range(1, PAGES + 1))
s = Settings()
qc = qdrant_store.client()
old = full_text_points(qc, DOC)
ref = old[0].payload
nodes = chunk_document(doc, doc_id=DOC, chunker=make_chunker(s), source_file=ref.get("source_file"),
                       extra={k: ref[k] for k in ("category", "material", "year", "doi") if k in ref})
for n in nodes:
    n.metadata["citation"], n.metadata["reference"] = ref.get("citation"), ref.get("reference")
oc, os_ = quality([p.payload.get("text", "") for p in old]); nc, ns = quality([n.get_content() for n in nodes])
print(f"old: {len(old)} chunks, {oc} chars, stop {os_:.3f}; new: {len(nodes)} chunks, {nc} chars, stop {ns:.3f}")
if "--dry" in sys.argv or not (nc > oc and ns >= 0.12):  # a handbook of data tables: 150-195 tables per 80 pages
    sys.exit("not replaced")
embed = make_embed_model(s)
vectors = embed.get_text_embedding_batch([n.get_content(metadata_mode=MetadataMode.EMBED) for n in nodes], show_progress=False)
points = list(qdrant_store.iter_points(nodes, {n.node_id: v for n, v in zip(nodes, vectors)}))
for p in points:
    p.payload["ocr"] = True
    if ref.get("drive_id"):
        p.payload["drive_id"] = ref["drive_id"]
qc.delete(NAME, points_selector=models.FilterSelector(filter=models.Filter(must=[
    models.FieldCondition(key="doc_id", match=models.MatchValue(value=DOC)),
    models.FieldCondition(key="source_type", match=models.MatchValue(value="full_text_pdf"))])), wait=True)
for i in range(0, len(points), 64):
    qc.upsert(NAME, points=points[i:i + 64], wait=True)
print(f"replaced: {len(points)} points")
