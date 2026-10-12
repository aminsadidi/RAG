"""OCR each part PDF of the Dmitriev handbook (pNNNNN-MMMMM.pdf, global page range in the name) into
units/NNNNN-MMMMM.json.gz; parts already converted are skipped."""
import gzip, json, sys, time
from pathlib import Path
from matrag import ingest
from matrag.config import Settings
root = Path(sys.argv[1])
conv = ingest.make_converter(Settings(force_ocr=True, convert_timeout_s=6 * 3600, convert_timeout_per_page_s=0))
for pdf in sorted(root.glob("p*.pdf")):
    target = root / "units" / f"{pdf.stem[1:]}.json.gz"
    if target.exists():
        continue
    t0 = time.time()
    doc = ingest._convert_pages(pdf, conv, (1, 10**6))
    tmp = target.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(doc.export_to_dict(), f)
    tmp.replace(target)
    print(f"{pdf.name}: {len(doc.pages)} pages, {len(doc.texts)} texts, {time.time() - t0:.0f} s", flush=True)
print("DONE", flush=True)
