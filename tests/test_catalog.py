"""A linked paper collection (the RAG-Optics folder layout), offline."""

import json
import shutil

import pytest

from matrag import catalog, pipeline
from matrag.catalog import doi_key, load_catalog, plan, shard_of
from matrag.pipeline import Workspace, link_collection, list_corpora

CSV_HEADER = "﻿category,material,year,title,authors,journal,doi,status,drive_path\n"


@pytest.fixture
def collection(tmp_path, sample_paper, monkeypatch):
    """A collection with: a PDF found by its index path, a DOI-named PDF, a PDF missing from the index,
    a duplicate, an entry with only an abstract and one with only a title."""
    monkeypatch.setattr(catalog, "PAPER_SUFFIXES", (".pdf", ".md"))  # the fixture paper is Markdown
    root = tmp_path / "RAG-Optics"
    folder = root / "01_Papers_by_Category" / "01_Borates" / "BBO"
    folder.mkdir(parents=True)
    shutil.copy(sample_paper, folder / "2004_Smith_air_broadening_1a2b3c.md")
    shutil.copy(sample_paper, folder / "10.1364_josab.6.000616.md")
    shutil.copy(sample_paper, folder / "10.1364_JOSAB.6.000616 (1).md")  # a second copy, differently named
    shutil.copy(sample_paper, root / "01_Papers_by_Category" / "uploaded_notes.md")
    for ignored in ("_cards", "_RAG_processed"):
        (root / ignored).mkdir(parents=True, exist_ok=True)
        shutil.copy(sample_paper, root / ignored / "card.md")
    index = root / "02_Master_Index"
    index.mkdir()
    rows = [
        {"category": "01_Borates", "material": "BBO", "year": "2004", "title": "Air-broadening of CO2",
         "authors": "Jane Smith; Ali Rezaei", "journal": "JQSRT", "doi": "10.1016/j.jqsrt.2004.01.001",
         "status": "downloaded", "drive_path": "01_Papers_by_Category/01_Borates/BBO/2004_Smith_air_broadening_1a2b3c.md",
         "abstract": "Air-broadened half-widths were measured."},
        {"category": "01_Borates", "material": "BBO", "year": "1989", "title": "New nonlinear-optical crystal: LiB3O5",
         "authors": "Chuangtian Chen; Yicheng Wu", "journal": "JOSA B", "doi": "10.1364/JOSAB.6.000616",
         "status": "paywalled", "drive_path": "", "abstract": ""},
        {"category": "01_Borates", "material": "BBO", "year": "1986", "title": "Optical properties of BBO",
         "authors": "D. Eimerl", "journal": "J. Appl. Phys.", "doi": "10.1063/1.337833", "status": "paywalled",
         "drive_path": "", "abstract": "Sellmeier equations of beta-barium borate are reported.",
         "tldr": "Sellmeier fit for BBO."},
        {"category": "01_Borates", "material": "BBO", "year": "", "title": "Growth of borate crystals",
         "authors": "", "journal": "", "doi": "10.1000/xyz", "status": "paywalled", "drive_path": "", "abstract": ""},
        {"category": "01_Borates", "material": "BBO", "year": "1989", "title": "duplicate row",
         "authors": "", "journal": "", "doi": "10.1364/josab.6.000616", "status": "", "drive_path": ""},
    ]
    (index / "papers_master_with_abstracts.jsonl").write_text("\n".join(json.dumps(r) for r in rows), "utf-8")
    return root


def test_doi_key():
    assert doi_key("10.1364/JOSAB.6.000616") == "10.1364_josab.6.000616"
    assert doi_key("10.1002/(SICI)1097-4628") == "10.1002_sici_1097_4628"


def test_catalog_reads_csv_with_bom_and_splits_authors(tmp_path):
    (tmp_path / "02_Master_Index").mkdir()
    (tmp_path / "02_Master_Index" / "papers_master.csv").write_text(
        CSV_HEADER + '01_Borates,BBO,1989,"LBO, a new crystal","Chuangtian Chen; Yicheng Wu",JOSA B,'
                     "10.1364/josab.6.000616,paywalled,\n", "utf-8")
    [entry] = load_catalog(tmp_path)
    assert entry.category == "01_Borates" and entry.year == 1989 and entry.authors == ["Chuangtian Chen", "Yicheng Wu"]
    info = entry.paper_info(entry.key)
    assert info.short_citation() == "Chen & Wu (1989)" and info.source == "catalog"


