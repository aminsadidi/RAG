"""Formula extraction logic with a fake LLM."""

import json

from llama_index.core.schema import TextNode

from matrag.dispersion import DispersionFormula, PoleTerm
from matrag.formulas import (
    Candidate, FormulaRecord, compare_with_reference, deduplicate_formulas, extract_from_candidate,
    numbers_in_source, text_candidates,
)
from matrag.references.refractiveindex import Entry, EntryData

BBO_CODE = ("RefracInd_e=sqrt(1+ inputValues.^2 *1.151075 ./ (inputValues.^2 -0.007142) +... "
            "inputValues.^2 *0.21803 ./ (inputValues.^2 -0.02259) +... inputValues.^2 *0.656 ./ (inputValues.^2 -263));")


def bbo_e(**overrides) -> DispersionFormula:
    base = dict(material="BBO", axis="e", constant=1.0, wavelength_min_um=0.188, wavelength_max_um=5.2,
                equation_text=BBO_CODE,
                pole_terms=[PoleTerm(coefficient=b, pole=c) for b, c in [(1.151075, 0.007142), (0.21803, 0.02259), (0.656, 263)]])
    return DispersionFormula(**(base | overrides))


def node(i, text, doc="p"):
    return TextNode(id_=f"{doc}::{i}", text=text, metadata={"doc_id": doc, "pages": "10", "content_type": "text",
                                                             "boxes": json.dumps([[10, 0.1, 0.1, 0.9, 0.2]])})


def test_text_candidates_merge_consecutive_formula_chunks():
    nodes = [node(1, "Introduction without formulas."), node(2, BBO_CODE.replace("_e", "_o")), node(3, BBO_CODE),
             node(9, "A Sellmeier model was used (no numbers).")]
    [c] = text_candidates(nodes)
    assert c.source == "text p::2-3" and "RefracInd_o" in c.text and "RefracInd_e" in c.text
    assert json.loads(c.boxes) == [[10, 0.1, 0.1, 0.9, 0.2]] * 2


def test_numbers_in_source():
    assert numbers_in_source(bbo_e(), BBO_CODE) == 1.0
    invented = bbo_e(pole_terms=[PoleTerm(coefficient=1.2, pole=0.0071)])
    assert numbers_in_source(invented, BBO_CODE) == 0.0
    assert numbers_in_source(bbo_e(), "S1 = 1.151075E+00, 7.142E-03, 0.21803, 2.259e-2, 0.656 and 263") == 1.0


class FakeLLM:
    def __init__(self, formulas):
        self.formulas = formulas

    def structured_predict(self, output_cls, prompt, **kwargs):
        assert "Sellmeier" in kwargs["context"] or kwargs["context"] == "(none)"
        return output_cls(formulas=self.formulas)


def test_extraction_checks_and_reference_comparison():
    candidate = Candidate(doc_id="p", source="text p::3", pages="10", text=BBO_CODE)
    [record] = extract_from_candidate(candidate, "(none)", FakeLLM([bbo_e()]))
    assert record.numbers_in_source == 1.0 and record.problems == []

    entry = Entry("main/BaB2O4/nk/Tamosauskas-e.yml", "main", "BaB2O4", "Tamosauskas-e", "", None, "2111.01212",
                  "formula 2", "0.188-5.2", "")
    same = EntryData(entry, "e", (0.188, 5.2), 2, [0, 1.151075, 0.007142, 0.21803, 0.02259, 0.656, 263], [])
    other_axis = EntryData(entry, "o", (0.188, 5.2), 2, [0, 0.90291, 0.003926, 0.83155, 0.018786, 0.76536, 60.01], [])
    compare_with_reference(record, [other_axis, same])
    assert record.reference_max_dn < 1e-9  # matched the e-ray entry, identical coefficients


def test_deduplicate_keeps_best_supported_copy():
    a = FormulaRecord(formula=bbo_e(), doc_id="p", pages="10", source="matlab", numbers_in_source=0.5)
    b = FormulaRecord(formula=bbo_e(), doc_id="p", pages="14", source="scilab", numbers_in_source=1.0)
    c = FormulaRecord(formula=bbo_e(axis="o"), doc_id="p", pages="10", source="matlab", numbers_in_source=1.0)
    out = deduplicate_formulas([a, b, c])
    assert len(out) == 2 and {r.source for r in out} == {"scilab", "matlab"}
