"""Convert this shard's work units of plan.json: units/<doc_id>/<start>-<end>.json.gz (unit by unit, so a
paper's pages can be spread over many shards).

usage: convert.py SHARD
"""
import gzip
import json
import sys
import time
from pathlib import Path

from common import download, site
from matrag import ingest
from matrag.config import Settings

shard = int(sys.argv[1])
plan = json.load(open("plan.json"))
units = [u for u in plan["units"] if u["shard"] == shard]
print(f"shard {shard}: {len(units)} units, {sum(u['end'] - u['start'] + 1 for u in units)} pages", flush=True)
base = Settings(convert_timeout_s=4 * 3600, convert_timeout_per_page_s=0)
converters = {}
session = None
failed = 0
started = time.time()
BUDGET = 5.2 * 3600  # a job may run 6 h; the units left over go to the next run (their paper is skipped now)
for u in sorted(units, key=lambda u: (u["doc_id"], u["start"])):
    if time.time() - started > BUDGET:
        print(f"time budget used up; {u['doc_id']} pages {u['start']}-{u['end']} and later units left", flush=True)
        break
    paper = plan["papers"][u["doc_id"]]
    pdf = Path("inputs" if paper.get("extra") else "pdfs") / f"{u['doc_id']}.pdf"
    if not paper.get("extra"):
        session = session or site()
        if not download(session, paper["source_file"], pdf):
            print(f"{u['doc_id']}: PDF not on the site", flush=True)
            failed += 1
            continue
    if u["mode"] not in converters:
        converters[u["mode"]] = ingest.make_converter(base.model_copy(update={"force_ocr": u["mode"] == "ocr"}))
    target = Path("units") / u["doc_id"] / f"{u['start']:05d}-{u['end']:05d}.json.gz"
    t0 = time.time()
    try:
        doc = ingest._convert_pages(pdf, converters[u["mode"]], (u["start"], u["end"]))
    except Exception as e:  # noqa: BLE001 - one unit's failure must not stop the shard
        print(f"{u['doc_id']} pages {u['start']}-{u['end']}: ERROR {type(e).__name__}", flush=True)
        failed += 1
        continue
    target.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(target, "wt", encoding="utf-8") as f:
        json.dump(doc.export_to_dict(), f)
    print(f"{u['doc_id']} pages {u['start']}-{u['end']} ({u['mode']}): {len(doc.pages)} pages, "
          f"{time.time() - t0:.0f} s", flush=True)
print(f"shard {shard} done; {failed} units failed", flush=True)
