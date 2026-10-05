import csv

from matrag.questions import _merge, _split_name, acceptable, candidate_passages, generate, NOT_FOUND
from matrag.evaluate import group_summaries, load_questions, RetrievalReport


def test_split_name():
    assert _split_name("LiB3O5", "LiB3O5 (Lithium triborate, LBO)") == ("LiB3O5", "Lithium triborate", "LBO")
    assert _split_name("Ag", "Ag (Silver)") == ("Ag", "Silver", "")
    assert _split_name("X", "") == ("X", "", "")


def test_merge_same_question_from_two_papers():
    rows = [{"question": "q", "doc_id": "a", "pages": "10"}, {"question": "q", "doc_id": "b", "pages": "2"}]
    assert _merge(rows) == [{"question": "q", "doc_id": "a;b", "pages": "2;10"}]


def test_acceptable_rejects_copies_and_references():
    passage = "The Sellmeier coefficients of LBO were measured at room temperature with a prism of 30 degrees."
    assert acceptable("What dispersion coefficients describe lithium triborate near 1 micron?", passage)
    assert not acceptable("What does the table show about LBO crystals in general?", passage)
    assert not acceptable("Were the Sellmeier coefficients of LBO were measured at room temperature?", passage)
    assert not acceptable("LBO?", passage)


class _Node:
    def __init__(self, i, doc, text, kind="text"):
        self.node_id = f"{doc}::{i}"
        self.metadata = {"doc_id": doc, "source_type": "full_text_pdf", "content_type": kind, "pages": "3",
                         "citation": doc, "reference": "A. (2000). A title. J."}
        self._text = text

    def get_content(self):
        return self._text


class _LLM:
    def __init__(self, replies):
        self.replies = iter(replies)

    def complete(self, prompt):
        class R:
            text = next(self.replies)
        return R()


def test_generate_writes_and_resumes(tmp_path):
    text = "Values 1.234 and 2.345 and 3.456 were found for the refractive index of KTP. " * 5
    nodes = [_Node(i, f"doc{i}", text) for i in range(3)]
    good = '{"question": "Which refractive index values were found for potassium titanyl phosphate?", ' \
           '"question_fa": "ضریب شکست KTP؟", "answer": "1.234"}'
    out = tmp_path / "generated.csv"
    assert generate(nodes, _LLM([good, "no json", good]), out, n=5) == 2
    assert len(candidate_passages(nodes)) == 3
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert {r["pages"] for r in rows} == {"3"} and rows[0]["group"] == "generated-text"
    # a second run skips the passages already tried (accepted or rejected)
    assert generate(nodes, _LLM([]), out, n=5) == 2


def test_group_summaries(tmp_path):
    path = tmp_path / "q.csv"
    path.write_text("id,group,question,doc_id,pages,expected\nri-a-1,ri,q1,a,,\nnone-01,none,q2,,,NOT_FOUND\n"
                    "dij-x,,q3,b,,\n", encoding="utf-8")
    items = load_questions(path)
    assert [it.group for it in items] == ["ri", "none", "dij"]
    rep = RetrievalReport("hybrid", {"ri-a-1": 1, "dij-x": None}, (1,))
    rows = {r["group"]: r for r in group_summaries(rep, items)}
    assert rows["ri"]["MRR"] == 1 and rows["dij"]["MRR"] == 0 and rows["all"]["questions"] == 2
    assert len(NOT_FOUND) == 40
