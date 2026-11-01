"""Extraction logic with a fake LLM (no API calls)."""

from llama_index.core.schema import TextNode

import math

import pytest

from matrag.extract import deduplicate, extract, normalize, parse_value, save_records, value_checks, value_in_text
from matrag.schema import ExtractionResult, PropertyRecord

TEXT = "The air-broadened half-width of R(10) is 0.0712(3) cm−1 atm−1 at 296 K."


def record(**overrides) -> PropertyRecord:
    fields = dict(
        material="CO2", property="air-broadened half-width", value_text="0.0712(3)", value=0.0712,
        uncertainty=0.0003, unit="cm-1 atm-1", spectral_position="R(10)", temperature_K=296,
        broadener="air", method="experimental", evidence="is 0.0712(3) cm-1 atm-1 at 296 K",
    )
    return PropertyRecord(**(fields | overrides))


class FakeLLM:
    def __init__(self, records):
        self.records = records
        self.calls = 0

    def structured_predict(self, output_cls, prompt, **kwargs):
        self.calls += 1
        assert "air-broadened half-width" in kwargs["properties"]
        return output_cls(records=self.records)


def make_node():
    return TextNode(id_="p::0", text=TEXT, metadata={"doc_id": "p", "pages": "3"})


def test_normalize_handles_unicode_minus_and_spaces():
    assert normalize("cm−1  atm−1") == normalize("cm-1 atm-1") == "cm-1atm-1"


def test_extraction_verifies_against_source():
    real = record()
    invented = record(value_text="0.0800", value=0.08, evidence="0.0800 cm-1 atm-1", spectral_position="R(12)")
    llm = FakeLLM([real, invented])
    out = extract(["air-broadened half-width"], llm, nodes=[make_node()])
    by_value = {r.value: r for r in out}
    assert by_value[0.0712].evidence_verified and by_value[0.0712].value_in_source
    assert not by_value[0.08].evidence_verified and not by_value[0.08].value_in_source
    assert by_value[0.0712].doc_id == "p" and by_value[0.0712].pages == "3"


def test_deduplicate_prefers_verified_copy():
    llm = FakeLLM([record(evidence="not in text"), record()])
    out = extract(["air-broadened half-width"], llm, nodes=[make_node()])
    assert len(out) == 1 and out[0].evidence_verified
    assert deduplicate(out) == out


def test_save_records(tmp_path):
    out = extract(["air-broadened half-width"], FakeLLM([record()]), nodes=[make_node()])
    save_records(out, tmp_path / "x.csv")
    save_records(out, tmp_path / "x.jsonl")
    assert "0.0712(3)" in (tmp_path / "x.csv").read_text()
    assert len((tmp_path / "x.jsonl").read_text().splitlines()) == 1


def test_empty_result_is_valid():
    assert ExtractionResult.model_validate({"records": []}).records == []


@pytest.mark.parametrize("value_text, source, found", [
    ("0.07", "gamma = 0.0712 cm-1", False),     # a prefix of a longer number
    ("2.3", "n = 12.35", False),               # inside a longer number
    ("96 K", "at 296 K", False),
    ("", "anything at all 296 K", False),       # an empty value used to pass everywhere
    ("K", "at 296 K", False),                   # no digit
    ("2", "x 2.5 y", False),
    ("234", "1,234 lines", False),
    ("0.0712", "gamma = 0.0712 cm-1", True),
    ("296 K", "at 296 K.", True),
    ("2.5", "x 2.5. y", True),
    ("0.0712(3)", "is 0.0712(3) cm−1", True),
    ("1.23 × 10^-22", "S = 1.23 × 10^-22 cm", True),
])
def test_value_must_stand_alone_in_the_text(value_text, source, found):
    assert value_in_text(value_text, normalize(source)) is found


@pytest.mark.parametrize("text, number", [
    ("0.0712(3)", 0.0712), ("1.23 × 10^-22", 1.23e-22), ("1.23×10−22", 1.23e-22), ("2.5·10⁻³", 0.0025),
    ("1.5e-4", 1.5e-4), ("−3.2", -3.2), (".5", 0.5), ("1.23 x 10^{-22}", 1.23e-22),
])
def test_value_text_is_parsed(text, number):
    assert math.isclose(parse_value(text), number)


def test_value_text_without_a_number():
    assert parse_value("about") is None and parse_value("") is None


def test_value_must_equal_value_text_and_evidence_must_be_long_enough():
    src = normalize(TEXT)
    assert value_checks(record(), src) == (True, True)
    assert value_checks(record(value=0.07), src)[1] is False             # the float does not say what the text says
    assert value_checks(record(value_text="0.07", value=0.07), src)[1] is False  # "0.07" only inside 0.0712
    assert value_checks(record(evidence="0.0712(3)"), src)[0] is False   # too short to verify anything
    assert value_checks(record(evidence=""), src)[0] is False
