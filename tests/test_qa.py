from llama_index.core.schema import NodeWithScore, TextNode

from matrag.qa import NOT_FOUND, answer_with_rag, build_context_pack, format_context


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


def test_context_pack_is_the_rag_prompt_plus_notes():
    node = NodeWithScore(node=TextNode(text="γ_air = 0.0712", metadata={"doc_id": "p", "pages": "3"}), score=1.0)
    text = build_context_pack("γ_air?", [node], {"corpus": "hitran"}, language="Persian")
    assert "[1] (p, p. 3)\nγ_air = 0.0712" in text
    assert "Write the answer in Persian" in text
    assert text.index("Question: γ_air?") < text.index("- corpus: hitran")


class TranslatingLLM(FakeLLM):
    def complete(self, prompt):
        if prompt.startswith("Translate this question"):
            return type("R", (), {"text": "What is γ_air?\n"})()
        return super().complete(prompt)


class RecordingRetriever(FakeRetriever):
    def retrieve(self, question):
        self.query = question
        return self.nodes


def test_persian_detection():
    from matrag.qa import is_persian

    assert is_persian("ضریب پهن‌شدگی γ_air چقدر است؟") and not is_persian("What is γ_air?")


def test_persian_question_is_translated_for_retrieval_only():
    from matrag.qa import translate_query

    llm = TranslatingLLM()
    question = "ضریب γ_air چقدر است؟"
    query = translate_query(question, llm)
    node = NodeWithScore(node=TextNode(text="γ_air = 0.0712", metadata={"doc_id": "p", "pages": "3"}), score=1.0)
    retriever = RecordingRetriever([node])
    answer = answer_with_rag(question, retriever, llm, "Persian", query)
    assert retriever.query == "What is γ_air?"  # search in English
    assert question in llm.prompt and "(English translation: What is γ_air?)" in llm.prompt
    assert "Write the answer in Persian" in llm.prompt and answer.search_query == query
