"""The OCR workflow replaces a paper's text without leaving it textless when a write fails (scripts/ocr_gh)."""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "ocr_gh"))
import common  # noqa: E402


class FakeQdrant:
    def __init__(self, ids, fail_at=None):
        self.ids, self.fail_at, self.calls = set(ids), fail_at, []

    def upsert(self, name, points, wait):
        self.calls.append("upsert")
        if self.fail_at is not None and len(self.calls) > self.fail_at:
            raise RuntimeError("network")
        self.ids |= {p.id for p in points}

    def delete(self, name, points_selector, wait):
        self.calls.append("delete")
        self.ids -= set(points_selector.points)


def pt(i, **payload):
    return SimpleNamespace(id=i, payload=payload)


def test_new_points_first_then_only_the_stale_old_ones():
    old = [pt("a", basis_p="experimental", pdf_mismatch=True, crystals=["X"]), pt("b"), pt("c")]
    new = [pt("b")] + [pt(f"n{i}") for i in range(70)]
    qc = FakeQdrant(["a", "b", "c"])
    common.swap_points(qc, old, new)
    assert qc.calls == ["upsert", "upsert", "delete"]
    assert qc.ids == {"b"} | {f"n{i}" for i in range(70)}
    assert all(p.payload["basis_p"] == "experimental" and p.payload["pdf_mismatch"] for p in new)


def test_a_failed_upsert_keeps_the_old_text():
    old = [pt("a"), pt("b")]
    qc = FakeQdrant(["a", "b"], fail_at=1)
    with pytest.raises(RuntimeError):
        common.swap_points(qc, old, [pt(f"n{i}") for i in range(100)])
    assert "delete" not in qc.calls and {"a", "b"} <= qc.ids
