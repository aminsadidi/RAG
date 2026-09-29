"""High-level operations on one corpus, shared by the CLI and the web app.

A ``Workspace`` bundles a corpus's folders, knowledge base and paper
library, and exposes the whole pipeline as plain method calls:
add papers -> ingest -> ask / pack / extract.
"""

import json
import re
import shutil
import time
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
from matrag.qa import Answer, answer_with_rag, answer_without_rag, build_context_pack, is_persian, translate_query
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
    return sorted(p.name for p in settings.data_dir.iterdir()
                  if (p / "pdfs").is_dir() or (p / "corpus_root.txt").exists())


def link_collection(corpus: str, folder: Path, settings: Settings | None = None) -> Path:
    """Make ``corpus`` read its papers from an external folder (e.g. RAG-Optics on Drive)."""
    settings = settings or get_settings()
    folder = Path(folder).expanduser().resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")
    link = settings.data_dir / corpus / "corpus_root.txt"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.write_text(str(folder), "utf-8")
    return link


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
        self._translations: dict[str, str] = {}

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
        for f in map(Path, files):
            name = Path(_safe_name(f.name))
            target = self.settings.raw_pdf_dir / name
            if f.resolve() != target.resolve():
                # A different paper under an existing name gets a new name (paper_2.pdf, ...)
                # instead of silently replacing the indexed one.
                n = 2
                while target.exists() and not _same_file(f, target):
                    target = target.with_name(f"{name.stem}_{n}{name.suffix}")
                    n += 1
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

    def plan(self):
        """What to index: every PDF, plus (in a linked collection) every index entry without one."""
        from matrag.catalog import Item, plan
        from matrag.ingest import find_papers

        if self.settings.corpus_root:
            return plan(self.settings.corpus_root)
        from matrag.catalog import Plan

        return Plan([Item(p.stem, p, None) for p in find_papers(self.settings.raw_pdf_dir)], [])

    def ingest(
        self,
        paths: list[Path] | None = None,
        force: bool = False,
        on_progress: Callable[[int, int, str], None] | None = None,
        prune: bool = False,
    ) -> list[IngestResult]:
        """Convert, chunk and index papers (default: every paper of the corpus).

        Papers already indexed from the same kind of source are skipped. In a
        linked collection, papers without a PDF are indexed from their abstract,
        and replaced by their full text once a PDF appears. ``prune`` removes
        papers that are no longer in the corpus.
        """
        from matrag.catalog import FULL_TEXT, Item
        from matrag.ingest import INGEST_VERSION, chunk_document, convert, make_chunker, make_converter, summary_node

        s = self.settings
        if paths:
            items = [Item(p.stem, p, None) for p in paths]
        else:
            items = self.plan().items
        library, versions, sources = self.library, self.kb.doc_versions(), self.kb.doc_source_types()
        files = self.kb.doc_source_files()
        converter = chunker = None
        results: list[IngestResult] = []
        pending: dict[str, list] = {}  # summary nodes, embedded in batches
        last_save = time.monotonic()

        def flush(final: bool = False):
            nonlocal last_save
            if pending:
                self.kb.add_documents(dict(pending), persist=False)
                pending.clear()
            # Save regularly, so a Colab disconnect loses at most a few minutes of work.
            if final or time.monotonic() - last_save > 600:
                self.kb.persist()
                library.save()
                if not final:
                    self.backup()
                last_save = time.monotonic()

        for i, item in enumerate(items):
            name = self._display_name(item)
            if on_progress:
                on_progress(i, len(items), name)
            # A PDF moved to another folder is re-chunked from its cached conversion,
            # so the source viewer finds it again.
            up_to_date = (versions.get(item.doc_id) == INGEST_VERSION
                          and sources.get(item.doc_id, FULL_TEXT) == item.source_type
                          and (item.pdf is None or files.get(item.doc_id) in (self._relative(item.pdf), item.pdf.name)))
            if up_to_date and not force:
                results.append(IngestResult(name, library.get(item.doc_id).short_citation(), 0, skipped=True))
                continue
            try:
                extra = self._extra_metadata(item)
                if item.pdf is None:
                    paper = item.entry.paper_info(item.doc_id)
                    library.put(paper, save=False)
                    pending[item.doc_id] = [summary_node(item.doc_id, item.entry.summary_text(), paper,
                                                         item.source_type, extra)]
                    if len(pending) >= 256:
                        flush()
                    results.append(IngestResult(name, paper.short_citation(), 1))
                    continue
                if converter is None:  # Docling models load lazily, only if needed
                    converter, chunker = make_converter(s), make_chunker(s)
                doc = convert(item.pdf, converter, s.processed_dir, item.doc_id, s.max_pages)
                # Metadata is looked up once; later edits to papers.json are kept.
                paper = library.papers.get(item.doc_id)
                if paper is None or (item.entry and paper.source != "catalog"):
                    paper = (item.entry.paper_info(item.doc_id) if item.entry else
                             resolve(doc, item.doc_id, item.pdf.name, online=s.fetch_metadata, pdf_path=item.pdf))
                    library.put(paper, save=False)
                nodes = chunk_document(doc, doc_id=item.doc_id, chunker=chunker, paper=paper,
                                       source_file=self._relative(item.pdf), extra=extra)
                self.kb.add_document(item.doc_id, nodes, persist=False)
                results.append(IngestResult(name, paper.short_citation(), len(nodes)))
                flush()
            except Exception as e:  # one broken PDF must not stop the batch
                results.append(IngestResult(name, item.doc_id, 0, error=f"{type(e).__name__}: {e}"))
        if prune and not paths:
            wanted = {item.doc_id for item in items}
            for doc_id in set(versions) - wanted:
                self.kb.remove_document(doc_id, persist=False)
                results.append(IngestResult(doc_id, doc_id, 0, skipped=True, error="removed: no longer in the corpus"))
        flush(final=True)
        if on_progress:
            on_progress(len(items), len(items), "done")
        if any(not r.skipped for r in results) or prune:
            self.backup()
        return results

    def convert_shard(self, shard: int, shards: int, retry_failed: bool = False,
                      on_progress: Callable[[int, int, str], None] | None = None) -> dict[str, int]:
        """Convert this worker's share of the PDFs (no database, no LLM).

        Several Colab sessions can run this at once with different ``shard``
        numbers: each paper belongs to exactly one shard, and every conversion
        lands in the shared cache folder, where ``ingest`` picks it up. Stopping
        and re-running is safe: finished papers are skipped. Papers that failed
        are recorded in ``_status/`` and skipped unless ``retry_failed``.
        """
        from matrag.catalog import shard_of
        from matrag.ingest import cached_names, convert, make_converter

        s = self.settings
        if not 0 <= shard < shards:
            raise ValueError(f"shard must be between 0 and {shards - 1}")
        status_dir = s.processed_dir / "_status"
        status_dir.mkdir(parents=True, exist_ok=True)
        failed = set() if retry_failed else _failed_ids(status_dir)
        mine = [it for it in self.plan().items if it.pdf is not None and shard_of(it.doc_id, shards) == shard]
        done = cached_names(s.processed_dir)
        todo = [it for it in mine if it.doc_id not in done and it.doc_id not in failed]
        counts = {"assigned": len(mine), "already_done": len(mine) - len(todo), "converted": 0, "failed": 0}
        log = status_dir / f"shard_{shard}_of_{shards}.jsonl"
        converter = make_converter(s) if todo else None
        for i, item in enumerate(todo):
            if on_progress:
                on_progress(i, len(todo), self._display_name(item))
            start = time.monotonic()
            try:
                doc = convert(item.pdf, converter, s.processed_dir, item.doc_id, s.max_pages)
                row = {"doc_id": item.doc_id, "status": "ok", "pages": len(doc.pages)}
                counts["converted"] += 1
            except Exception as e:
                row = {"doc_id": item.doc_id, "status": "failed", "error": f"{type(e).__name__}: {e}"[:500]}
                counts["failed"] += 1
            row |= {"file": self._relative(item.pdf), "seconds": round(time.monotonic() - start, 1),
                    "time": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            with log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        if on_progress:
            on_progress(len(todo), len(todo), "done")
        return counts

    def reference_dois(self) -> set[str]:
        """DOIs of the papers refractiveindex.info takes its data from (their answers are known)."""
        dois = set()
        # Reading the database's thousands of small files is slow on a Drive mount:
        # the DOIs are read once and kept next to the corpus settings.
        cache = self.settings.data_dir / self.settings.corpus / "reference_dois.json"
        if cache.exists():
            dois |= set(json.loads(cache.read_text("utf-8")))
        elif self.settings.reference_db.exists():
            from matrag.references.refractiveindex import iter_entries

            found = sorted({e.doi for e in iter_entries(self.settings.reference_db) if e.doi})
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(found, indent=0), "utf-8")
            dois |= set(found)
        root = self.settings.corpus_root
        listed = root / "04_Dispersion_Formulas_Data" / "refractiveindex_reference_dois.txt" if root else None
        if listed and listed.exists():
            dois |= {line.strip().replace("\\_", "_") for line in listed.read_text("utf-8").splitlines() if line.strip()}
        return dois

    def organize(self, move: bool = False) -> list[dict]:
        """Sort a linked collection's PDFs into category folders (see ``catalog.organize``)."""
        from matrag.catalog import organize

        if not self.settings.corpus_root:
            raise ValueError("organize works on a linked collection (matrag link <folder>)")
        return organize(self.settings.corpus_root, move, self.reference_dois())

    def status(self) -> dict[str, int]:
        """Counts of the corpus: papers by source type, conversions done, and indexed papers."""
        from matrag.ingest import cached_names

        plan = self.plan()
        counts: dict[str, int] = {}
        for item in plan.items:
            counts[item.source_type] = counts.get(item.source_type, 0) + 1
        done = cached_names(self.settings.processed_dir)
        counts["pdfs_converted"] = sum(it.doc_id in done for it in plan.items if it.pdf is not None)
        status_dir = self.settings.processed_dir / "_status"
        counts["pdfs_failed"] = len(_failed_ids(status_dir)) if status_dir.exists() else 0
        counts["duplicate_pdfs"] = len(plan.duplicates)
        counts["indexed_papers"] = len(self._indexed_doc_ids())
        return counts

    def _indexed_doc_ids(self) -> set[str]:
        """Papers in the database, read from the chunk store (without loading the embedding model)."""
        if "kb" in self.__dict__:
            return set(self.kb.doc_versions())
        path = self.settings.docstore_path
        if not path.exists():
            return set()
        from llama_index.core.storage.docstore import SimpleDocumentStore

        return {n.metadata.get("doc_id") for n in SimpleDocumentStore.from_persist_path(str(path)).docs.values()}

    def _relative(self, pdf: Path) -> str:
        try:
            return pdf.relative_to(self.settings.raw_pdf_dir).as_posix()
        except ValueError:
            return pdf.name

    def _display_name(self, item) -> str:
        return self._relative(item.pdf) if item.pdf else item.doc_id

    @staticmethod
    def _extra_metadata(item) -> dict:
        if item.entry is None:
            return {}
        e = item.entry
        return {"category": e.category, "material": e.material, "year": e.year or -1, "doi": e.doi}

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
        pdf = self.pdf_path(doc_id)
        self.kb.remove_document(doc_id)
        self.library.remove(doc_id)
        processed = self.settings.processed_dir
        files = [*self.settings.raw_pdf_dir.glob(f"{doc_id}.*"), processed / f"{doc_id}.json",
                 processed / f"{doc_id}.json.gz", *([pdf] if pdf else [])]
        for f in files:
            f.unlink(missing_ok=True)
        self.backup()

    def pdf_path(self, doc_id: str) -> Path | None:
        nodes = self.kb.nodes([doc_id])
        if not nodes or not nodes[0].metadata.get("source_file"):
            return None
        path = self.settings.raw_pdf_dir / nodes[0].metadata["source_file"]
        return path if path.suffix.lower() == ".pdf" and path.exists() else None

    def source_image(self, node_id: str):
        """Page image(s) of a chunk with its region highlighted (stacked if it spans pages)."""
        from PIL import Image

        from matrag.pdfview import render_highlight, source_pages

        node = self.kb.docstore.get_node(node_id)
        if node.metadata.get("source_type") in ("abstract", "metadata_only"):
            return None  # known only from the index: there is no page to show
        pdf = self.settings.raw_pdf_dir / node.metadata.get("source_file", "")
        if pdf.suffix.lower() != ".pdf" or not pdf.exists():
            raise FileNotFoundError(f"PDF not found for {node_id}: {pdf}")
        images = [render_highlight(pdf, node.metadata, page) for page in source_pages(node.metadata)[:3]]
        if len(images) == 1:
            return images[0]
        stacked = Image.new("RGB", (max(i.width for i in images), sum(i.height for i in images) + 12 * len(images)),
                            "#e8e7e3")
        y = 0
        for image in images:
            stacked.paste(image, (0, y))
            y += image.height + 12
        return stacked

    # --- using the knowledge base ---

    def retriever(self, mode: RetrievalMode = RetrievalMode.hybrid, top_k: int | None = None,
                  doc_ids: list[str] | None = None):
        # Building the BM25 index over tens of thousands of chunks takes seconds,
        # so retrievers are reused until the knowledge base changes.
        key = (mode, top_k or self.settings.top_k, tuple(sorted(doc_ids or ())), self.kb.revision)
        cache = self.__dict__.setdefault("_retrievers", {})
        if key not in cache:
            if len(cache) >= 8 or any(k[3] != self.kb.revision for k in cache):
                cache.clear()
            cache[key] = make_retriever(self.kb, mode, key[1], doc_ids or None)
        return cache[key]

    def search_query(self, text: str, provider: str | None = None) -> str | None:
        """English translation of a Persian question or property name (None if already English).

        The papers are in English, so Persian text is translated before retrieval;
        translations are cached so repeating a question costs no extra LLM call.
        """
        if not is_persian(text):
            return None
        if text not in self._translations:
            self._translations[text] = translate_query(text, self.llm(provider))
        return self._translations[text]

    def ask(self, question: str, provider: str | None = None, mode: RetrievalMode = RetrievalMode.hybrid,
            top_k: int | None = None, doc_ids: list[str] | None = None, language: str | None = None) -> Answer:
        query = self.search_query(question, provider)
        language = language or ("Persian" if query else None)
        return answer_with_rag(question, self.retriever(mode, top_k, doc_ids), self.llm(provider), language, query)

    def ask_without_rag(self, question: str, provider: str | None = None, language: str | None = None) -> Answer:
        query = self.search_query(question, provider)
        language = language or ("Persian" if query else None)
        return answer_without_rag(question, self.llm(provider), language, query)

    def pack(self, question: str, language: str | None = None, mode: RetrievalMode = RetrievalMode.hybrid,
             top_k: int | None = None, doc_ids: list[str] | None = None, provider: str | None = None) -> str:
        """Prompt file for a chat assistant. Only a Persian question needs the LLM (to translate it)."""
        k = top_k or self.settings.top_k
        query = self.search_query(question, provider)
        language = language or ("Persian" if query else None)
        nodes = self.retriever(mode, k, doc_ids).retrieve(query or question)
        about = {
            "question": question,
            **({"search query (English)": query} if query else {}),
            "corpus": self.settings.corpus,
            "retrieval": f"{mode.value}, top {k}",
            "embedding model": self.settings.embed_model,
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
        return build_context_pack(question, nodes, about, language, query)

    def extract(self, properties: list[str], provider: str | None = None, exhaustive: bool = False,
                mode: RetrievalMode = RetrievalMode.hybrid, top_k: int | None = None,
                doc_ids: list[str] | None = None) -> list[ExtractedRecord]:
        from matrag.extract import extract

        s = self._settings_for(provider)
        llm = self.llm(provider)
        # Property names typed in Persian are translated like questions.
        properties = [self.search_query(p, provider) or p for p in properties]
        if exhaustive:
            records = extract(properties, llm, nodes=self.kb.nodes(doc_ids or None), min_interval_s=s.llm_min_interval_s)
        else:
            records = extract(properties, llm, retriever=self.retriever(mode, top_k, doc_ids),
                              min_interval_s=s.llm_min_interval_s)
        from matrag.profiles import load_profile, plausibility

        specs = load_profile(s)
        for r in records:
            r.llm = s.llm_name
            r.plausible = plausibility(r.property, r.value, specs)
        return records

    def extract_formulas(self, doc_ids: list[str] | None = None, provider: str | None = None,
                         on_progress: Callable[[int, int, str], None] | None = None):
        """Dispersion formulas of the given papers (default: all), checked against refractiveindex.info."""
        from matrag.formulas import compare_with_reference, extract_formulas
        from matrag.ingest import cached_document
        from matrag.references.refractiveindex import find_entries

        s = self._settings_for(provider)
        llm = self.llm(provider)
        library = self.library
        # Formulas are only read from full texts, not from abstracts.
        full_text = {d for d, t in self.kb.doc_source_types().items() if t == "full_text_pdf"}
        doc_ids = [d for d in (doc_ids or self.kb.doc_ids()) if d in full_text]
        records = []
        for i, doc_id in enumerate(doc_ids):
            if on_progress:
                on_progress(i, len(doc_ids), doc_id)
            doc = cached_document(s.processed_dir, doc_id)
            found = extract_formulas(doc, self.kb.nodes([doc_id]), llm, s.llm_min_interval_s)
            paper = library.get(doc_id)
            entries = (find_entries(s.reference_db, doi=paper.doi, arxiv_id=paper.arxiv_id)
                       if s.reference_db.exists() else [])
            for record in found:
                record.llm = s.llm_name
                if entries:
                    compare_with_reference(record, entries)
            records += found
        if on_progress:
            on_progress(len(doc_ids), len(doc_ids), "done")
        return records

    def default_properties(self) -> list[str]:
        from matrag.profiles import load_profile

        return [spec.name for spec in load_profile(self.settings)]


def _failed_ids(status_dir: Path) -> set[str]:
    """Papers whose latest conversion attempt (in any worker's log) failed."""
    latest: dict[str, str] = {}
    for log in sorted(status_dir.glob("shard_*.jsonl")):
        for line in log.read_text("utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:  # a line cut off by a disconnect
                continue
            latest[row["doc_id"]] = row["status"]
    return {doc_id for doc_id, status in latest.items() if status == "failed"}


def _same_file(a: Path, b: Path) -> bool:
    import filecmp

    return filecmp.cmp(a, b, shallow=False)


def _safe_name(name: str) -> str:
    """File names become doc ids: keep them short and filesystem/URL friendly."""
    stem, suffix = Path(name).stem, Path(name).suffix.lower()
    stem = re.sub(r"[^\w.-]+", "_", stem).strip("_")[:80] or "paper"
    return stem + suffix


def slugify(text: str, length: int = 60) -> str:
    return re.sub(r"[^\w]+", "_", text.lower()).strip("_")[:length]
