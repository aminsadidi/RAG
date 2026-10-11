"""Shared by the OCR workflow's steps (.github/workflows/ocr.yml): the site, Qdrant and text measures.

Paper text never goes to the log or to an unencrypted artifact (the repository is public): steps print
doc_ids and numbers only.
"""
import os
import re
from pathlib import Path

import requests

NAME = "rag-optics"
SITE = os.environ.get("SITE_URL", "https://matrag.ethanjamescarter1995.workers.dev")
PART_PAGES = 40  # pages per work unit; a book is spread over the shards in units
STOP = set("the of and in to is a for with by are was on that as from be this at an which were it we or".split())
DATA = Path(__file__).resolve().parents[2] / "data" / NAME


def quality(texts) -> tuple[int, float]:
    """Characters, and the share of common English words (readable prose: 0.25-0.4, garbled text < 0.12)."""
    words = [w for t in texts for w in re.findall(r"[A-Za-z]+", t)]
    return sum(map(len, texts)), sum(w.lower() in STOP for w in words) / max(1, len(words))


def site() -> requests.Session:
    s = requests.Session()
    r = s.get(f"{SITE}/?key={os.environ['SITE_KEY']}", allow_redirects=False, timeout=60)
    if r.status_code != 303:
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


def full_text_points(qc, doc_id: str) -> list:
    points, _ = qc.scroll(NAME, limit=10000, with_payload=True, with_vectors=False, scroll_filter={"must": [
        {"key": "doc_id", "match": {"value": doc_id}}, {"key": "source_type", "match": {"value": "full_text_pdf"}}]})
    return points
