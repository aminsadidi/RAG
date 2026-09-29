"""Evaluation sets built from refractiveindex.info, and the formula benchmark loop."""

import json
from types import SimpleNamespace

from matrag.benchmark import paper_row, retrieval_questions, summarize
from matrag.evaluate import GoldQuestion, first_relevant_rank


def entry(material, path):
    return SimpleNamespace(entry=SimpleNamespace(material=material, path=path))


def hit(doc_id, pages):
    return SimpleNamespace(node=SimpleNamespace(metadata={"doc_id": doc_id, "pages": pages}))


def test_retrieval_questions_accept_any_cited_paper_and_page():
    refs = {"10.1364_a": [entry("BaB2O4", "main/BaB2O4/nk/A-o.yml")],
            "10.1364_b": [entry("BaB2O4", "main/BaB2O4/nk/B-e.yml"), entry("LiB3O5", "main/LiB3O5/nk/B.yml")]}
    questions = {q.id: q for q in retrieval_questions(refs)}
    assert questions["rii-BaB2O4"].doc_id == "10.1364_a;10.1364_b" and "BaB2O4" in questions["rii-BaB2O4"].question
    assert not questions["rii-LiB3O5"].gradable  # retrieval only: no expected answer
    q = questions["rii-BaB2O4"]
    assert first_relevant_rank(q, [hit("other", "1"), hit("10.1364_b", "7")]) == 2
    # Gold questions with pages still require one of those pages.
    paged = GoldQuestion(id="x", question="?", doc_id="d", pages=[3], expected=[["1"]])
    assert first_relevant_rank(paged, [hit("d", "1,2"), hit("d", "3")]) == 2


def test_paper_rows_and_summary():
    refs = [entry("BaB2O4", "main/BaB2O4/nk/A-o.yml")]
    close = SimpleNamespace(reference_max_dn=2e-4)
    far = SimpleNamespace(reference_max_dn=0.05)
    rows = [paper_row("a", "A (2000)", refs, [far, close]),
            paper_row("b", "B (2001)", refs, [far]),
            paper_row("c", "C (2002)", refs, [])]
    assert rows[0]["best_max_dn"] == 2e-4 and rows[0]["within_0.001"] and not rows[0]["within_0.0001"]
    assert rows[2]["best_max_dn"] is None and not rows[2]["within_0.01"]
    s = summarize(rows)
    assert s["papers"] == 3 and s["formula extracted"] == 0.667 and s["|Δn| ≤ 0.001"] == 0.333


def test_formula_benchmark_resumes(settings, tmp_path, monkeypatch):
    from matrag.pipeline import Workspace

    ws = Workspace(settings, corpus="bench")
    refs = {"p1": [entry("BaB2O4", "e1")], "p2": [entry("LiNbO3", "e2")]}
    monkeypatch.setattr(ws, "formula_references", lambda: refs)
    calls = []

    def fake_extract(doc_ids, provider=None, references=None):
        calls.append(doc_ids[0])
        if doc_ids[0] == "p2":
            raise KeyboardInterrupt  # a disconnect in the middle of the run
        return []

    monkeypatch.setattr(ws, "extract_formulas", fake_extract)
    out = tmp_path / "bench.jsonl"
    try:
        ws.formula_benchmark(out)
    except KeyboardInterrupt:
        pass
    assert [json.loads(line)["doc_id"] for line in out.read_text().splitlines()] == ["p1"]
    monkeypatch.setattr(ws, "extract_formulas", lambda doc_ids, provider=None, references=None: [])
    rows = ws.formula_benchmark(out)  # continues with p2 only
    assert [r["doc_id"] for r in rows] == ["p1", "p2"] and calls == ["p1", "p2"]
