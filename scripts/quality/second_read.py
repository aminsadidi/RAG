"""A second reading of the tables of OCR'd documents (handbooks, old scans), to find what OCR misread.

Each table passage of a document on the site is cut out of its PDF page (the passage's boxes), sent to a vision model
behind an OpenAI-compatible API, which transcribes it, and the numbers of that transcription are compared with the
numbers of the passage text. The tables where they differ are listed, worst first, for a look at the page (a minus
sign read as 2, a 7 read as 1, a dropped digit). Only ids, pages and counts go to the report; the transcriptions stay
in the cache folder, which is local and resumable (a table already read is not sent again).

    python scripts/quality/second_read.py DOC_ID PDF CACHE_DIR [--model M] [--limit N] [--workers 4]
        (QDRANT_URL, QDRANT_API_KEY; VISION_API_KEY, VISION_BASE_URL)
"""
import argparse
import base64
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import datamap  # noqa: E402

PROMPT = ("Transcribe this table from a scientific book or paper exactly as CSV (first row: the column headers). Keep "
          "every number exactly as printed, with its sign, decimal point and exponent; leave empty cells empty; do not "
          "correct or complete anything. Output only the CSV.")
NUM = re.compile(r"[-−–]?\d+(?:\.\d+)?(?:\s*[×x]\s*10\s*[-−–]?\d+|[eE][-+]?\d+)?")


def numbers(text: str) -> Counter:
    """The numbers of a text, normalized (unicode minus, spaces in exponents), as a multiset."""
    out = Counter()
    for m in NUM.findall(text.replace(",", "")):
        out[re.sub(r"\s+", "", m).replace("−", "-").replace("–", "-")] += 1
    return out


def table_points(doc_id: str) -> list[dict]:
    out, offset = [], None
    while True:
        body = {"limit": 256, "with_payload": ["node_id", "text", "boxes", "content_type"], "with_vector": False,
                "filter": {"must": [{"key": "doc_id", "match": {"value": doc_id}}]}}
        if offset is not None:
            body["offset"] = offset
        r = datamap.qdrant("/collections/rag-optics/points/scroll", body)
        out += [p["payload"] for p in r["points"] if p["payload"].get("content_type") == "table"]
        offset = r.get("next_page_offset")
        if offset is None:
            return out


def crop(pdf, boxes: list, scale: float = 2.8, margin: float = 0.015) -> bytes:
    """PNG of the region of the first page the passage is on (all its boxes on that page), with a margin."""
    page = boxes[0][0]
    on = [b for b in boxes if b[0] == page]
    x0, y0 = max(0, min(b[1] for b in on) - margin), max(0, min(b[2] for b in on) - margin)
    x1, y1 = min(1, max(b[3] for b in on) + margin), min(1, max(b[4] for b in on) + margin)
    im = pdf[page - 1].render(scale=scale).to_pil()
    w, h = im.size
    buf = io.BytesIO()
    im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))).save(buf, "PNG")
    return buf.getvalue()


def ask(png: bytes, model: str) -> str:
    body = {"model": model, "temperature": 0, "messages": [{"role": "user", "content": [
        {"type": "text", "text": PROMPT},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}}]}]}
    url = os.environ.get("VISION_BASE_URL", "https://oxionai.com/v1").rstrip("/") + "/chat/completions"
    for attempt in range(8):  # the service answers 503 while it is upgraded, and 429 when busy: wait and retry
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
                "Authorization": "Bearer " + os.environ["VISION_API_KEY"], "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == 7:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 7:
                raise
        time.sleep(min(300, 15 * 2 ** attempt))
    raise RuntimeError("unreachable")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("doc_id"), ap.add_argument("pdf"), ap.add_argument("cache")
    ap.add_argument("--model", default="gemini-3.1-pro")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    import pypdfium2

    pdf, cache = pypdfium2.PdfDocument(a.pdf), Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)
    tables = [t for t in table_points(a.doc_id) if json.loads(t.get("boxes") or "[]")]
    tables.sort(key=lambda t: int(t["node_id"].split("::")[1]))
    if a.limit:
        tables = tables[: a.limit]
    images = {t["node_id"]: crop(pdf, json.loads(t["boxes"])) for t in tables}  # pdfium is not thread-safe

    def one(t):
        key = hashlib.sha1((a.model + t["node_id"]).encode() + images[t["node_id"]]).hexdigest()[:16]
        f = cache / f"{key}.json"
        if not f.exists():
            f.write_text(json.dumps({"node": t["node_id"], "model": a.model, "csv": ask(images[t["node_id"]], a.model)}))
        csv = json.loads(f.read_text())["csv"]
        ours, theirs = numbers(t["text"]), numbers(csv)
        both = sum((ours & theirs).values())
        return {"node": t["node_id"], "page": json.loads(t["boxes"])[0][0], "numbers": sum(ours.values()),
                "read": sum(theirs.values()), "agree": round(both / max(1, sum(ours.values()), sum(theirs.values())), 3),
                "only_ocr": sum((ours - theirs).values()), "only_second": sum((theirs - ours).values())}

    with ThreadPoolExecutor(a.workers) as ex:
        rows = sorted(ex.map(one, tables), key=lambda r: r["agree"])
    report = {"doc_id": a.doc_id, "model": a.model, "tables": len(rows),
              "agree_all": sum(r["agree"] == 1 for r in rows), "rows": rows}
    (cache / "report.json").write_text(json.dumps(report, indent=1))
    print(f"{a.doc_id}: {len(rows)} tables, {report['agree_all']} read alike; worst:")
    for r in rows[:15]:
        print(f"  p. {r['page']:>4}  agree {r['agree']:.2f}  ({r['only_ocr']} numbers only in OCR, {r['only_second']} only in the second reading)  {r['node']}")


if __name__ == "__main__":
    main()
