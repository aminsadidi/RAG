"""Command-line interface.

    matrag ingest                  # convert + index every paper in data/<corpus>/pdfs
    matrag link /path/RAG-Optics   # read the corpus from a folder with a master index (e.g. on Drive)
    matrag organize --move         # sort a linked collection's PDFs into category folders
    matrag convert --shard 0 --shards 4   # parallel workers: convert PDFs only
    matrag status                  # papers with PDF / abstract / title, converted, indexed
    matrag add 2111.01212 x.pdf    # add papers (arXiv ids or files) and index them
    matrag info                    # list indexed papers
    matrag ask "question"          # grounded answer with citations
    matrag ask "question" --no-rag # baseline: the LLM alone
    matrag pack "question"         # prompt file with sources, to upload to any chat AI
    matrag extract -p "line intensity" -p "air-broadened half-width" -o results/x.csv
    matrag formulas                # dispersion formulas (Sellmeier, ...) vs refractiveindex.info
    matrag formula-table f.jsonl   # a formula as a table of n(λ)
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
    prune: Annotated[bool, typer.Option(help="Remove indexed papers that are no longer in the corpus.")] = False,
    quiet: Annotated[bool, typer.Option(help="Print only errors and a summary.")] = False,
) -> None:
    """Convert papers with Docling, chunk them and add them to the vector database."""
    ws = _workspace()
    if paths:
        paths = ws.add_files(paths)
    elif not ws.settings.corpus_root and not any(ws.settings.raw_pdf_dir.iterdir()):
        typer.echo(f"No papers found in {ws.settings.raw_pdf_dir}", err=True)
        raise typer.Exit(1)
    results = ws.ingest(paths, force, on_progress=None if quiet else _echo_progress, prune=prune)
    # A whole collection: list only the problems, not thousands of lines.
    _print_ingest([r for r in results if r.error] if quiet or len(results) > 100 else results)
    new = [r for r in results if not r.skipped and not r.error]
    typer.echo(f"Indexed {len(new)} papers ({sum(r.chunks for r in new)} chunks); "
               f"{sum(r.skipped for r in results)} unchanged; {sum(bool(r.error) for r in results)} errors.")


@app.command()
def link(
    folder: Annotated[Path, typer.Argument(help="Folder with the papers, e.g. /content/drive/MyDrive/RAG-Optics.")],
) -> None:
    """Make the corpus read its papers from a folder (any sub-folder) with a master index."""
    from matrag.config import get_settings
    from matrag.pipeline import link_collection

    corpus = get_settings().corpus
    link_collection(corpus, folder)
    # Create the shared output folder now: workers starting at the same moment could
    # otherwise each create one, and Drive allows two folders with the same name.
    (_workspace().settings.processed_dir / "_status").mkdir(parents=True, exist_ok=True)
    typer.echo(f"Corpus '{corpus}' now reads its papers from {folder}")


@app.command()
def organize(
    move: Annotated[bool, typer.Option(help="Really move the files (default: only show what would happen).")] = False,
) -> None:
    """Sort the collection's PDFs into 01_Papers_by_Category/<category>/<material>/ (nothing is deleted)."""
    from collections import Counter

    rows = _workspace().organize(move)
    moved = [r for r in rows if r["moved_from"]]
    verb = "moved" if move else "would move"
    for r in moved[:20]:
        typer.echo(f"  {r['moved_from']} -> {r['file']}")
    if len(moved) > 20:
        typer.echo(f"  ... and {len(moved) - 20} more")
    kinds = Counter(r["kind"] for r in rows)
    typer.echo(f"{len(rows)} PDFs: {kinds['indexed']} in the master index, {kinds['not_in_index']} not in it, "
               f"{kinds['duplicate']} duplicate copies; {verb} {len(moved)}; "
               f"{sum(r['in_refractiveindex'] for r in rows)} are data sources of refractiveindex.info.")
    if move:
        typer.echo("Report: 02_Master_Index/pdf_inventory.csv")


