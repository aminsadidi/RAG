"""Add downloaded open-access papers to the site search without a Colab run (for a slow connection): each PDF is
converted (OCR if it has no text layer), chunked and embedded here with the pipeline's own converter, chunker and
model, and its points replace the paper's points on the site (an abstract it had there). The papers are added to
data/rag-optics/external_points.txt so export-qdrant leaves them alone; put the PDF in its category folder on Drive too,
for the page view after the next Colab run. Only doc_ids and counts are printed.

    python scripts/quality/add_papers.py PAPERS.json CACHE_DIR      (QDRANT_URL, QDRANT_API_KEY)

PAPERS.json: [{"pdf": "...", "doi": "10.1017/hpl.2015.7", "category": "02_Phosphates_Arsenates_KDP",
               "material": "KDP_DKDP_KH2PO4", "drive_id": "(optional)"}]
"""
import json
import sys
from pathlib import Path

from llama_index.core.schema import MetadataMode
from qdrant_client import models

from matrag import qdrant_store
from matrag.catalog import doi_key
from matrag.config import Settings
from matrag.index import make_embed_model
from matrag.ingest import chunk_document, convert, make_chunker, make_converter
from matrag.metadata import resolve
from matrag.new_papers import needs_ocr

NAME = "rag-optics"
EXTERNAL = Path(__file__).resolve().parents[2] / "data" / NAME / "external_points.txt"

papers, cache = json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2])
s = Settings()
qc, chunker, embed = qdrant_store.client(), make_chunker(s), make_embed_model(s)
converters = {}
added = []
for p in papers:
    pdf, doc_id = Path(p["pdf"]), doi_key(p["doi"])
    ocr = needs_ocr(pdf)
    if ocr not in converters:
        converters[ocr] = make_converter(s.model_copy(update={"force_ocr": True}) if ocr else s)
    doc = convert(pdf, converters[ocr], cache / ("docling_ocr" if ocr else "docling"), doc_id)
    paper = resolve(doc, doc_id, pdf.name, online=True, pdf_path=pdf)
    source_file = f"01_Papers_by_Category/{p['category']}/{p['material']}/{p['doi'].replace('/', '-')}.pdf"
    extra = {"category": p["category"], "material": p["material"], "doi": p["doi"], "year": str(paper.year or ""),
             **({"conversion": "ocr"} if ocr else {})}
    nodes = chunk_document(doc, doc_id=doc_id, chunker=chunker, paper=paper, source_file=source_file, extra=extra)
    vectors = embed.get_text_embedding_batch([n.get_content(metadata_mode=MetadataMode.EMBED) for n in nodes],
                                             show_progress=False)
    points = list(qdrant_store.iter_points(nodes, {n.node_id: v for n, v in zip(nodes, vectors)}))
    for pt in points:
        if p.get("drive_id"):
            pt.payload["drive_id"] = p["drive_id"]
        if ocr:
            pt.payload["ocr"] = True
    qc.delete(NAME, points_selector=models.FilterSelector(filter=models.Filter(must=[
        models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))])), wait=True)
    for i in range(0, len(points), 64):
        qc.upsert(NAME, points=points[i:i + 64], wait=True)
    added.append(doc_id)
    print(f"{doc_id}: {len(doc.pages)} pages, {len(points)} chunks{' (OCR)' if ocr else ''}, {paper.short_citation()}",
          flush=True)

known = set(EXTERNAL.read_text("utf-8").split()) if EXTERNAL.exists() else set()
with open(EXTERNAL, "a", encoding="utf-8") as f:
    f.write("".join(f"{d}\n" for d in added if d not in known))
