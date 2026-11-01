"""Shared by the OCR workflow's steps (.github/workflows/ocr.yml): the site, Qdrant and text measures.

Paper text never goes to the log or to an unencrypted artifact (the repository is public): steps print
doc_ids and numbers only.
"""
import os
import re
from pathlib import Path

import requests

NAME = "rag-optics"
SITE = os.environ.get("SITE_URL") or (Path(__file__).resolve().parents[2] / "web" / "site_url.txt").read_text().strip()
PART_PAGES = 40  # pages per work unit; a book is spread over the shards in units
STOP = set("the of and in to is a for with by are was on that as from be this at an which were it we or".split())
DATA = Path(__file__).resolve().parents[2] / "data" / NAME


def quality(texts) -> tuple[int, float]:
    """Characters, and the share of common English words (readable prose: 0.25-0.4, garbled text < 0.12)."""
    words = [w for t in texts for w in re.findall(r"[A-Za-z]+", t)]
    return sum(map(len, texts)), sum(w.lower() in STOP for w in words) / max(1, len(words))


def site() -> requests.Session:
    s = requests.Session()
    # the CI account (SITE_USER/SITE_PASS from the site, web/src/oidc.js), by the login form: no password in a URL
    r = s.post(f"{SITE}/login", data={"username": os.environ.get("SITE_USER", ""), "password": os.environ["SITE_PASS"]},
               allow_redirects=False, timeout=60)
    if r.status_code != 303 or "session" not in s.cookies:
        raise SystemExit(f"site login failed ({r.status_code})")
    return s


def download(session: requests.Session, source_file: str, target: Path) -> bool:
    """The PDF behind the site's /pdf/ link (PDFs over 25 MB are not on the site)."""
    if target.exists():
        return True
    for _ in range(3):
        try:
            r = session.get(f"{SITE}/pdf/{source_file}", timeout=300)
        except requests.RequestException:
            continue
        if r.status_code == 404:
            return False
        if r.ok and r.content[:4] == b"%PDF":
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".tmp")
            tmp.write_bytes(r.content)
            tmp.replace(target)
            return True
    return False


def listed(name: str) -> set[str]:
    path = DATA / f"{name}.txt"
    lines = path.read_text("utf-8").splitlines() if path.exists() else []
    return {line.split("#")[0].strip() for line in lines} - {""}


PAPER_KEYS = ("drive_id", "pdf_mismatch", "conversion")  # paper-level fields the site's old points carry


def full_text_points(qc, doc_id: str) -> list:
    from qdrant_client import models

    points, _ = qc.scroll(NAME, limit=10000, with_payload=True, with_vectors=False, scroll_filter=models.Filter(must=[
        models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id)),
        models.FieldCondition(key="source_type", match=models.MatchValue(value="full_text_pdf"))]))
    return points


def replace_points(qc, doc_id: str, points: list, old: list, ocr: bool = False, batch: int = 64) -> None:
    """Put ``points`` in place of the paper's full-text points ``old`` on the site, never leaving it without text.

    The new points are written first and only then the old ones not among them are deleted, so a failure half
    way leaves the paper with both, not with nothing. Paper-level fields (PAPER_KEYS) come over from the old
    points, and a passage whose text did not change keeps the fields other scripts added (crystals, junk, ...).
    """
    from qdrant_client import models

    from matrag.qdrant_store import ENRICHED_KEYS, text_hash

    ref = old[0].payload if old else {}
    enriched = {text_hash(p.payload.get("text", "")): {k: p.payload[k] for k in ENRICHED_KEYS if k in p.payload}
                for p in old}
    for p in points:
        p.payload.update({k: ref[k] for k in PAPER_KEYS if k in ref})
        p.payload.update(enriched.get(text_hash(p.payload.get("text", "")), {}))
        if ocr:
            p.payload["ocr"] = True
    for i in range(0, len(points), batch):
        qc.upsert(NAME, points=points[i:i + batch], wait=True)
    new = {str(p.id) for p in points}
    stale = [p.id for p in old if str(p.id) not in new]
    if stale:
        qc.delete(NAME, points_selector=models.PointIdsList(points=stale), wait=True)