@app.command()
def convert(
    shard: Annotated[int, typer.Option(help="This worker's number: 0, 1, ..., shards-1.")] = 0,
    shards: Annotated[int, typer.Option(help="Number of workers running in parallel.")] = 1,
    retry_failed: Annotated[bool, typer.Option(help="Try again papers whose conversion failed before.")] = False,
) -> None:
    """Convert PDFs with Docling only (no database, no LLM); run in several sessions with --shard/--shards."""
    ws = _workspace()
    typer.echo(f"Worker {shard} of {shards}: converting into {ws.settings.processed_dir}")
    counts = ws.convert_shard(shard, shards, retry_failed, on_progress=_echo_progress)
    typer.echo(", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in counts.items()))


@app.command()
def status() -> None:
    """How many papers there are (full text / abstract / title only), converted and indexed."""
    ws = _workspace()
    labels = {"full_text_pdf": "papers with PDF", "abstract": "papers with abstract only",
              "metadata_only": "papers with title only", "pdfs_converted": "PDFs converted",
              "pdfs_failed": "PDFs that failed to convert", "duplicate_pdfs": "duplicate PDFs (ignored)",
              "indexed_papers": "papers in the database"}
    for key, value in ws.status().items():
        typer.echo(f"{labels.get(key, key)}: {value}")


_started: list[float] = []


def _echo_progress(i: int, n: int, name: str) -> None:
    """Every item for small batches; for large ones every 25th, with the time left."""
    import time

    if i == 0:
        _started[:] = [time.monotonic()]
    if i >= n or (n > 100 and i % 25):
        return
    line = f"[{i + 1}/{n}] {name}"
    if n > 100 and i:
        left = (time.monotonic() - _started[0]) / i * (n - i)
        line += f"   (about {left / 60:.0f} min left)"
    typer.echo(line, err=False)


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
    text = ws.pack(question, language, mode, top_k, doc)  # a Persian question is translated first
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


@app.command()
def formulas(
    doc: DocOption = None,
    out: Annotated[Path, typer.Option("--out", "-o", help="Output .jsonl file.")] = Path("results/formulas.jsonl"),
) -> None:
    """Extract dispersion formulas (Sellmeier, Cauchy, ...) and compare them with refractiveindex.info."""
    from matrag.formulas import save_formulas

    ws = _workspace()
    typer.echo(f"[{ws.settings.corpus} | {ws.llm_name()}]", err=True)
    records = ws.extract_formulas(doc, on_progress=_echo_progress)
    save_formulas(records, out)
    if records:
        _print_table([{"#": i, "paper": r.doc_id, "material": r.formula.material, "axis": r.formula.axis,
                       "range_um": "%s-%s" % r.formula.valid_range_um(), "T_K": r.formula.temperature_K or "",
                       "in_source": r.numbers_in_source, "problems": "; ".join(r.problems) or "-",
                       "max_dn_vs_ref": r.reference_max_dn if r.reference_max_dn is not None else "-"}
                      for i, r in enumerate(records)])
    typer.echo(f"{len(records)} formulas saved to {out}")


@app.command("formula-table")
def formula_table(
    formulas_file: Annotated[Path, typer.Argument(help="File written by 'matrag formulas'.")],
    index: Annotated[int, typer.Option(help="Which formula (the # column).")] = 0,
    start: Annotated[float, typer.Option("--from", help="First wavelength, µm (default: start of validity range).")] = 0.0,
    stop: Annotated[float, typer.Option("--to", help="Last wavelength, µm (default: end of validity range).")] = 0.0,
    step: Annotated[float, typer.Option(help="Wavelength step, µm.")] = 0.05,
    temperature: Annotated[float | None, typer.Option(help="Temperature in K (temperature-dependent formulas).")] = None,
    out: Annotated[Path | None, typer.Option("--out", "-o")] = None,
) -> None:
    """Turn an extracted formula into a table of n(λ)."""
    import numpy as np

    from matrag.dispersion import table
    from matrag.evaluate import write_rows
    from matrag.formulas import load_formulas

    record = load_formulas(formulas_file)[index]
    lo, hi = record.formula.valid_range_um()
    lam = np.arange(start or lo, (stop or hi) + step / 2, step)
    rows = table(lambda x: record.formula.refractive_index(x, temperature), lam)
    out = out or formulas_file.with_name(f"{record.doc_id}_{record.formula.material}_{record.formula.axis or 'n'}.csv")
    write_rows(out, rows)
    typer.echo(f"{len(rows)} wavelengths written to {out}")


@app.command("export-qdrant")
def export_qdrant(
    recreate: Annotated[bool, typer.Option(help="Delete and rebuild the collection.")] = False,
    collection: Annotated[str | None, typer.Option(help="Collection name (default: the corpus name).")] = None,
) -> None:
    """Upload the knowledge base (chunks, their stored embeddings, BM25) to Qdrant for the web app.

    Needs QDRANT_URL and QDRANT_API_KEY; resumable (chunks already uploaded are skipped).
    """
    from matrag import qdrant_store

    ws = _workspace()
    name = collection or ws.settings.corpus
    qc = qdrant_store.client()
    n = qdrant_store.export(ws.kb, qc, name, recreate=recreate, root=str(ws.settings.corpus_root or "") or None,
                            on_progress=lambda i, total: typer.echo(f"  {i}/{total}") if i % 2048 < 64 or i == total else None)
    info = qc.get_collection(name)
    typer.echo(f"uploaded {n} chunks; collection '{name}' now holds {info.points_count} points")


@app.command("export-formulas")
def export_formulas(
    out: Annotated[Path, typer.Argument(help="Folder to write (the site's static files).")] = Path("web/public/ri"),
) -> None:
    """Write the refractiveindex.info n(λ) entries for the site's refractive index tab: index.json (the
    materials) and m/<i>.json (the entries of material i), served as static files."""
    import json
    import shutil

    from matrag.config import Settings
    from matrag.references import anisotropic, paper_formulas
    from matrag.references.refractiveindex import book_names, formula_catalog

    entries = formula_catalog(Settings().reference_db)
    names = book_names(Settings().reference_db)
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for e in entries:
        groups.setdefault((e["shelf"], e["group"], e["material"]), []).append(e)
    shutil.rmtree(out / "m", ignore_errors=True)
    (out / "m").mkdir(parents=True)
    index = []
    for i, ((shelf, group, material), items) in enumerate(sorted(groups.items(), key=lambda kv: (kv[0][0] != "main", kv[0]))):
        (out / "m" / f"{i}.json").write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        name = names.get((shelf, group, material), "")
        index.append({"i": i, "shelf": shelf, "group": group, "material": material,
                      **({"name": name} if name and name != material else {}), "n": len(items),
                      "formulas": sum(e["type"] != "tab" for e in items),
                      "range_um": [min(e["range_um"][0] for e in items), max(e["range_um"][1] for e in items)]})
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    typer.echo(f"{len(entries)} entries ({sum(e['type'] != 'tab' for e in entries)} formulas) for "
               f"{len(index)} materials written to {out}")
    added = paper_formulas.add_to_site(out, Settings().data_dir / Settings().corpus / "paper_formulas.yml")
    typer.echo(f"{added} more materials from formulas read in the collection's papers (paper_formulas.yml)")
    thermo = Settings().data_dir / Settings().corpus / "thermo_optic.yml"
    dij = Settings().data_dir / Settings().corpus / "nonlinear_coefficients.yml"
    cubic = anisotropic.cubic_crystals(dij)
    typer.echo(f"{anisotropic.build(out, thermo, cubic)} crystals written to aniso.json (phase-matching tab; "
               f"{len(cubic)} cubic, for QPM only)")
    typer.echo(f"{anisotropic.build_nonlinear(out, dij)} crystals with nonlinear coefficients written to dij.json")


@app.command("export-papers")
def export_papers(
    out: Annotated[Path, typer.Argument(help="JSON file to write.")] = Path("web/src/papers.json"),
    collection: Annotated[str | None, typer.Option(help="Collection name (default: the corpus name).")] = None,
) -> None:
    """Write the list of papers in the Qdrant collection, for the site's collection browser."""
    import json

    from matrag import qdrant_store
    from matrag.config import Settings

    rows = qdrant_store.paper_list(qdrant_store.client(), collection or Settings().corpus)
    out.write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    typer.echo(f"{len(rows)} papers written to {out}")


@app.command("export-pdfs")
def export_pdfs(dest: Annotated[Path, typer.Argument(help="Folder to copy the PDFs into (web-pdfs/pdfs).")]) -> None:
    """Copy the PDFs of the full-text papers into a folder, for the site's PDF Worker (web-pdfs/)."""
    from matrag import qdrant_store

    ws = _workspace()
    root = ws.settings.corpus_root
    if root is None:
        raise typer.BadParameter("no collection linked (matrag link)")
    copied, skipped = qdrant_store.copy_pdfs(ws.kb, str(root), str(dest))
    typer.echo(f"{copied} PDFs in {dest}; skipped {len(skipped)} (missing or over 25 MB)")
    for rel in skipped[:20]:
        typer.echo(f"  skipped: {rel}")


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
    persian: Annotated[bool, typer.Option(help="Use the Persian questions (question_fa), translated by the LLM.")] = False,
    backend: Annotated[str, typer.Option(help="'local' (this database) or 'qdrant' (the web app's search).")] = "local",
    gold: Annotated[list[str] | None, typer.Option("--gold", help="Question files in gold/ (default: questions.csv; "
                                                    "repeat for several, e.g. --gold questions.csv --gold generated.csv).")] = None,
) -> None:
    """Recall@k and MRR of each retrieval mode, overall and per group of questions (no LLM needed,
    except with --persian)."""
    from matrag.evaluate import evaluate_retrieval as run, group_summaries, load_questions, write_rows

    ws = _workspace()
    items = [it for name in gold or ["questions.csv"] for it in load_questions(_gold(name))]
    items = [it for it in items if it.answerable]
    query_fn = None
    if persian:
        items = [it for it in items if it.question_fa]
        typer.echo(f"Translating {len(items)} Persian questions...", err=True)
        from concurrent.futures import ThreadPoolExecutor

        # several at once: Ollama serves parallel requests (OLLAMA_NUM_PARALLEL)
        with ThreadPoolExecutor(4) as pool:
            done = list(pool.map(lambda it: ws.search_query(it.question_fa) or it.question_fa, items))
        translations = {it.id: tr for it, tr in zip(items, done)}
        query_fn = lambda it: translations[it.id]  # noqa: E731
    typer.echo(f"{len(items)} questions", err=True)
    ks = tuple(x for x in (1, 3, 5, 10) if x <= k)
    tag = (" (qdrant)" if backend == "qdrant" else "") + (" (fa→en)" if persian else "")
    retriever = _qdrant_retrievers(ws, items, k, query_fn) if backend == "qdrant" else (lambda m: ws.retriever(m, k))
    reports = [run(items, retriever(m), m.value + tag, ks, query_fn) for m in modes or list(RetrievalMode)]
    rows = [r.summary() for r in reports]
    _print_table(rows)
    groups = [{"mode": r.mode, **g} for r in reports for g in group_summaries(r, items)]
    _print_table(groups)
    suffix = "_retrieval" + ("_qdrant" if backend == "qdrant" else "") + ("_fa" if persian else "")
    out = Path("results/eval") / f"{ws.settings.corpus}{suffix}.csv"
    if persian:
        write_rows(out.with_name(out.stem + "_translations.csv"),
                   [{"id": it.id, "question_fa": it.question_fa, "translation": translations[it.id],
                     "original_en": it.question} for it in items])
    write_rows(out, rows)
    write_rows(out.with_name(out.stem + "_groups.csv"), groups)
    write_rows(out.with_name(out.stem + "_ranks.csv"),
               [{"id": it.id, "group": it.group, **{r.mode: r.ranks[it.id] for r in reports}} for it in items])
    typer.echo(f"saved {out}")


