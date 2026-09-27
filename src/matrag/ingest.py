"""Stage 1: turn papers into retrievable chunks.

PDF --(Docling)--> DoclingDocument --(HybridChunker)--> LlamaIndex TextNodes

Docling keeps the document structure (sections, tables, captions), and its
HybridChunker splits along that structure while respecting the embedding
model's token limit. Tables are kept whole where possible and their header
row is repeated in every piece, which matters because most property values
in papers are reported in tables.
"""

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
INGEST_VERSION = 3


def make_converter(settings: Settings) -> DocumentConverter:
    pdf_options = PdfPipelineOptions(do_ocr=settings.do_ocr, do_table_structure=True)
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


def convert(path: Path, converter: DocumentConverter, cache_dir: Path) -> DoclingDocument:
    """Convert a paper, caching the result as JSON.

    Conversion is the slowest step on a laptop CPU, so each paper is
    converted only once.
    """
    cache_file = cache_dir / f"{path.stem}.json"
    if cache_file.exists():
        return DoclingDocument.load_from_json(cache_file)
    doc = converter.convert(path).document
    cache_dir.mkdir(parents=True, exist_ok=True)
    doc.save_as_json(cache_file)
    return doc


def chunk_document(
    doc: DoclingDocument, doc_id: str, chunker: HybridChunker, paper: PaperInfo | None = None
) -> list[TextNode]:
    """Split a document into nodes carrying provenance metadata.

    Node ids are deterministic (``<doc_id>::<n>``) so evaluation sets can
    refer to exact chunks across rebuilds.
    """
    nodes = []
    for i, chunk in enumerate(chunker.chunk(dl_doc=doc)):
        items = chunk.meta.doc_items
        pages = sorted({prov.page_no for item in items for prov in item.prov})
        has_table = any(item.label == DocItemLabel.TABLE for item in items)
        metadata = {
            "doc_id": doc_id,
            "source_file": doc.origin.filename if doc.origin else doc_id,
            "headings": clean_text(" > ".join(chunk.meta.headings or [])),
            "pages": ",".join(map(str, pages)),
            "first_page": pages[0] if pages else -1,
            "content_type": "table" if has_table else "text",
            "ingest_version": INGEST_VERSION,
            # Bibliographic labels, e.g. "Tan et al. (2019)" and the full reference.
            "citation": paper.short_citation() if paper else doc_id,
            "reference": paper.reference() if paper else doc_id,
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


def find_papers(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in SUPPORTED_SUFFIXES)
