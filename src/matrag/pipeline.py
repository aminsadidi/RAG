"""High-level operations on one corpus, shared by the CLI and the web app.

A ``Workspace`` bundles a corpus's folders, knowledge base and paper
library, and exposes the whole pipeline as plain method calls:
add papers -> ingest -> ask / pack / extract.
"""

import re
import shutil
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cache, cached_property
from pathlib import Path

from llama_index.core.llms import LLM

from matrag.config import Settings, get_settings
from matrag.index import KnowledgeBase, make_embed_model
from matrag.metadata import Library, PaperInfo, resolve
from matrag.qa import Answer, answer_with_rag, answer_without_rag, build_context_pack
from matrag.retrieve import RetrievalMode, make_retriever
from matrag.schema import ExtractedRecord


@cache
def _embed_model(name: str, query_instruction: str, max_length: int):
    # Loading the embedding model takes seconds; share it across corpora.
    return make_embed_model(
        Settings(embed_model=name, embed_query_instruction=query_instruction,
                 chunk_max_tokens=max_length, _env_file=None)
    )


def list_corpora(settings: Settings | None = None) -> list[str]:
    settings = settings or get_settings()
    if not settings.data_dir.exists():
        return []
    return sorted(p.name for p in settings.data_dir.iterdir() if (p / "pdfs").is_dir())


@dataclass
class IngestResult:
    file: str
    citation: str
    chunks: int
    skipped: bool = False
    error: str | None = None