def _qdrant_retrievers(ws, items, k: int, query_fn=None):
    """Retrievers over the web app's search (Qdrant: stored vectors, server-side BM25, RRF)."""
    from types import SimpleNamespace

    from matrag import qdrant_store

    qc = qdrant_store.client()
    embed = ws.kb.index._embed_model
    texts = sorted({(query_fn or (lambda it: it.question))(it) for it in items})
    typer.echo(f"Embedding {len(texts)} queries...", err=True)
    vectors = {q: embed.get_query_embedding(q) for q in texts}

    class QdrantRetriever:
        def __init__(self, mode):
            self.mode = mode

        def retrieve(self, query):
            points = qdrant_store.search(qc, ws.settings.corpus, query, vectors[query], k, self.mode)
            return [SimpleNamespace(node=SimpleNamespace(metadata=p.payload)) for p in points]

    return lambda m: QdrantRetriever(m.value)


@evaluate_app.command("answers")
def evaluate_answers(
    no_rag: Annotated[bool, typer.Option(help="Also evaluate the LLM without retrieval.")] = True,
    top_k: TopKOption = None,
    limit: Annotated[int | None, typer.Option(help="Only the first N questions (to save API quota).")] = None,
) -> None:
    """Share of answers containing the expected values: RAG vs the LLM alone."""
    from matrag.evaluate import evaluate_answers as run, load_questions, write_rows

    ws = _workspace()
    # Retrieval-only questions (e.g. those built by 'evaluate build-gold') have no expected answer.
    items = [it for it in load_questions(_gold("questions.csv")) if it.gradable][:limit]
    if not items:
        typer.echo("No questions with expected answers in the gold file (retrieval-only questions are skipped).")
        raise typer.Exit(0)
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


