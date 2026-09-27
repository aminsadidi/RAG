"""Command-line interface.

    matrag ingest                  # convert + index every paper in data/raw_pdfs
    matrag info                    # list indexed papers
    matrag ask "question"          # grounded answer with citations
    matrag ask "question" --no-rag # baseline: the LLM alone
    matrag extract -p "line intensity" -p "air-broadened half-width" -o results/x.csv
"""

from pathlib import Path
from typing import Annotated

import typer

from matrag.config import get_settings
from matrag.retrieve import RetrievalMode

app = typer.Typer(help="RAG over scientific papers for material properties.", no_args_is_help=True)


def _knowledge_base():
    from matrag.index import KnowledgeBase, make_embed_model

    settings = get_settings()
    return KnowledgeBase(settings, make_embed_model(settings))


@app.command()
def ingest(
    paths: Annotated[list[Path] | None, typer.Argument(help="Files to ingest (default: data/raw_pdfs).")] = None,
) -> None:
    """Convert papers with Docling, chunk them and add them to the vector database."""
    from matrag.ingest import chunk_document, convert, find_papers, make_chunker, make_converter

    settings = get_settings()
    paths = paths or find_papers(settings.raw_pdf_dir)
    if not paths:
        typer.echo(f"No papers found in {settings.raw_pdf_dir}", err=True)
        raise typer.Exit(1)

    kb = _knowledge_base()
    converter, chunker = make_converter(settings), make_chunker(settings)
    for i, path in enumerate(paths, start=1):
        typer.echo(f"[{i}/{len(paths)}] {path.name}")
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
    if exhaustive:
        records = run_extract(prop, llm, nodes=kb.nodes(doc), min_interval_s=settings.llm_min_interval_s)
    else:
        retriever = make_retriever(kb, mode, top_k or settings.top_k, doc)
        records = run_extract(prop, llm, retriever=retriever, min_interval_s=settings.llm_min_interval_s)

    save_records(records, out)
    unverified = sum(not r.value_in_source for r in records)
    typer.echo(f"{len(records)} values saved to {out} ({unverified} not found verbatim in their source)")


if __name__ == "__main__":
    app()
