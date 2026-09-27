"""Evaluation against hand-checked reference ("gold") data.

Two gold files per corpus, in ``data/<corpus>/gold/``:

``questions.csv`` -- for retrieval and question answering
    id, question, doc_id, pages, expected
    - pages:    pages holding the answer, e.g. "5" or "5;6"
    - expected: strings the answer must contain, separated by ";";
                alternatives separated by "|", e.g. "1.36" or "323;367" or "twice|two times".
                "NOT_FOUND" marks a question the papers cannot answer: the correct
                reply is the system's "not found" message (a hallucination test).
                Such questions have no doc_id/pages and are skipped for retrieval.

``values.csv`` -- for property extraction
    doc_id, property, value, unit, material, spectral_position, rel_tol
    - rel_tol is the accepted relative difference (default 0.01 = 1 %)

Metrics
    Retrieval:  Recall@k (a gold page of the gold paper is among the top k
                chunks) and MRR (mean reciprocal rank of the first such chunk).
    Answers:    share of answers containing every expected string; share of
                "not found" replies.
    Extraction: a record matches a gold value when doc, property name and
                number (within rel_tol) agree; precision, recall and F1 follow.
"""

import csv
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel

from matrag.extract import normalize
from matrag.qa import NOT_FOUND
from matrag.schema import ExtractedRecord

# --- gold data ---


class GoldQuestion(BaseModel):
    id: str
    question: str
    doc_id: str
    pages: list[int]
    expected: list[list[str]]  # all groups required; any alternative within a group

    @property
    def answerable(self) -> bool:
        return self.expected != [["NOT_FOUND"]]


class GoldValue(BaseModel):
    doc_id: str
    property: str
    value: float
    unit: str = ""
    material: str = ""
    spectral_position: str = ""
    rel_tol: float = 0.01


def load_questions(path: Path) -> list[GoldQuestion]:
    with path.open(encoding="utf-8") as f:
        return [
            GoldQuestion(
                id=row["id"], question=row["question"], doc_id=row.get("doc_id") or "",
                pages=[int(p) for p in re.split(r"[;, ]+", row.get("pages") or "") if p.strip()],
                expected=[[alt.strip() for alt in group.split("|") if alt.strip()]
                          for group in row.get("expected", "").split(";") if group.strip()],
            )
            for row in csv.DictReader(f)
        ]


def load_values(path: Path) -> list[GoldValue]:
    with path.open(encoding="utf-8") as f:
        return [GoldValue(**{k: v for k, v in row.items() if v not in ("", None)}) for row in csv.DictReader(f)]


# --- retrieval ---


def _pages(node) -> set[int]:
    return {int(p) for p in str(node.metadata.get("pages", "")).split(",") if p.strip().isdigit()}


def first_relevant_rank(item: GoldQuestion, hits) -> int | None:
    """1-based rank of the first chunk from the gold paper and a gold page."""
    for rank, hit in enumerate(hits, start=1):
        if hit.node.metadata.get("doc_id") == item.doc_id and _pages(hit.node) & set(item.pages):
            return rank
    return None


@dataclass
class RetrievalReport:
    mode: str
    ranks: dict[str, int | None]
    ks: tuple[int, ...]

    def recall_at(self, k: int) -> float:
        return sum(r is not None and r <= k for r in self.ranks.values()) / max(len(self.ranks), 1)

    @property
    def mrr(self) -> float:
        return sum(1 / r for r in self.ranks.values() if r) / max(len(self.ranks), 1)

    def summary(self) -> dict[str, float | str]:
        return {"mode": self.mode, **{f"recall@{k}": round(self.recall_at(k), 3) for k in self.ks},
                "MRR": round(self.mrr, 3)}


def evaluate_retrieval(items: list[GoldQuestion], retriever, mode: str, ks=(1, 3, 5, 10)) -> RetrievalReport:
    """``retriever`` must return at least max(ks) hits."""
    ranks = {it.id: first_relevant_rank(it, retriever.retrieve(it.question)) for it in items if it.answerable}
    return RetrievalReport(mode, ranks, ks)


# --- answers ---


def is_not_found(answer: str) -> bool:
    return normalize(NOT_FOUND).rstrip(".") in normalize(answer)


def contains_expected(answer: str, expected: list[list[str]]) -> bool:
    if expected == [["NOT_FOUND"]]:
        return is_not_found(answer)
    text = normalize(answer)
    return all(any(normalize(alt) in text for alt in group) for group in expected)


