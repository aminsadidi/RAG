from llama_index.core.schema import NodeWithScore, TextNode

from matrag.qa import NOT_FOUND, answer_with_rag, format_context


class FakeRetriever:
    def __init__(self, nodes):
        self.nodes = nodes

    def retrieve(self, question):
        return self.nodes


class FakeLLM:
    def __init__(self):
        self.prompt = None

    def complete(self, prompt):
        self.prompt = prompt
        return type("R", (), {"text": " 0.0712 cm-1 atm-1 [1] "})()


def test_context_numbers_and_labels_sources():
    node = NodeWithScore(node=TextNode(text="γ_air = 0.0712", metadata={"doc_id": "p", "pages": "3", "content_type": "table"}), score=1.0)
    assert format_context([node]) == "[1] (p, p. 3, table)\nγ_air = 0.0712"


def test_answer_with_rag_uses_sources():
    node = NodeWithScore(node=TextNode(text="γ_air = 0.0712", metadata={"doc_id": "p", "pages": "3"}), score=1.0)
    llm = FakeLLM()
    answer = answer_with_rag("γ_air?", FakeRetriever([node]), llm)
    assert answer.text == "0.0712 cm-1 atm-1 [1]" and answer.sources == [node]
    assert "γ_air = 0.0712" in llm.prompt and NOT_FOUND in llm.prompt


def test_no_sources_short_circuits():
    llm = FakeLLM()
    assert answer_with_rag("q", FakeRetriever([]), llm).text == NOT_FOUND
    assert llm.prompt is None
