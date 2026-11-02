"""Statistics of the search evaluation (scripts/quality/evalstats.py) and the frozen dev/test split."""

import csv
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "quality"))
import evalstats as E  # noqa: E402


def test_bootstrap_interval_holds_the_mean_and_narrows_with_more_questions():
    rng = random.Random(1)
    small = [rng.random() for _ in range(50)]
    big = small * 8
    m, lo, hi = E.bootstrap_ci(small, n=2000)
    assert lo < m < hi
    _, lo2, hi2 = E.bootstrap_ci(big, n=2000)
    assert hi2 - lo2 < (hi - lo) / 2
    assert E.bootstrap_ci([0.5] * 10, n=200) == (0.5, 0.5, 0.5)


def test_paired_bootstrap_sees_a_small_consistent_gain_that_separate_intervals_hide():
    rng = random.Random(2)
    a = [rng.random() for _ in range(200)]
    b = [x + 0.03 for x in a]
    d, lo, hi, worse = E.paired_bootstrap(a, b, n=2000)
    assert d == pytest.approx(0.03) and lo > 0 and worse == 0
    _, alo, ahi = E.bootstrap_ci(a, n=2000)
    _, blo, bhi = E.bootstrap_ci(b, n=2000)
    assert blo < ahi  # the two separate intervals overlap
    with pytest.raises(ValueError):
        E.paired_bootstrap([1], [1, 2])


def test_rr10():
    assert [E.rr10(r) for r in (1, 2, 10, 11, None)] == [1, 0.5, 0.1, 0, 0]


def test_split_is_frozen_and_covers_every_gold_question():
    split = E.load_split()
    assert set(split.values()) == {"dev", "test"}
    ids = [r["id"] for f in ("questions.csv", "generated.csv")
           for r in csv.DictReader(open(ROOT / "data/rag-optics/gold" / f, encoding="utf-8")) if r.get("doc_id")]
    assert set(ids) <= set(split)
    # dev is the 200 questions the site was tuned on (search_eval's old seed-0 sample): test never was
    rows = [r for f in ("questions.csv", "generated.csv")
            for r in csv.DictReader(open(ROOT / "data/rag-optics/gold" / f, encoding="utf-8")) if r.get("doc_id")]
    random.Random(0).shuffle(rows)
    assert {r["id"] for r in rows[:200]} == {i for i, s in split.items() if s == "dev"}


def test_ri_questions_also_accept_papers_with_a_formula_for_the_material():
    extra = E.ri_alternatives()
    assert {"10.1063_1.360499", "10.1109_3.362711"} <= extra["LiB3O5"]
    got = E.accepted("ri-LiB3O5-2", "10.1364_josab.6.000616", extra).split(";")
    assert got[0] == "10.1364_josab.6.000616" and "10.1109_3.362711" in got
    assert E.accepted("dij-LiB3O5", "x", extra) == "x"  # other groups unchanged
    assert E.accepted("ri-Unknown-1", "a;b", extra) == "a;b"
