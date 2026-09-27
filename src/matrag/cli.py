"""Command-line interface.

    matrag ingest                  # convert + index every paper in data/<corpus>/pdfs
    matrag add 2111.01212 x.pdf    # add papers (arXiv ids or files) and index them
    matrag info                    # list indexed papers
    matrag ask "question"          # grounded answer with citations
    matrag ask "question" --no-rag # baseline: the LLM alone
    matrag pack "question"         # prompt file with sources, to upload to any chat AI
    matrag extract -p "line intensity" -p "air-broadened half-width" -o results/x.csv
    matrag app                     # web interface

Global options pick the corpus and the LLM, e.g.:
    matrag --corpus optical --llm gemini ask "..."
"""

import os
from pathlib import Path
from typing import Annotated

import typer

from matrag.retrieve import RetrievalMode

app = typer.Typer(help="RAG over scientific papers for material properties.", no_args_is_help=True)

DocOption = Annotated[list[str] | None, typer.Option("--doc", help="Restrict to these doc ids (repeatable).")]
TopKOption = Annotated[int | None, typer.Option(help="Number of chunks to retrieve.")]


@app.callback()
def main(
    corpus: Annotated[str | None, typer.Option(help="Corpus name (default: MATRAG_CORPUS or 'hitran').")] = None,
    llm: Annotated[str | None, typer.Option(help="LLM provider: ollama or gemini.")] = None,
) -> None:
    # Passed on through the environment so every Settings() sees them.
    if corpus:
        os.environ["MATRAG_CORPUS"] = corpus
    if llm:
        os.environ["MATRAG_LLM_PROVIDER"] = llm


def _workspace():
    from matrag.pipeline import Workspace

    return Workspace()


def _print_ingest(results) -> None:
    for r in results:
        if r.error:
            typer.echo(f"  ✗ {r.file}: {r.error}", err=True)
        elif r.skipped:
            typer.echo(f"  = {r.file}: {r.citation} (already indexed)")
        else:
            typer.echo(f"  ✓ {r.file}: {r.citation}, {r.chunks} chunks")


@app.command()
def ingest(
    paths: Annotated[list[Path] | None, typer.Argument(help="Files to ingest (default: data/<corpus>/pdfs).")] = None,
    force: Annotated[bool, typer.Option(help="Re-index papers that are already in the database.")] = False,
) -> None:
    """Convert papers with Docling, chunk them and add them to the vector database."""
    ws = _workspace()
    if paths:
        paths = ws.add_files(paths)
    elif not any(ws.settings.raw_pdf_dir.iterdir()):
        typer.echo(f"No papers found in {ws.settings.raw_pdf_dir}", err=True)
        raise typer.Exit(1)
    _print_ingest(ws.ingest(paths, force, on_progress=_echo_progress))


def _echo_progress(i: int, n: int, name: str) -> None:
    if i < n:
        typer.echo(f"[{i + 1}/{n}] {name}")


@app.command()
def add(items: Annotated[list[str], typer.Argument(help="arXiv ids (e.g. 2111.01212) or paths to PDF files.")]) -> None:
    """Add papers to the corpus and index them."""
    ws = _workspace()
    paths = []
    for item in items:
        if Path(item).exists():
            paths += ws.add_files([Path(item)])
        else:
            paths.append(ws.download_arxiv(item))
            typer.echo(f"downloaded arXiv:{item}")
    _print_ingest(ws.ingest(paths))


@app.command()
def info() -> None:
    """List the papers in the knowledge base."""
    ws = _workspace()
    papers = ws.papers()
    for paper, chunks in papers:
        typer.echo(f"{paper.doc_id}: {paper.short_citation()}, {chunks} chunks")
        if paper.title:
            typer.echo(f"    {paper.title}")
    typer.echo(f"Total: {len(papers)} papers")


@app.command()
def ask(
    question: str,
    mode: RetrievalMode = RetrievalMode.hybrid,
    top_k: TopKOption = None,
    doc: DocOption = None,
    no_rag: Annotated[bool, typer.Option("--no-rag", help="Baseline: ask the LLM without retrieval.")] = False,
    show_sources: bool = True,
) -> None:
    """Answer a question from the papers, with citations."""
    from matrag.qa import format_source_label

    ws = _workspace()
    typer.echo(f"[{ws.settings.corpus} | {ws.llm_name()}]", err=True)
    if no_rag:
        typer.echo(ws.ask_without_rag(question).text)
        return
    answer = ws.ask(question, mode=mode, top_k=top_k, doc_ids=doc)
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
    top_k: TopKOption = None,
    doc: DocOption = None,
) -> None:
    """Retrieve sources and write a prompt file to upload to a chat assistant (no LLM call)."""
    from matrag.pipeline import slugify

    ws = _workspace()
    text = ws.pack(question, language, mode, top_k, doc)
    out = out or Path("results/packs") / f"{ws.settings.corpus}_{slugify(question)}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    typer.echo(f"{text.count(chr(10) + '[')} sources written to {out}")