@evaluate_app.command("build-gold")
def evaluate_build_gold(
    overwrite: Annotated[bool, typer.Option(help="Replace an existing questions.csv.")] = False,
) -> None:
    """Retrieval questions with a known relevant paper, built from checked data (see matrag.questions):
    refractiveindex.info materials asked three ways (with Persian versions), the papers of the
    nonlinear coefficients and of the formulas read from the collection, and questions the collection
    cannot answer."""
    from matrag.config import get_settings
    from matrag.questions import build_curated, write_questions
    from matrag.references.refractiveindex import book_names

    ws = _workspace()
    s = get_settings()
    path = s.data_dir / s.corpus / "gold" / "questions.csv"
    if path.exists() and not overwrite:
        typer.echo(f"{path} exists (use --overwrite to replace it)")
        return
    if not s.reference_db.exists():
        typer.echo(f"refractiveindex.info database not found: {s.reference_db}", err=True)
        raise typer.Exit(1)
    full_text = {d for d, kind in ws.kb.doc_source_types().items() if kind == "full_text_pdf"}
    names = {m: n for (shelf, _, m), n in book_names(s.reference_db).items() if shelf == "main"}
    # the curated YAML files are read from the repository (data/<corpus>/), next to this program
    corpus_dir = Path(__file__).resolve().parents[2] / "data" / s.corpus
    rows = build_curated(s.reference_db, corpus_dir if corpus_dir.exists() else s.data_dir / s.corpus,
                         full_text, names)
    write_questions(path, rows)
    counts = {}
    for r in rows:
        counts[r["group"]] = counts.get(r["group"], 0) + 1
    typer.echo(f"{len(rows)} questions {counts}; saved {path}")