class Workspace:
    def __init__(self, settings: Settings | None = None, corpus: str | None = None):
        settings = settings or get_settings()
        if corpus:
            settings = settings.model_copy(update={"corpus": corpus})
        self.settings = settings
        settings.raw_pdf_dir.mkdir(parents=True, exist_ok=True)

    # --- components (created on first use) ---

    @cached_property
    def kb(self) -> KnowledgeBase:
        s = self.settings
        return KnowledgeBase(s, _embed_model(s.embed_model, s.embed_query_instruction, s.chunk_max_tokens))

    @property
    def library(self) -> Library:
        return Library(self.settings.library_path)  # re-read: it may be edited by hand

    def llm(self, provider: str | None = None) -> LLM:
        from matrag.llm import make_llm

        return make_llm(self._settings_for(provider))

    def llm_name(self, provider: str | None = None) -> str:
        return self._settings_for(provider).llm_name

    def _settings_for(self, provider: str | None) -> Settings:
        if provider and provider != self.settings.llm_provider:
            return self.settings.model_copy(update={"llm_provider": provider})
        return self.settings

    # --- papers ---

    def add_files(self, files: list[Path]) -> list[Path]:
        """Copy papers into the corpus folder; returns their new paths."""
        added = []
        for f in files:
            target = self.settings.raw_pdf_dir / _safe_name(Path(f).name)
            if Path(f).resolve() != target.resolve():
                shutil.copyfile(f, target)
            added.append(target)
        return added

    def download_arxiv(self, arxiv_id: str) -> Path:
        arxiv_id = arxiv_id.strip().removeprefix("arXiv:").removeprefix("arxiv:")
        target = self.settings.raw_pdf_dir / f"arxiv_{arxiv_id}.pdf"
        if not target.exists():
            request = urllib.request.Request(f"https://arxiv.org/pdf/{arxiv_id}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=120) as response:
                data = response.read()
            if not data.startswith(b"%PDF"):
                raise ValueError(f"arXiv did not return a PDF for {arxiv_id}")
            target.write_bytes(data)
        return target

    def ingest(
        self,
        paths: list[Path] | None = None,
        force: bool = False,
        on_progress: Callable[[int, int, str], None] | None = None,
    ) -> list[IngestResult]:
        """Convert, chunk and index papers (default: every paper in the corpus folder)."""
        from matrag.ingest import INGEST_VERSION, chunk_document, convert, find_papers, make_chunker, make_converter

        s = self.settings
        paths = paths or find_papers(s.raw_pdf_dir)
        library, versions = self.library, self.kb.doc_versions()
        converter = chunker = None
        results = []
        for i, path in enumerate(paths):
            if on_progress:
                on_progress(i, len(paths), path.name)
            doc_id = path.stem
            if versions.get(doc_id) == INGEST_VERSION and not force:
                results.append(IngestResult(path.name, library.get(doc_id).short_citation(), 0, skipped=True))
                continue
            try:
                if converter is None:  # Docling models load lazily, only if needed
                    converter, chunker = make_converter(s), make_chunker(s)
                doc = convert(path, converter, s.processed_dir)
                # Metadata is looked up once; later edits to papers.json are kept.
                paper = library.papers.get(doc_id)
                if paper is None:
                    paper = resolve(doc, doc_id, path.name, online=s.fetch_metadata, pdf_path=path)
                    library.put(paper)
                nodes = chunk_document(doc, doc_id=doc_id, chunker=chunker, paper=paper)
                self.kb.add_document(doc_id, nodes)
                results.append(IngestResult(path.name, paper.short_citation(), len(nodes)))
            except Exception as e:  # one broken PDF must not stop the batch
                results.append(IngestResult(path.name, doc_id, 0, error=f"{type(e).__name__}: {e}"))
        if on_progress:
            on_progress(len(paths), len(paths), "done")
        if any(not r.skipped and not r.error for r in results):
            self.backup()
        return results

    def backup(self) -> None:
        """Mirror the corpus database to ``storage_backup_dir``, if configured."""
        backup_dir = self.settings.storage_backup_dir
        source = self.settings.docstore_path.parent
        if backup_dir and source.exists():
            shutil.copytree(source, Path(backup_dir) / self.settings.corpus, dirs_exist_ok=True)

    def papers(self) -> list[tuple[PaperInfo, int]]:
        """Indexed papers with their chunk counts."""
        library = self.library
        counts: dict[str, int] = {}
        for node in self.kb.nodes():
            counts[node.metadata["doc_id"]] = counts.get(node.metadata["doc_id"], 0) + 1
        return [(library.get(doc_id), n) for doc_id, n in sorted(counts.items())]

    def remove_paper(self, doc_id: str) -> None:
        """Remove a paper from the database, the library and the corpus folder."""
        self.kb.remove_document(doc_id)
        self.library.remove(doc_id)
        for f in [*self.settings.raw_pdf_dir.glob(f"{doc_id}.*"), self.settings.processed_dir / f"{doc_id}.json"]:
            f.unlink(missing_ok=True)
        self.backup()

    # --- using the knowledge base ---

    def retriever(self, mode: RetrievalMode = RetrievalMode.hybrid, top_k: int | None = None,
                  doc_ids: list[str] | None = None):
        return make_retriever(self.kb, mode, top_k or self.settings.top_k, doc_ids or None)

    def ask(self, question: str, provider: str | None = None, mode: RetrievalMode = RetrievalMode.hybrid,
            top_k: int | None = None, doc_ids: list[str] | None = None, language: str | None = None) -> Answer:
        return answer_with_rag(question, self.retriever(mode, top_k, doc_ids), self.llm(provider), language)

    def ask_without_rag(self, question: str, provider: str | None = None, language: str | None = None) -> Answer:
        return answer_without_rag(question, self.llm(provider), language)

    def pack(self, question: str, language: str | None = None, mode: RetrievalMode = RetrievalMode.hybrid,
             top_k: int | None = None, doc_ids: list[str] | None = None) -> str:
        k = top_k or self.settings.top_k
        nodes = self.retriever(mode, k, doc_ids).retrieve(question)
        about = {
            "question": question,
            "corpus": self.settings.corpus,
            "retrieval": f"{mode.value}, top {k}",
            "embedding model": self.settings.embed_model,
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
        return build_context_pack(question, nodes, about, language)

    def extract(self, properties: list[str], provider: str | None = None, exhaustive: bool = False,
                mode: RetrievalMode = RetrievalMode.hybrid, top_k: int | None = None,
                doc_ids: list[str] | None = None) -> list[ExtractedRecord]:
        from matrag.extract import extract

        s = self._settings_for(provider)
        llm = self.llm(provider)
        if exhaustive:
            records = extract(properties, llm, nodes=self.kb.nodes(doc_ids or None), min_interval_s=s.llm_min_interval_s)
        else:
            records = extract(properties, llm, retriever=self.retriever(mode, top_k, doc_ids),
                              min_interval_s=s.llm_min_interval_s)
        for r in records:
            r.llm = s.llm_name
        return records


def _safe_name(name: str) -> str:
    """File names become doc ids: keep them short and filesystem/URL friendly."""
    stem, suffix = Path(name).stem, Path(name).suffix.lower()
    stem = re.sub(r"[^\w.-]+", "_", stem).strip("_")[:80] or "paper"
    return stem + suffix


def slugify(text: str, length: int = 60) -> str:
    return re.sub(r"[^\w]+", "_", text.lower()).strip("_")[:length]
