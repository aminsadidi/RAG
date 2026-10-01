"""OCR the scanned / broken-text target papers (Docling + RapidOCR, full page), caching each conversion."""
import json, os, sys, time
from pathlib import Path
os.environ["MATRAG_FORCE_OCR"] = "true"
from matrag.config import Settings
from matrag.ingest import convert, make_converter

shard, shards = int(sys.argv[1]), int(sys.argv[2])
t = json.load(open("targets.json")); sc = json.load(open("scanned.json"))
todo = sorted(k for k, (why, s) in sc.items() if s or why != "benchmark")
todo = [k for i, k in enumerate(todo) if i % shards == shard]
s = Settings(); conv = make_converter(s)
for k in todo:
    if (Path("cache") / f"{k}.json.gz").exists():
        continue
    t0 = time.time()
    try:
        doc = convert(Path("root") / t[k][1], conv, Path("cache"), k, s.max_pages)
        print(f"{k} ok {len(doc.pages)} pages {time.time() - t0:.0f}s", flush=True)
    except Exception as e:
        print(f"{k} ERROR {type(e).__name__}: {e}", flush=True)
print("DONE", flush=True)
