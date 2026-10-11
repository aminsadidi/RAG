"""Find the papers to convert again and write plan.json: work units of up to PART_PAGES pages, spread
over the shards by estimated time.

  ocr   scanned PDFs: almost no embedded text, or garbled text (full-page OCR)
  full  PDFs whose site text stops early: past the 60-page limit of the usual conversion (books,
        theses, reviews) or cut short by a conversion timeout (no OCR, every page)

Already handled papers are skipped: OCR'd ones (points marked ocr), ones the October OCR run judged
(scripts/ocr_site/report.json) and ones an earlier run of this workflow judged (scripts/ocr_gh/reports).
Extra PDFs (not on the site) come from inputs/<doc_id>.pdf, always with OCR.

usage: scan.py SHARDS [--only doc_id,...]
"""
import json
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pypdfium2

from common import PART_PAGES, quality, site, download, NAME
from matrag import qdrant_store

MAX_PAGES = 60  # Settings.max_pages of the usual conversion
SECONDS = {"ocr": 6.0, "full": 1.5}  # rough time per page on a 4-core runner

shards = int(sys.argv[1])
only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
pdfs = Path("pdfs")

qc = qdrant_store.client()
docs = defaultdict(lambda: {"texts": [], "ocr": False})
offset = None
while True:
    points, offset = qc.scroll(NAME, limit=1000, offset=offset, with_vectors=False, scroll_filter={"must": [
        {"key": "source_type", "match": {"value": "full_text_pdf"}}]},
        with_payload=["doc_id", "text", "source_file", "ocr"])
    for p in points:
        d = docs[p.payload["doc_id"]]
        d["texts"].append(p.payload.get("text", ""))
        d["source_file"] = p.payload.get("source_file")
        d["ocr"] |= bool(p.payload.get("ocr"))
    if offset is None:
        break
here = Path(__file__).parent
done = set(json.load(open(here.parent / "ocr_site" / "report.json")))
for f in (here / "reports").glob("*.json"):  # earlier runs of this workflow
    done |= {k for k, r in json.load(open(f)).items() if "better" in r}
extra = {p.stem: p for p in Path("inputs").glob("*.pdf")} if Path("inputs").exists() else {}
todo = {k: v for k, v in docs.items() if (only is None or k in only) and k not in extra
        and (only is not None or (k not in done and not v["ocr"]))}
print(f"{len(docs)} papers with full text on the site; {len(todo)} to check; {len(extra)} extra PDFs", flush=True)

session = site()


def measure(item):
    doc_id, d = item
    path = pdfs / f"{doc_id}.pdf"
    if not download(session, d["source_file"], path):
        return doc_id, None
    try:
        pdf = pypdfium2.PdfDocument(str(path))
        try:
            texts = [pdf[i].get_textpage().get_text_range() for i in range(len(pdf))]
        finally:
            pdf.close()
    except Exception:
        return doc_id, None
    finally:
        if only is None:
            path.unlink(missing_ok=True)  # the shards download their own; the runner's disk is small
    return doc_id, (len(texts), *quality(texts))


rows, plan = {}, []
with ThreadPoolExecutor(8) as pool:
    for n, (doc_id, m) in enumerate(pool.map(measure, todo.items()), 1):
        if n % 200 == 0:
            print(f"  {n}/{len(todo)} checked", flush=True)
        if m is None:
            continue
        pages, chars, stop = m
        site_chars, _ = quality(todo[doc_id]["texts"])
        if chars < 3000 or chars < 300 * pages or stop < 0.12:
            mode = "ocr"
        elif pages > MAX_PAGES or site_chars < 0.5 * chars:
            mode = "full"
        elif only is not None:
            mode = "full"
        else:
            continue
        rows[doc_id] = {"mode": mode, "pages": pages, "pdf_chars": chars, "pdf_stop": round(stop, 3),
                        "site_chars": site_chars, "source_file": todo[doc_id]["source_file"]}
for doc_id, path in extra.items():
    pdf = pypdfium2.PdfDocument(str(path))
    rows[doc_id] = {"mode": "ocr", "pages": len(pdf), "source_file": None, "extra": True}
    pdf.close()

# Units, longest first, each to the shard with the least work so far.
units = [{"doc_id": k, "mode": r["mode"], "start": s, "end": min(s + PART_PAGES - 1, r["pages"]),
          "cost": (min(s + PART_PAGES - 1, r["pages"]) - s + 1) * SECONDS[r["mode"]]}
         for k, r in rows.items() for s in range(1, r["pages"] + 1, PART_PAGES)]
load = [0.0] * shards
for u in sorted(units, key=lambda u: -u["cost"]):
    u["shard"] = min(range(shards), key=load.__getitem__)
    load[u["shard"]] += u["cost"]
json.dump({"papers": rows, "units": units}, open("plan.json", "w"), indent=1)
by_mode = defaultdict(int)
for r in rows.values():
    by_mode[r["mode"]] += 1
print(f"plan: {dict(by_mode)} papers, {sum(r['pages'] for r in rows.values())} pages, {len(units)} units; "
      f"longest shard about {max(load) / 3600:.1f} h", flush=True)
