from llama_index.core.schema import NodeWithScore, TextNode

from matrag.evaluate import (
    GoldValue, contains_expected, evaluate_answers, evaluate_extraction, evaluate_retrieval,
    load_questions, same_property,
)
from matrag.qa import NOT_FOUND
from matrag.schema import ExtractedRecord

GOLD_CSV = """id,question,doc_id,pages,expected
q1,What is the CH4 scaling factor?,paper,10,1.36
q2,At which temperatures?,paper,5;6,323;367
q3,Unanswerable question?,,,NOT_FOUND
"""


def hit(doc_id, pages):
    return NodeWithScore(node=TextNode(text="x", metadata={"doc_id": doc_id, "pages": pages}), score=1.0)


class FakeRetriever:
    def __init__(self, hits):
        self.hits = hits

    def retrieve(self, question):
        return self.hits[question]


def test_load_questions(tmp_path):
    path = tmp_path / "q.csv"
    path.write_text(GOLD_CSV, encoding="utf-8")
    items = load_questions(path)
    assert items[1].pages == [5, 6] and items[1].expected == [["323"], ["367"]]
    assert items[2].doc_id == "" and not items[2].answerable


def test_retrieval_metrics(tmp_path):
    path = tmp_path / "q.csv"
    path.write_text(GOLD_CSV, encoding="utf-8")
    items = load_questions(path)
    retriever = FakeRetriever({
        items[0].question: [hit("other", "10"), hit("paper", "9,10")],  # relevant at rank 2
        items[1].question: [hit("paper", "1")],  # not found
    })
    report = evaluate_retrieval(items, retriever, "hybrid", ks=(1, 3))
    assert report.ranks == {"q1": 2, "q2": None}  # q3 (unanswerable) is skipped
    assert report.recall_at(1) == 0 and report.recall_at(3) == 0.5 and report.mrr == 0.25


def test_answer_metrics(tmp_path):
    path = tmp_path / "q.csv"
    path.write_text(GOLD_CSV, encoding="utf-8")
    items = load_questions(path)
    answers = {items[0].question: "A factor of 1.36 was used [1].",
               items[1].question: "At 323 K only.",
               items[2].question: NOT_FOUND}
    summary = evaluate_answers(items, answers.get, "rag").summary()
    assert summary["accuracy (answerable)"] == 0.5
    assert summary["abstained (unanswerable)"] == 1.0
    assert contains_expected("twice as large", [["twice", "two times"]])


def record(**kw) -> ExtractedRecord:
    base = dict(material="CO2", property="air-broadened half-width", value_text="0.0712", value=0.0712,
                evidence="", doc_id="p", node_id="p::0", pages="3", evidence_verified=True, value_in_source=True)
    return ExtractedRecord(**(base | kw))


def test_extraction_metrics():
    gold = [GoldValue(doc_id="p", property="air-broadened half width", value=0.0712),
            GoldValue(doc_id="p", property="air-broadened half width", value=0.0698)]
    records = [record(), record(value=0.0712, value_text="0.0712"),  # duplicate: only one can match
               record(value=0.0800), record(doc_id="elsewhere")]  # wrong value; paper not in gold
    report = evaluate_extraction(records, gold)
    assert (report.n_extracted, len(report.matches)) == (3, 1)
    assert round(report.precision, 3) == 0.333 and report.recall == 0.5


def test_property_name_matching():
    assert same_property("air-broadened Lorentz half-width", "air-broadened half width")
    assert not same_property("line intensity", "air-broadened half-width")


def test_numeric_spectral_position():
    from matrag.evaluate import same_position

    assert same_position("0.40", "0.4 µm, 295 K") and same_position("0.40", "0.40 microns")
    assert not same_position("0.40", "4.0 µm")
    assert same_position("R(50)", "R(50) of the 20012-00001 band")
