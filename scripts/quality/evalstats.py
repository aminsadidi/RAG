"""Statistics for the search evaluations: bootstrap confidence intervals, paired comparisons, the frozen
dev/test split of the gold questions.

With ~200 questions a mean reciprocal rank has a 95% interval about ±0.06 wide: a change of 0.02 between two
runs is noise. Two methods on the same questions are compared with a paired bootstrap (the difference per
question resampled), which is much tighter than comparing two separate intervals.
"""
import csv
import re
import random
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPLIT = ROOT / "data" / "rag-optics" / "gold" / "split.csv"


def bootstrap_ci(values, n: int = 10000, level: float = 0.95, seed: int = 0) -> tuple[float, float, float]:
    """Mean of `values` and its percentile bootstrap interval: (mean, low, high)."""
    values = list(values)
    if not values:
        return (float("nan"),) * 3
    rng, k = random.Random(seed), len(values)
    means = sorted(sum(values[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    lo, hi = means[int((1 - level) / 2 * n)], means[min(n - 1, int((1 + level) / 2 * n))]
    return st.mean(values), lo, hi


def paired_bootstrap(a, b, n: int = 10000, level: float = 0.95, seed: int = 0) -> tuple[float, float, float, float]:
    """b - a on the same questions: (mean difference, low, high, share of resamples where b is not better)."""
    a, b = list(a), list(b)
    if len(a) != len(b):
        raise ValueError("a paired comparison needs the same questions on both sides")
    d = [y - x for x, y in zip(a, b)]
    mean, lo, hi = bootstrap_ci(d, n, level, seed)
    rng, k = random.Random(seed + 1), len(d)
    worse = sum(sum(d[rng.randrange(k)] for _ in range(k)) <= 0 for _ in range(n)) / n if d else float("nan")
    return mean, lo, hi, worse


def rr10(rank: int | None) -> float:
    """Reciprocal rank cut at 10 (the per-question value whose mean is MRR@10)."""
    return 1 / rank if rank and rank <= 10 else 0.0


def load_split(path: Path = SPLIT) -> dict[str, str]:
    """Question id -> "dev" or "test" (frozen; tune on dev, report on test)."""
    with path.open(encoding="utf-8") as f:
        return {r["id"]: r["split"] for r in csv.DictReader(f)}


def ci_text(m: tuple) -> str:
    return f"{m[0]:.3f} [{m[1]:.3f}–{m[2]:.3f}]"


def ri_alternatives(path: Path = ROOT / "data" / "rag-optics" / "paper_formulas.yml") -> dict[str, set[str]]:
    """Material -> papers of the collection whose dispersion formula for it was read by hand (paper_formulas.yml).

    A refractive-index question was graded against the papers refractiveindex.info cites only, so a top hit on
    another paper with a Sellmeier formula for the same crystal counted as a miss. Read with a regex: the CI
    runner's plain python3 has no YAML parser.
    """
    out: dict[str, set[str]] = {}
    material = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if m := re.match(r"- material:\s*(\S+)", line):
            material = m.group(1)
        elif (m := re.match(r"\s+doc_id:\s*(\S+)", line)) and material:
            out.setdefault(material, set()).add(m.group(1))
    return out


def accepted(question_id: str, gold: str, extra: dict[str, set[str]]) -> str:
    """The papers accepted for a question ("a;b"): for an ri question (ri-<material>-<k>) also extra[material]."""
    docs = [d for d in gold.split(";") if d]
    if m := re.fullmatch(r"ri-(.+)-\d+", question_id):
        docs += sorted(extra.get(m.group(1), set()) - set(docs))
    return ";".join(docs)