def test_plan_pairs_pdfs_with_the_index(collection):
    result = plan(collection)
    items = {it.doc_id: it for it in result.items}
    smith = items["10.1016_j.jqsrt.2004.01.001"]  # matched by its stored path
    assert smith.pdf.name.startswith("2004_Smith") and smith.source_type == "full_text_pdf"
    lbo = items["10.1364_josab.6.000616"]  # matched by its DOI file name; the index's duplicate row is dropped
    assert lbo.pdf.name == "10.1364_josab.6.000616.md" and lbo.entry.title.startswith("New nonlinear")
    assert [p.name for p in result.duplicates] == ["10.1364_JOSAB.6.000616 (1).md"]
    assert items["10.1063_1.337833"].source_type == "abstract" and items["10.1063_1.337833"].pdf is None
    assert items["10.1000_xyz"].source_type == "metadata_only"
    assert items["uploaded_notes"].entry is None  # a PDF not in the index is still indexed
    # Cards and conversions are not papers.
    assert all("card" not in str(it.pdf) for it in result.items)
    assert len(result.items) == 5


def test_shards_split_the_papers_exactly_once():
    ids = [f"paper_{i}" for i in range(200)]
    shards = [shard_of(d, 4) for d in ids]
    assert shards == [shard_of(d, 4) for d in ids]  # stable
    assert set(shards) == {0, 1, 2, 3}


def test_workspace_on_a_linked_collection(collection, settings, embed_model, tokenizer, monkeypatch):
    import matrag.ingest

    monkeypatch.setattr(pipeline, "_embed_model", lambda *a: embed_model)
    real_chunker = matrag.ingest.make_chunker
    monkeypatch.setattr(matrag.ingest, "make_chunker", lambda s, t=None: real_chunker(s, tokenizer))
    settings = settings.model_copy(update={"fetch_metadata": False})
    link_collection("optics", collection, settings)
    assert "optics" in list_corpora(settings)
    ws = Workspace(settings, corpus="optics")
    assert ws.settings.processed_dir == collection.resolve() / "_RAG_processed" / "docling"

    # Two parallel workers convert disjoint halves; together they cover every PDF.
    counts = [ws.convert_shard(i, 2) for i in range(2)]
    assert sum(c["converted"] for c in counts) == 3 and sum(c["failed"] for c in counts) == 0
    assert ws.convert_shard(0, 2)["converted"] == 0  # re-running skips finished papers
    assert ws.status()["pdfs_converted"] == 3

    results = ws.ingest()
    assert not [r for r in results if r.error]
    sources = ws.kb.doc_source_types()
    assert sources["10.1063_1.337833"] == "abstract" and sources["10.1364_josab.6.000616"] == "full_text_pdf"
    assert ws.library.get("10.1364_josab.6.000616").short_citation() == "Chen & Wu (1989)"
    [abstract] = ws.kb.nodes(["10.1063_1.337833"])
    assert "Sellmeier equations" in abstract.get_content() and abstract.metadata["material"] == "BBO"
    assert ws.source_image(abstract.node_id) is None  # no page to show for an abstract
    chunk = ws.kb.nodes(["10.1016_j.jqsrt.2004.01.001"])[0]
    assert chunk.metadata["source_file"] == "01_Papers_by_Category/01_Borates/BBO/2004_Smith_air_broadening_1a2b3c.md"
    assert all(r.skipped for r in ws.ingest())  # nothing changed

    hits = ws.retriever(top_k=3).retrieve("Sellmeier equations of beta-barium borate")
    assert any(h.node.metadata["doc_id"] == "10.1063_1.337833" for h in hits)
    assert ws.retriever(top_k=3) is ws.retriever(top_k=3)  # reused until the database changes

    # A PDF arriving for a paper known only by its abstract replaces the abstract.
    folder = collection / "01_Papers_by_Category" / "01_Borates" / "BBO"
    shutil.copy(folder / "10.1364_josab.6.000616.md", folder / "10.1063_1.337833.md")
    [new] = [r for r in ws.ingest() if not r.skipped]
    assert new.chunks > 1 and ws.kb.doc_source_types()["10.1063_1.337833"] == "full_text_pdf"

    # Pruning drops papers that left the collection.
    (collection / "01_Papers_by_Category" / "uploaded_notes.md").unlink()
    ws.ingest(prune=True)
    assert "uploaded_notes" not in ws.kb.doc_ids()


