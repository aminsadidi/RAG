"""Papers whose PDF holds a different paper: drop the wrong full text from the site and index the
paper from its master-index entry (abstract), as the pipeline does for papers without a PDF."""
import json, re
from llama_index.core.schema import MetadataMode
from qdrant_client import models
from matrag import qdrant_store
from matrag.catalog import CatalogEntry, _normalise, doi_key
from matrag.config import Settings
from matrag.index import make_embed_model
from matrag.ingest import summary_node

WRONG = ["10.1016_j.infrared.2020.103571", "10.1016_j.optmat.2020.110648", "10.1143_jjap.45.5795",
         "10.1143_jjap.25.1397", "10.1070_qe1975v005n02abeh010943", "10.1515_nanoph_2020_0112"]
entries = {}
for line in open("master.jsonl"):
    e = CatalogEntry(**_normalise(json.loads(line)))
    entries[e.key] = e
qc = qdrant_store.client(); embed = make_embed_model(Settings())
for d in WRONG:
    e = entries[d]
    kind = "abstract" if e.abstract else "metadata_only"
    node = summary_node(d, e.summary_text(), e.paper_info(d), kind,
                        extra={"category": e.category, "material": e.material, "year": e.year or -1, "doi": e.doi})
    vec = embed.get_text_embedding(node.get_content(metadata_mode=MetadataMode.EMBED))
    [pt] = qdrant_store.iter_points([node], {node.node_id: vec})
    pt.payload["pdf_mismatch"] = True  # the PDF in the collection is another paper
    qc.delete("rag-optics", points_selector=models.FilterSelector(filter=models.Filter(must=[
        models.FieldCondition(key="doc_id", match=models.MatchValue(value=d))])), wait=True)
    qc.upsert("rag-optics", points=[pt], wait=True)
    print(d, kind, node.metadata["citation"], "|", e.title[:70])
