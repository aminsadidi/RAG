"""Stage 1: turn papers into retrievable chunks.

PDF --(Docling)--> DoclingDocument --(HybridChunker)--> LlamaIndex TextNodes

Docling keeps the document structure (sections, tables, captions), and its
HybridChunker splits along that structure while respecting the embedding
model's token limit. Tables are kept whole where possible and their header
row is repeated in every piece, which matters because most property values
in papers are reported in tables.
"""

import gzip
import json
import os
import sys
from pathlib import Path

from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.transforms.chunker.tokenizer.base import BaseTokenizer
from docling_core.types.doc import DocItemLabel, DoclingDocument
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode

from matrag.config import Settings
from matrag.metadata import PaperInfo
from matrag.textfix import clean_text

SUPPORTED_SUFFIXES = {".pdf", ".md", ".html", ".docx"}

# Bump when chunking or text cleaning changes: papers indexed with an older
# version are re-indexed automatically on the next ingest.
INGEST_VERSION = 4


def make_converter(settings: Settings) -> DocumentConverter:
    pdf_options = PdfPipelineOptions(do_ocr=settings.do_ocr, do_table_structure=True,
                                     do_formula_enrichment=settings.do_formula_enrichment,
                                     document_timeout=settings.convert_timeout_s)
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)}
    )


def make_chunker(settings: Settings, tokenizer: BaseTokenizer | None = None) -> HybridChunker:
    """Chunker whose token budget matches the embedding model."""
    if tokenizer is None:
        from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer

        # Keep a margin: the embedding model adds special tokens, and chunks
        # measured by Docling can come out a few tokens longer once serialized.
        tokenizer = HuggingFaceTokenizer.from_pretrained(
            model_name=settings.embed_model, max_tokens=settings.chunk_max_tokens - 32
        )
    return HybridChunker(tokenizer=tokenizer, merge_peers=True)


def cached_document(cache_dir: Path, name: str) -> DoclingDocument | None:
    """A cached conversion (compressed, or plain JSON from older versions), if there is one."""
    packed = cache_dir / f"{name}.json.gz"
    if packed.exists():
        with gzip.open(packed, "rt", encoding="utf-8") as f:
            return DoclingDocument.model_validate_json(f.read())
    plain = cache_dir / f"{name}.json"
    return DoclingDocument.load_from_json(plain) if plain.exists() else None


def is_cached(cache_dir: Path, name: str) -> bool:
    return (cache_dir / f"{name}.json.gz").exists() or (cache_dir / f"{name}.json").exists()


def cached_names(cache_dir: Path) -> set[str]:
    """Names of all cached conversions, from one folder listing (fast on a network drive)."""
    if not cache_dir.exists():
        return set()
    names = set()
    for f in os.listdir(cache_dir):
        if f.startswith("."):
            continue  # unfinished temporary files
        if f.endswith(".json.gz"):
            names.add(f[: -len(".json.gz")])
        elif f.endswith(".json"):
            names.add(f[: -len(".json")])
    return names


def convert(path: Path, converter: DocumentConverter, cache_dir: Path, name: str | None = None,
            max_pages: int | None = None) -> DoclingDocument:
    """Convert a paper, caching the result as compressed JSON under ``name`` (default: file name).

    Conversion is the slowest step, so each paper is converted only once. The
    cache file is written in one step (via a temporary file), so a conversion
    interrupted by a disconnect is never mistaken for a finished one; this also
    lets several workers fill the same cache folder in parallel.
    """
    name = name or path.stem
    doc = cached_document(cache_dir, name)
    if doc is not None:
        return doc
    page_range = (1, max_pages) if max_pages else (1, sys.maxsize)
    doc = converter.convert(path, page_range=page_range).document
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / f"{name}.json.gz"
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(doc.export_to_dict(), f)
    os.replace(tmp, target)
    return doc