def test_organize_sorts_downloads_into_category_folders(collection, sample_paper):
    from matrag.catalog import organize

    downloads = collection / "05_Downloaded_PDFs"
    downloads.mkdir()
    shutil.copy(sample_paper, downloads / "10.1063-1.337833.md")  # '/' written as '-'
    shutil.copy(sample_paper, downloads / "10.9999-unknown.md")
    (collection / "04_Dispersion_Formulas_Data").mkdir()
    shutil.copy(sample_paper, collection / "04_Dispersion_Formulas_Data" / "10.1063-1.337833.md")

    before = sorted(p.relative_to(collection) for p in collection.rglob("*.md"))
    dry = organize(collection, move=False)
    assert sorted(p.relative_to(collection) for p in collection.rglob("*.md")) == before  # dry run changes nothing

    rows = {r["doc_id"]: r for r in organize(collection, move=True, reference_dois={"10.1063/1.337833"})}
    assert len(rows) == len(dry)
    eimerl = rows["10.1063_1.337833"]
    assert eimerl["file"] == "01_Papers_by_Category/01_Borates/BBO/10.1063-1.337833.md"
    assert eimerl["moved_from"] == "05_Downloaded_PDFs/10.1063-1.337833.md" and eimerl["in_refractiveindex"]
    assert rows["10.9999-unknown"]["file"] == "01_Papers_by_Category/99_Not_in_master_index/10.9999-unknown.md"
    assert not rows["uploaded_notes"]["moved_from"]  # already inside the papers folder
    assert not rows["10.1016_j.jqsrt.2004.01.001"]["moved_from"]  # stored by the harvester
    dup = [r for r in rows.values() if r["kind"] == "duplicate"]
    assert [r["file"] for r in dup] == ["01_Papers_by_Category/98_Duplicate_copies/10.1364_JOSAB.6.000616 (1).md"]
    # Nothing was deleted, the reference data stayed where it was, and a report was written.
    assert len(list(collection.rglob("*.md"))) == len(before)
    assert (collection / "04_Dispersion_Formulas_Data" / "10.1063-1.337833.md").exists()
    assert (collection / "02_Master_Index" / "pdf_inventory.csv").exists()
    # Running again moves nothing.
    assert not [r for r in organize(collection, move=True) if r["moved_from"]]


def test_parallel_chunking_gives_the_same_chunks(collection, settings, embed_model, monkeypatch):
    """Worker processes produce exactly the chunks and metadata of the sequential path."""
    pytest.importorskip("transformers")
    try:  # the real tokenizer, from the local cache (no download in tests)
        from transformers import AutoTokenizer

        AutoTokenizer.from_pretrained(settings.embed_model, local_files_only=True)
    except Exception:
        pytest.skip("embedding model's tokenizer not cached locally")
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setattr(pipeline, "_embed_model", lambda *a: embed_model)
    monkeypatch.setattr(pipeline, "PARALLEL_MIN_PAPERS", 1)
    settings = settings.model_copy(update={"fetch_metadata": False})
    indexed = {}
    for corpus, workers in (("sequential", 1), ("parallel", 2)):
        link_collection(corpus, collection, settings)
        ws = Workspace(settings.model_copy(update={"ingest_workers": workers}), corpus=corpus)
        ws.convert_shard(0, 1)
        assert not [r for r in ws.ingest() if r.error]
        indexed[corpus] = [(n.node_id, n.get_content(), n.metadata) for n in ws.kb.nodes()]
    assert indexed["parallel"] == indexed["sequential"] and len(indexed["parallel"]) > 5


def test_failed_conversions_are_skipped_until_retried(collection, settings, monkeypatch):
    import matrag.ingest

    def broken(*a, **k):
        raise RuntimeError("damaged PDF")

    link_collection("optics", collection, settings)
    ws = Workspace(settings, corpus="optics")
    monkeypatch.setattr(matrag.ingest, "convert", broken)
    assert ws.convert_shard(0, 1)["failed"] == 3
    assert ws.convert_shard(0, 1)["failed"] == 0  # recorded: not retried by default
    assert ws.status()["pdfs_failed"] == 3
    assert ws.convert_shard(0, 1, retry_failed=True)["failed"] == 3
