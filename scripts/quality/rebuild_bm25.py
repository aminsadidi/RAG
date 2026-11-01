"""Rebuild the BM25 vectors of the passages whose formula normalization changed (qdrant_store._SPACED_FORMULA
now reads word characters and digits as ASCII, like the site). Only the sparse vector of those points is
rewritten: text, dense vector and payload (enrichment included) stay as they are. Nothing is printed but counts.

    python scripts/quality/rebuild_bm25.py [--dry]    (QDRANT_URL, QDRANT_API_KEY)
"""
import re
import sys

from qdrant_client import models

from matrag import qdrant_store as qs

NAME = "rag-optics"
# the rule the collection's BM25 vectors were built with until 2026-11
OLD = re.compile(r"\b(?:[A-Z][a-z]?)+(?:\s+\d{1,3}(?:\s+(?:[A-Z][a-z]?)+(?![a-z]))?)+(?![\w.])")


def old_normalize(text: str) -> str:
    def join(m):
        s = m.group(0)
        return re.sub(r"\s+", "", s) if sum(c.isupper() for c in s) >= 2 else s

    return OLD.sub(join, text.translate(qs._DIGITS))


def changed(points) -> list:
    return [p for p in points if old_normalize(p.payload.get("text", "")) != qs.normalize_formulas(p.payload.get("text", ""))]


def rebuild(qc, name: str = NAME, dry: bool = False, batch: int = 64) -> tuple[int, int]:
    """(points read, points rewritten)."""
    seen, todo, offset = 0, [], None
    while True:
        points, offset = qc.scroll(name, limit=1000, offset=offset, with_payload=["text"], with_vectors=False)
        seen += len(points)
        todo += changed(points)
        if offset is None:
            break
    if not dry:
        for i in range(0, len(todo), batch):
            qc.update_vectors(name, points=[models.PointVectors(id=p.id, vector={qs.SPARSE: qs.sparse_vector(p.payload["text"])})
                                            for p in todo[i:i + batch]], wait=True)
    return seen, len(todo)


if __name__ == "__main__":
    seen, n = rebuild(qs.client(), dry="--dry" in sys.argv)
    print(f"{n} of {seen} passages {'would get' if '--dry' in sys.argv else 'got'} a new BM25 vector")