@dataclass
class AnswerReport:
    system: str
    answers: dict[str, str] = field(default_factory=dict)
    correct: dict[str, bool] = field(default_factory=dict)

    unanswerable: set[str] = field(default_factory=set)

    def summary(self) -> dict[str, float | str]:
        answerable = [i for i in self.answers if i not in self.unanswerable]
        rate = lambda ids, fn: round(sum(fn(i) for i in ids) / len(ids), 3) if ids else ""  # noqa: E731
        return {
            "system": self.system,
            "accuracy (answerable)": rate(answerable, lambda i: self.correct[i]),
            "not found (answerable)": rate(answerable, lambda i: is_not_found(self.answers[i])),
            "abstained (unanswerable)": rate(sorted(self.unanswerable), lambda i: self.correct[i]),
        }


def evaluate_answers(items: list[GoldQuestion], answer_fn: Callable[[str], str], system: str,
                     on_item: Callable[[str], None] | None = None) -> AnswerReport:
    report = AnswerReport(system)
    for it in items:
        if on_item:
            on_item(it.id)
        text = answer_fn(it.question)
        report.answers[it.id] = text
        report.correct[it.id] = contains_expected(text, it.expected)
        if not it.answerable:
            report.unanswerable.add(it.id)
    return report


# --- extraction ---


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower().replace("-", " "))) - {"of", "the", "a", "coefficient"}


def property_similarity(a: str, b: str) -> float:
    """Overlap of the word sets of two property names (Jaccard index, 0-1)."""
    ta, tb = _tokens(a), _tokens(b)
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0


def same_property(a: str, b: str, threshold: float = 0.5) -> bool:
    return property_similarity(a, b) >= threshold


_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def same_position(gold: str, extracted: str) -> bool:
    """A numeric gold position (e.g. "0.40") matches any equal number in the extracted text
    ("0.4 µm, 295 K"); other positions (e.g. "R(50)") must appear as text."""
    if _NUMBER.fullmatch(gold.strip()):
        return any(abs(float(x) - float(gold)) <= 1e-9 * max(1.0, abs(float(gold)))
                   for x in _NUMBER.findall(extracted))
    return normalize(gold) in normalize(extracted)


def value_matches(record: ExtractedRecord, gold: GoldValue) -> bool:
    if record.doc_id != gold.doc_id or not same_property(record.property, gold.property):
        return False
    if gold.spectral_position and not same_position(gold.spectral_position, record.spectral_position or ""):
        return False
    return abs(record.value - gold.value) <= gold.rel_tol * abs(gold.value) + 1e-12


@dataclass
class ExtractionReport:
    n_extracted: int
    n_gold: int
    matches: list[tuple[ExtractedRecord, GoldValue]]

    @property
    def precision(self) -> float:
        return len(self.matches) / self.n_extracted if self.n_extracted else 0.0

    @property
    def recall(self) -> float:
        return len(self.matches) / self.n_gold if self.n_gold else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    def summary(self) -> dict[str, float | int]:
        errors = [abs(r.value - g.value) / abs(g.value) for r, g in self.matches if g.value]
        return {"extracted": self.n_extracted, "gold": self.n_gold, "matched": len(self.matches),
                "precision": round(self.precision, 3), "recall": round(self.recall, 3), "F1": round(self.f1, 3),
                "mean_rel_error": round(sum(errors) / len(errors), 5) if errors else 0.0}


def evaluate_extraction(records: Iterable[ExtractedRecord], gold: list[GoldValue]) -> ExtractionReport:
    """One-to-one greedy matching; records are limited to the papers in the gold set."""
    gold_docs = {g.doc_id for g in gold}
    records = [r for r in records if r.doc_id in gold_docs]
    unmatched = list(gold)
    matches = []
    for r in records:
        for g in unmatched:
            if value_matches(r, g):
                matches.append((r, g))
                unmatched.remove(g)
                break
    return ExtractionReport(len(records), len(gold), matches)


def load_records(path: Path) -> list[ExtractedRecord]:
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fields = ExtractedRecord.model_fields
    out = []
    for row in rows:
        # Empty CSV cells: None for optional fields, "" for required text fields.
        clean = {k: v for k, v in row.items() if k in fields and (v != "" or fields[k].is_required())}
        for flag in ("evidence_verified", "value_in_source"):
            clean[flag] = str(row.get(flag, "")).lower() == "true"
        out.append(ExtractedRecord(**clean))
    return out


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
