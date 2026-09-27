"""Command-line interface.

    matrag ingest                  # convert + index every paper in data/<corpus>/pdfs
    matrag info                    # list indexed papers
    matrag ask "question"          # grounded answer with citations
    matrag ask "question" --no-rag # baseline: the LLM alone
    matrag pack "question"         # prompt file with sources, to upload to any chat AI
    matrag extract -p "line intensity" -p "air-broadened half-width" -o results/x.csv

Global options pick the corpus and the LLM, e.g.:
    matrag --corpus optical --llm gemini ask "..."
"""

import os
from pathlib import Path
from typing import Annotated

import typer

from matrag.config import get_settings
from matrag.retrieve import RetrievalMode

app = typer.Typer(help="RAG over scientific papers for material properties.", no_args_is_help=True)


@app.callback()
def main(
    corpus: Annotated[str | None, typer.Option(help="Corpus name (default: MATRAG_CORPUS or 'hitran').")] = None,
    llm: Annotated[str | None, typer.Option(help="LLM provider: ollama or gemini.")] = None,
) -> None:
    # Passed on through the environment so get_settings() sees them everywhere.
    if corpus:
        os.environ["MATRAG_CORPUS"] = corpus
    if llm:
        os.environ["MATRAG_LLM_PROVIDER"] = llm


def _knowledge_base():
    from matrag.index import KnowledgeBase, make_embed_model

    settings = get_settings()
    return KnowledgeBase(settings, make_embed_model(settings))


@app.command()
def ingest(
    paths: Annotated[list[Path] | None, typer.Argument(help="Files to ingest (default: data/<corpus>/pdfs).")] = None,
    force: Annotated[bool, typer.Option(help="Re-index papers that are already in the database.")] = False,
) -> None:
    """Convert papers with Docling, chunk them and add them to the vector database."""
    from matrag.ingest import INGEST_VERSION, chunk_document, convert, find_papers, make_chunker, make_converter

    settings = get_settings()
    paths = paths or find_papers(settings.raw_pdf_dir)
    if not paths:
        typer.echo(f"No papers found in {settings.raw_pdf_dir}", err=True)
        raise typer.Exit(1)

    kb = _knowledge_base()
    versions = kb.doc_versions()
    converter, chunker = make_converter(settings), make_chunker(settings)
    for i, path in enumerate(paths, start=1):
        typer.echo(f"[{i}/{len(paths)}] {path.name}")
        if versions.get(path.stem) == INGEST_VERSION and not force:
            typer.echo("    already indexed (use --force to rebuild)")
            continue
        doc = convert(path, converter, settings.processed_dir)
        nodes = chunk_document(doc, doc_id=path.stem, chunker=chunker)
        kb.add_document(path.stem, nodes)
        typer.echo(f"    {len(nodes)} chunks")


@app.command()
def info() -> None:
    """List the papers in the knowledge base."""
    kb = _knowledge_base()
    doc_ids = kb.doc_ids()
    for doc_id in doc_ids:
        typer.echo(f"{doc_id}: {len(kb.nodes([doc_id]))} chunks")
    typer.echo(f"Total: {len(doc_ids)} papers")


@app.command()
def ask(
    question: str,
    mode: RetrievalMode = RetrievalMode.hybrid,
    top_k: Annotated[int | None, typer.Option(help="Chunks to retrieve.")] = None,
    doc: Annotated[list[str] | None, typer.Option(help="Restrict to these doc ids.")] = None,
    no_rag: Annotated[bool, typer.Option("--no-rag", help="Baseline: ask the LLM without retrieval.")] = False,
    show_sources: bool = True,
) -> None:
    """Answer a question from the papers, with citations."""
    from matrag.llm import make_llm
    from matrag.qa import answer_with_rag, answer_without_rag, format_source_label

    settings = get_settings()
    llm = make_llm(settings)
    typer.echo(f"[{settings.corpus} | {settings.llm_name}]", err=True)
    if no_rag:
        typer.echo(answer_without_rag(question, llm).text)
        return

    from matrag.retrieve import make_retriever

    retriever = make_retriever(_knowledge_base(), mode, top_k or settings.top_k, doc)
    answer = answer_with_rag(question, retriever, llm)
    typer.echo(answer.text)
    if show_sources:
        typer.echo("\nSources:")
        for i, node in enumerate(answer.sources, start=1):
            typer.echo(f"  [{i}] {format_source_label(node)}  (score {node.score:.3f})")


@app.command()
def pack(
    question: str,
    out: Annotated[Path | None, typer.Option("--out", "-o", help="Output file (default: results/packs/<question>.md).")] = None,
    language: Annotated[str | None, typer.Option(help="Language of the answer, e.g. Persian.")] = None,
    mode: RetrievalMode = RetrievalMode.hybrid,
    top_k: Annotated[int | None, typer.Option(help="Chunks to include.")] = None,
    doc: Annotated[list[str] | None, typer.Option(help="Restrict to these doc ids.")] = None,
) -> None:
    """Retrieve sources and write a prompt file to upload to a chat assistant (no LLM call)."""
    import re
    from datetime import datetime, timezone

    from matrag.qa import build_context_pack
    from matrag.retrieve import make_retriever

    settings = get_settings()
    k = top_k or settings.top_k
    nodes = make_retriever(_knowledge_base(), mode, k, doc).retrieve(question)
    about = {
        "question": question,
        "corpus": settings.corpus,
        "retrieval": f"{mode.value}, top {k}",
        "embedding model": settings.embed_model,
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    if out is None:
        slug = re.sub(r"[^\w]+", "_", question.lower()).strip("_")[:60]
        out = Path("results/packs") / f"{settings.corpus}_{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_context_pack(question, nodes, about, language), encoding="utf-8")
    typer.echo(f"{len(nodes)} sources written to {out}")


@app.command()
def extract(
    prop: Annotated[list[str], typer.Option("--property", "-p", help="Property to extract (repeatable).")],
    out: Annotated[Path, typer.Option("--out", "-o", help="Output .csv or .jsonl file.")] = Path("results/extracted.csv"),
    doc: Annotated[list[str] | None, typer.Option(help="Restrict to these doc ids.")] = None,
    exhaustive: Annotated[bool, typer.Option(help="Process every chunk instead of retrieved ones.")] = False,
    mode: RetrievalMode = RetrievalMode.hybrid,
    top_k: Annotated[int | None, typer.Option(help="Chunks retrieved per property.")] = None,
) -> None:
    """Extract property values into a table."""
    from matrag.extract import extract as run_extract
    from matrag.extract import save_records
    from matrag.llm import make_llm
    from matrag.retrieve import make_retriever

    settings = get_settings()
    kb = _knowledge_base()
    llm = make_llm(settings)
    typer.echo(f"[{settings.corpus} | {settings.llm_name}]", err=True)
    if exhaustive:
        records = run_extract(prop, llm, nodes=kb.nodes(doc), min_interval_s=settings.llm_min_interval_s)
    else:
        retriever = make_retriever(kb, mode, top_k or settings.top_k, doc)
        records = run_extract(prop, llm, retriever=retriever, min_interval_s=settings.llm_min_interval_s)

    for r in records:
        r.llm = settings.llm_name
    save_records(records, out)
    unverified = sum(not r.value_in_source for r in records)
    typer.echo(f"{len(records)} values saved to {out} ({unverified} not found verbatim in their source)")


if __name__ == "__main__":
    app()
