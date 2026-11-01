"""Extraction logic with a fake LLM (no API calls)."""

from llama_index.core.schema import TextNode

from matrag.extract import deduplicate, extract, normalize, save_records
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


def test_value_must_stand_alone_in_the_source():
    from matrag.extract import number_in, value_checked

    src = normalize("values 0.0712 and 12.35 measured at 296 K, n = 2 .5")
    assert not number_in("0.07", src)       # a prefix of 0.0712
    assert not number_in("2.3", src)        # inside 12.35
    assert not number_in("96 K", src)       # inside 296 K
    assert not number_in("", src) and not number_in("K", src)  # no digit: never verified
    assert number_in("0.0712", src) and number_in("12.35", src) and number_in("296 K", src)
    # the recorded float must be the number written
    assert value_checked(0.0712, "0.0712", src)
    assert not value_checked(0.08, "0.0712", src)


def test_value_text_is_parsed():
    from matrag.extract import parse_number, value_checked

    assert parse_number("0.0712(3)") == 0.0712
    assert abs(parse_number("1.23 × 10^-22") - 1.23e-22) < 1e-30
    assert abs(parse_number("1.23·10⁻²²") - 1.23e-22) < 1e-30
    assert abs(parse_number("4.5e-3") - 4.5e-3) < 1e-12
    assert parse_number("about") is None
    assert value_checked(1.23e-22, "1.23 × 10^-22", normalize("S = 1.23 × 10^-22 cm/molecule"))


def test_evidence_needs_twenty_characters():
    from matrag.extract import evidence_checked

    src = normalize(TEXT)
    assert not evidence_checked("", src) and not evidence_checked("0.0712", src)
    assert evidence_checked("is 0.0712(3) cm-1 atm-1 at 296 K", src)