@app.command()
def extract(
    prop: Annotated[list[str], typer.Option("--property", "-p", help="Property to extract (repeatable).")],
    out: Annotated[Path, typer.Option("--out", "-o", help="Output .csv or .jsonl file.")] = Path("results/extracted.csv"),
    doc: DocOption = None,
    exhaustive: Annotated[bool, typer.Option(help="Process every chunk instead of retrieved ones.")] = False,
    mode: RetrievalMode = RetrievalMode.hybrid,
    top_k: TopKOption = None,
) -> None:
    """Extract property values into a table."""
    from matrag.extract import save_records

    ws = _workspace()
    typer.echo(f"[{ws.settings.corpus} | {ws.llm_name()}]", err=True)
    records = ws.extract(prop, exhaustive=exhaustive, mode=mode, top_k=top_k, doc_ids=doc)
    save_records(records, out)
    unverified = sum(not r.value_in_source for r in records)
    typer.echo(f"{len(records)} values saved to {out} ({unverified} not found verbatim in their source)")


evaluate_app = typer.Typer(help="Evaluate against gold data in data/<corpus>/gold/.", no_args_is_help=True)
app.add_typer(evaluate_app, name="evaluate")


def _gold(name: str) -> Path:
    from matrag.config import get_settings

    path = get_settings().data_dir / get_settings().corpus / "gold" / name
    if not path.exists():
        typer.echo(f"Gold file not found: {path}", err=True)
        raise typer.Exit(1)
    return path


def _print_table(rows: list[dict]) -> None:
    widths = {k: max(len(str(k)), *(len(str(r[k])) for r in rows)) for k in rows[0]}
    typer.echo("  ".join(str(k).ljust(w) for k, w in widths.items()))
    for r in rows:
        typer.echo("  ".join(str(r[k]).ljust(w) for k, w in widths.items()))


@evaluate_app.command("retrieval")
def evaluate_retrieval(
    modes: Annotated[list[RetrievalMode] | None, typer.Option("--mode", help="Modes to compare (default: all).")] = None,
    k: Annotated[int, typer.Option(help="Chunks retrieved per question.")] = 10,
) -> None:
    """Recall@k and MRR of each retrieval mode (no LLM needed)."""
    from matrag.evaluate import evaluate_retrieval as run, load_questions, write_rows

    ws = _workspace()
    items = load_questions(_gold("questions.csv"))
    reports = [run(items, ws.retriever(m, k), m.value, ks=tuple(x for x in (1, 3, 5, 10) if x <= k))
               for m in modes or list(RetrievalMode)]
    rows = [r.summary() for r in reports]
    _print_table(rows)
    out = Path("results/eval") / f"{ws.settings.corpus}_retrieval.csv"
    write_rows(out, rows)
    write_rows(out.with_name(out.stem + "_ranks.csv"),
               [{"id": i, **{r.mode: r.ranks[i] for r in reports}} for i in reports[0].ranks])
    typer.echo(f"saved {out}")


@evaluate_app.command("answers")
def evaluate_answers(
    no_rag: Annotated[bool, typer.Option(help="Also evaluate the LLM without retrieval.")] = True,
    top_k: TopKOption = None,
    limit: Annotated[int | None, typer.Option(help="Only the first N questions (to save API quota).")] = None,
) -> None:
    """Share of answers containing the expected values: RAG vs the LLM alone."""
    from matrag.evaluate import evaluate_answers as run, load_questions, write_rows

    ws = _workspace()
    items = load_questions(_gold("questions.csv"))[:limit]
    name = ws.llm_name()
    progress = lambda i: typer.echo(f"  {i}", err=True)  # noqa: E731
    systems = [(f"RAG + {name}", lambda q: ws.ask(q, top_k=top_k).text)]
    if no_rag:
        systems.append((f"{name} alone", lambda q: ws.ask_without_rag(q).text))
    reports = [run(items, fn, system, on_item=progress) for system, fn in systems]
    _print_table([r.summary() for r in reports])
    out = Path("results/eval") / f"{ws.settings.corpus}_answers.csv"
    write_rows(out, [r.summary() for r in reports])
    write_rows(out.with_name(out.stem + "_details.csv"),
               [{"id": it.id, "question": it.question,
                 **{f"{r.system} correct": r.correct[it.id] for r in reports},
                 **{f"{r.system} answer": r.answers[it.id] for r in reports}} for it in items])
    typer.echo(f"saved {out}")


@evaluate_app.command("extraction")
def evaluate_extraction(
    records: Annotated[Path, typer.Argument(help="CSV written by 'matrag extract'.")],
) -> None:
    """Precision, recall and F1 of extracted values against data/<corpus>/gold/values.csv."""
    from matrag.evaluate import evaluate_extraction as run, load_records, load_values, write_rows

    ws = _workspace()
    report = run(load_records(records), load_values(_gold("values.csv")))
    _print_table([report.summary()])
    out = Path("results/eval") / f"{ws.settings.corpus}_extraction.csv"
    write_rows(out, [report.summary()])
    typer.echo(f"saved {out}")


@app.command(name="app")
def run_app(
    port: int = 7860,
    share: Annotated[bool, typer.Option(help="Create a temporary public Gradio link.")] = False,
) -> None:
    """Start the web interface."""
    from matrag.webapp import launch

    launch(port=port, share=share)


if __name__ == "__main__":
    app()