def chunk_document(
    doc: DoclingDocument, doc_id: str, chunker: HybridChunker, paper: PaperInfo | None = None,
    source_file: str | None = None, extra: dict | None = None,
) -> list[TextNode]:
    """Split a document into nodes carrying provenance metadata.

    Node ids are deterministic (``<doc_id>::<n>``) so evaluation sets can
    refer to exact chunks across rebuilds. ``source_file`` is the PDF's path
    relative to the corpus folder (default: its file name); ``extra`` holds
    more metadata, e.g. the paper's category in a collection.
    """
    nodes = []
    for i, chunk in enumerate(chunker.chunk(dl_doc=doc)):
        items = chunk.meta.doc_items
        pages = sorted({prov.page_no for item in items for prov in item.prov})
        has_table = any(item.label == DocItemLabel.TABLE for item in items)
        metadata = {
            "doc_id": doc_id,
            # Where the chunk sits on its pages, for highlighting the source in the PDF.
            "boxes": json.dumps(chunk_boxes(doc, items)),
            "source_file": source_file or (doc.origin.filename if doc.origin else doc_id),
            "source_type": "full_text_pdf",
            "headings": clean_text(" > ".join(chunk.meta.headings or [])),
            "pages": ",".join(map(str, pages)),
            "first_page": pages[0] if pages else -1,
            "content_type": "table" if has_table else "text",
            "ingest_version": INGEST_VERSION,
            # Bibliographic labels, e.g. "Tan et al. (2019)" and the full reference.
            "citation": paper.short_citation() if paper else doc_id,
            "reference": paper.reference() if paper else doc_id,
            **(extra or {}),
        }
        node = TextNode(
            id_=f"{doc_id}::{i}",
            # contextualize() prepends the section headings, which gives the
            # embedding model the context a bare table row would lack.
            text=clean_text(chunker.contextualize(chunk=chunk)),
            metadata=metadata,
            # The text already carries the headings; don't add metadata twice.
            excluded_embed_metadata_keys=list(metadata),
            excluded_llm_metadata_keys=list(metadata),
        )
        node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=doc_id)
        nodes.append(node)
    return nodes


# --- parallel chunking -----------------------------------------------------------
# Chunking (tokenizing every piece of text) is CPU-bound and runs one paper at a time;
# with papers already converted, it is what an ingest waits for. Worker processes
# chunk several papers at once while the main process embeds the finished ones on the
# GPU. The chunks are exactly those of the sequential path: same chunker, same code.

_worker_chunker: HybridChunker | None = None


def init_chunk_worker(settings: Settings) -> None:
    global _worker_chunker
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")  # one thread per process
    _worker_chunker = make_chunker(settings)


def chunk_cached(job: dict) -> tuple[str, list[TextNode], PaperInfo]:
    """Chunk one converted paper in a worker process (see ``init_chunk_worker``).

    ``job`` holds the paper's doc_id, cache folder, known metadata (or None, then it
    is resolved here from the document), relative source file and extra metadata.
    """
    from matrag.metadata import resolve

    doc = cached_document(job["cache_dir"], job["doc_id"])
    if doc is None:
        raise FileNotFoundError(f"No cached conversion for {job['doc_id']}")
    paper = job["paper"] or resolve(doc, job["doc_id"], job["pdf"].name, online=job["online"], pdf_path=job["pdf"])
    nodes = chunk_document(doc, doc_id=job["doc_id"], chunker=_worker_chunker, paper=paper,
                           source_file=job["source_file"], extra=job["extra"])
    return job["doc_id"], nodes, paper


def summary_node(doc_id: str, text: str, paper: PaperInfo, source_type: str,
                 extra: dict | None = None) -> TextNode:
    """A single node for a paper known only from its index entry (abstract, or just its title).

    It lets the paper be found and cited as a lead, while ``source_type`` makes
    clear that no full text stood behind it.
    """
    metadata = {
        "doc_id": doc_id, "boxes": "[]", "source_file": "", "source_type": source_type,
        "headings": "Abstract" if source_type == "abstract" else "",
        "pages": "", "first_page": -1,
        "content_type": source_type,  # "abstract" or "metadata_only"
        "ingest_version": INGEST_VERSION,
        "citation": paper.short_citation(), "reference": paper.reference(),
        **(extra or {}),
    }
    node = TextNode(id_=f"{doc_id}::0", text=clean_text(text), metadata=metadata,
                    excluded_embed_metadata_keys=list(metadata), excluded_llm_metadata_keys=list(metadata))
    node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=doc_id)
    return node


def chunk_boxes(doc: DoclingDocument, items) -> list[list[float]]:
    """[[page, x0, y0, x1, y1], ...] with coordinates as fractions of the page size,
    measured from the top-left corner (independent of the rendering resolution)."""
    boxes = []
    for item in items:
        for prov in item.prov:
            page = doc.pages.get(prov.page_no)
            if page is None or not page.size.width or not page.size.height:
                continue
            w, h = page.size.width, page.size.height
            box = prov.bbox.to_top_left_origin(page_height=h)
            boxes.append([prov.page_no, *(round(v, 4) for v in (box.l / w, box.t / h, box.r / w, box.b / h))])
    return boxes


def find_papers(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in SUPPORTED_SUFFIXES)