@evaluate_app.command("generate-questions")
def evaluate_generate_questions(
    n: Annotated[int, typer.Option(help="Number of accepted questions wanted (the file is resumed).")] = 1000,
    seed: Annotated[int, typer.Option(help="Seed of the passage sample.")] = 0,
    workers: Annotated[int, typer.Option(help="Passages sent to the LLM at once (set OLLAMA_NUM_PARALLEL to match).")] = 4,
) -> None:
    """Questions written by the LLM from passages of the papers, saved to gold/generated.csv
    (the passage's paper and pages are the answer). Use a local model on a GPU (Colab)."""
    from matrag.config import get_settings
    from matrag.questions import generate

    ws = _workspace()
    s = get_settings()
    out = s.data_dir / s.corpus / "gold" / "generated.csv"
    typer.echo(f"[{ws.llm_name()}] choosing passages...", err=True)
    total = generate(ws.kb.nodes(), ws.llm(), out, n, seed, on_progress=_echo_progress, workers=workers)
    typer.echo(f"{total} questions in {out}")


@evaluate_app.command("formulas")
def evaluate_formulas(
    limit: Annotated[int | None, typer.Option(help="Process at most N more papers in this run.")] = None,
    run: Annotated[str, typer.Option(help="Name of the run: results go to <corpus>_formula_benchmark[_<run>].jsonl.")] = "",
) -> None:
    """Formula benchmark: extract the dispersion formulas of every paper refractiveindex.info
    takes a formula from, and compare n(λ) with the database (resumes where it stopped)."""
    from matrag.benchmark import summarize
    from matrag.evaluate import write_rows

    ws = _workspace()
    out = Path("results/eval") / f"{ws.settings.corpus}_formula_benchmark{'_' + run if run else ''}.jsonl"
    typer.echo(f"[{ws.settings.corpus} | {ws.llm_name()}]", err=True)
    try:
        rows = ws.formula_benchmark(out, limit, on_progress=_echo_progress)
    except (ValueError, FileNotFoundError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)
    summary = summarize(rows)
    _print_table([summary])
    write_rows(out.with_suffix(".csv"), rows)
    write_rows(out.with_name(out.stem + "_summary.csv"), [summary])
    typer.echo(f"saved {out.with_suffix('.csv')} (one row per paper) and {out.stem}_summary.csv")


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


reference_app = typer.Typer(help="Reference databases: HITRAN and refractiveindex.info.", no_args_is_help=True)
app.add_typer(reference_app, name="reference")


@reference_app.command("hitran")
def reference_hitran(
    records: Annotated[Path, typer.Argument(help="CSV written by 'matrag extract'.")],
    molecule: Annotated[str, typer.Option(help="Molecule formula, e.g. CO2.")],
    nu_min: Annotated[float, typer.Option(help="Wavenumber window start (cm-1); selects the band.")],
    nu_max: Annotated[float, typer.Option(help="Wavenumber window end (cm-1).")],
    isotopologue: Annotated[int, typer.Option(help="HITRAN isotopologue number (1 = most abundant).")] = 1,
    out: Annotated[Path | None, typer.Option("--out", "-o")] = None,
) -> None:
    """Compare extracted line parameters with HITRAN (downloaded with HAPI)."""
    from matrag.evaluate import load_records, write_rows
    from matrag.references.hitran import compare

    rows = compare(load_records(records), molecule, isotopologue, nu_min, nu_max)
    matched = [r for r in rows if r["hitran_value"] != ""]
    if matched:
        _print_table([{k: r[k] for k in ("spectral_position", "property", "value", "hitran_value", "abs_diff", "rel_diff")}
                      for r in matched])
    out = out or records.with_name(records.stem + "_vs_hitran.csv")
    if rows:
        write_rows(out, rows)
    typer.echo(f"{len(matched)}/{len(rows)} values matched to HITRAN lines; saved {out}")


@reference_app.command("optical-candidates")
def reference_optical_candidates(
    database: Annotated[Path, typer.Option(help="refractiveindex.info-database/database folder.")] =
        Path("data/optical/reference/database"),
    out: Annotated[Path, typer.Option("--out", "-o")] = Path("data/optical/candidates.csv"),
) -> None:
    """List the source papers of refractiveindex.info with open-access status (Crossref)."""
    from matrag.evaluate import write_rows
    from matrag.references.refractiveindex import open_access_candidates

    if not database.exists():
        typer.echo("Clone it first: git clone --depth 1 https://github.com/polyanskiy/refractiveindex.info-database "
                   "data/optical/reference", err=True)
        raise typer.Exit(1)
    rows = open_access_candidates(database)
    rows.sort(key=lambda r: (not r.get("open_access"), -(r.get("year") or 0)))
    cols = ["open_access", "year", "authors", "title", "journal", "doi", "arxiv_id", "materials",
            "data_types", "wavelength_um", "citations", "license", "entries"]
    write_rows(out, [{c: r.get(c, "") for c in cols} for r in rows])
    typer.echo(f"{len(rows)} papers ({sum(bool(r.get('open_access')) for r in rows)} open access); saved {out}")


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
