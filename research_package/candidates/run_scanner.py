#!/usr/bin/env python3
"""
Task 3: Whole collection candidate scanner for MatRAG.
Scans papers page-by-page and records candidate passages for:
  (a) d_ij or d_eff values with pm/V (or esu, or "relative to KDP/quartz") -> scan_dij.jsonl
  (b) dn/dT or thermo-optic formulas -> scan_thermo.jsonl
  (c) Sellmeier equations with coefficients -> scan_sellmeier.jsonl
Also generates candidates/SCAN_SUMMARY.md
"""

import os
import sys
import json
import re
import glob
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pypdf
import gdown

CANDIDATES_DIR = "/home/aminsadidi11584/RAG/research_package/candidates"
SCRATCH_DIR = "/home/aminsadidi11584/.gemini/antigravity-cli/brain/f17647dd-8096-4ef7-aa21-ecebc5ff42f7/scratch"
DATA_DIR = "/home/aminsadidi11584/RAG/research_package/data"
PAPERS_CORE = "/home/aminsadidi11584/papers_core"
WEB_DIR = "/home/aminsadidi11584/RAG/web/src"

os.makedirs(CANDIDATES_DIR, exist_ok=True)
os.makedirs(SCRATCH_DIR, exist_ok=True)

SCAN_DIJ_FILE = os.path.join(CANDIDATES_DIR, "scan_dij.jsonl")
SCAN_THERMO_FILE = os.path.join(CANDIDATES_DIR, "scan_thermo.jsonl")
SCAN_SELLMEIER_FILE = os.path.join(CANDIDATES_DIR, "scan_sellmeier.jsonl")
SUMMARY_MD_FILE = os.path.join(CANDIDATES_DIR, "SCAN_SUMMARY.md")
CHECKPOINT_FILE = os.path.join(CANDIDATES_DIR, "scan_checkpoint.json")

LOCK = threading.RLock()

# Regex patterns for candidates
RE_DIJ = re.compile(
    r'(?:d_?\{?\d{2}\}?|d_?eff|deff|nonlinear\s+(?:optical\s+)?coefficient|second[- ]order\s+nonlinear)'
    r'[^.\n;]{0,120}?'
    r'(?:\d+(?:\.\d+)?\s*(?:pm\s*/\s*V|pm\s*V|esu|10\^[-–]?\d+\s*esu)|relative\s+to\s+(?:KDP|quartz|alpha-quartz))',
    re.IGNORECASE
)

RE_THERMO = re.compile(
    r'(?:dn_?[oexyz]?\s*/\s*dT|thermo[- ]optic\s+(?:dispersion\s+)?(?:coefficient|formula|constants?)|thermal\s+refractive\s+index)'
    r'[^.\n;]{0,120}?'
    r'(?:10\^[-–]?\d+|×\s*10|\bppm/K\b|\/°C|\/K|°C\^[-–]1|K\^[-–]1)',
    re.IGNORECASE
)

RE_SELLMEIER = re.compile(
    r'(?:Sellmeier\s+(?:equation|dispersion|formula)|dispersion\s+formula|refractive\s+index\s+formula|temperature[- ]dependent\s+Sellmeier)'
    r'[^.\n;]{0,140}?'
    r'(?:n\^?2|λ\^?2|lambda\^?2|\d+\.\d+)',
    re.IGNORECASE
)


def load_checkpoint():
    with LOCK:
        if os.path.exists(CHECKPOINT_FILE):
            try:
                with open(CHECKPOINT_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"scanned_ids": [], "total_scanned": 0, "stats": {}}


def save_checkpoint(ckpt):
    with LOCK:
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(ckpt, f, indent=2)


def append_hit(filepath, record):
    with LOCK:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def scan_single_pdf(pdf_path, meta, ckpt, crystal_stats):
    doc_id = meta.get("doc_id") or meta.get("id") or os.path.basename(pdf_path)
    mat = meta.get("material", "Unknown")
    filename = meta.get("filename", os.path.basename(pdf_path))

    try:
        reader = pypdf.PdfReader(pdf_path)
        num_pages = len(reader.pages)
    except Exception as e:
        return 0, 0, 0

    dij_hits = 0
    thermo_hits = 0
    sellm_hits = 0

    dij_pages = []
    thermo_pages = []
    sellm_pages = []

    for page_idx in range(num_pages):
        page_num = page_idx + 1
        try:
            text = reader.pages[page_idx].extract_text() or ""
        except Exception:
            continue

        if not text:
            continue

        # Split into readable sentences or table rows
        lines = text.splitlines()

        # (a) Check dij
        for line in lines:
            line_str = line.strip()
            if len(line_str) < 15:
                continue
            if RE_DIJ.search(line_str) or (any(k in line_str.lower() for k in ["pm/v", "esu", "relative to kdp"]) and any(k in line_str.lower() for k in ["d36", "d31", "d22", "d14", "d15", "d24", "d32", "d33", "deff", "d_eff"])):
                record = {
                    "task": "dij",
                    "material": mat,
                    "doc_id": doc_id,
                    "pdf_file": filename,
                    "pdf_page": page_num,
                    "label": f"Page {page_num} passage",
                    "quote": line_str[:250],
                    "values": {},
                    "frame_quote": "",
                    "status": "candidate",
                    "note": ""
                }
                append_hit(SCAN_DIJ_FILE, record)
                dij_hits += 1
                if page_num not in dij_pages:
                    dij_pages.append(page_num)
                break  # Record top candidate per page to avoid flooding

        # (b) Check thermo
        for line in lines:
            line_str = line.strip()
            if len(line_str) < 15:
                continue
            if RE_THERMO.search(line_str) or (any(k in line_str.lower() for k in ["dn/dt", "dno/dt", "dne/dt", "thermo-optic"]) and any(k in line_str.lower() for k in ["10-5", "10-6", "10^-5", "10^-6", "/°c", "/k", "ppm/k"])):
                record = {
                    "task": "thermo",
                    "material": mat,
                    "doc_id": doc_id,
                    "pdf_file": filename,
                    "pdf_page": page_num,
                    "label": f"Page {page_num} passage",
                    "quote": line_str[:250],
                    "values": {},
                    "frame_quote": "",
                    "status": "candidate",
                    "note": ""
                }
                append_hit(SCAN_THERMO_FILE, record)
                thermo_hits += 1
                if page_num not in thermo_pages:
                    thermo_pages.append(page_num)
                break

        # (c) Check sellmeier
        for line in lines:
            line_str = line.strip()
            if len(line_str) < 15:
                continue
            if RE_SELLMEIER.search(line_str) or ("sellmeier" in line_str.lower() and re.search(r'n\^?2|λ\^?2|\d+\.\d+', line_str)):
                record = {
                    "task": "sellmeier",
                    "material": mat,
                    "doc_id": doc_id,
                    "pdf_file": filename,
                    "pdf_page": page_num,
                    "label": f"Page {page_num} passage",
                    "quote": line_str[:250],
                    "values": {},
                    "frame_quote": "",
                    "status": "candidate",
                    "note": ""
                }
                append_hit(SCAN_SELLMEIER_FILE, record)
                sellm_hits += 1
                if page_num not in sellm_pages:
                    sellm_pages.append(page_num)
                break

    with LOCK:
        ckpt["scanned_ids"].append(doc_id)
        ckpt["total_scanned"] += 1
        save_checkpoint(ckpt)

        if mat not in crystal_stats:
            crystal_stats[mat] = {
                "papers_count": 0,
                "dij_pages": [],
                "thermo_pages": [],
                "sellm_pages": []
            }
        crystal_stats[mat]["papers_count"] += 1
        crystal_stats[mat]["dij_pages"].extend(dij_pages)
        crystal_stats[mat]["thermo_pages"].extend(thermo_pages)
        crystal_stats[mat]["sellm_pages"].extend(sellm_pages)

    return dij_hits, thermo_hits, sellm_hits


def generate_summary_md(crystal_stats, total_papers):
    with open(SUMMARY_MD_FILE, "w", encoding="utf-8") as f:
        f.write("# خلاصه اسکن جامع مقالات اپتیک غیرخطی (Task 3 Summary)\n\n")
        f.write(f"گزارش استخراج کاندیداها از مجموعه مقالات MatRAG (تعداد مقالات اسکن شده: {total_papers}).\n\n")
        f.write("| نام بلور / ماده | مقالات اسکن‌شده | صفحات کاندید d_ij | صفحات کاندید dn/dT | صفحات کاندید Sellmeier | مجموع گزیده‌ها |\n")
        f.write("| :--- | :---: | :--- | :--- | :--- | :---: |\n")

        sorted_mats = sorted(crystal_stats.keys(), key=lambda m: crystal_stats[m]["papers_count"], reverse=True)
        for mat in sorted_mats:
            st = crystal_stats[mat]
            p_cnt = st["papers_count"]
            d_p = ", ".join(str(p) for p in sorted(list(set(st["dij_pages"])))[:5]) or "-"
            if len(set(st["dij_pages"])) > 5:
                d_p += f" (+{len(set(st['dij_pages']))-5})"
            t_p = ", ".join(str(p) for p in sorted(list(set(st["thermo_pages"])))[:5]) or "-"
            if len(set(st["thermo_pages"])) > 5:
                t_p += f" (+{len(set(st['thermo_pages']))-5})"
            s_p = ", ".join(str(p) for p in sorted(list(set(st["sellm_pages"])))[:5]) or "-"
            if len(set(st["sellm_pages"])) > 5:
                s_p += f" (+{len(set(st['sellm_pages']))-5})"
            tot = len(st["dij_pages"]) + len(st["thermo_pages"]) + len(st["sellm_pages"])
            f.write(f"| `{mat}` | {p_cnt} | {d_p} | {t_p} | {s_p} | **{tot}** |\n")

        f.write("\n\n---\n*ثبت لحظه‌ای در فایل‌های `scan_dij.jsonl`، `scan_thermo.jsonl` و `scan_sellmeier.jsonl` تکمیل شد.*\n")
    print(f"Generated {SUMMARY_MD_FILE}")


def run_collection_scan(max_papers=300):
    ckpt = load_checkpoint()
    scanned_set = set(ckpt["scanned_ids"])
    crystal_stats = {}

    # 1. First scan all available local PDFs in papers_core
    core_files = glob.glob(os.path.join(PAPERS_CORE, "*.pdf"))
    print(f"Scanning {len(core_files)} core PDFs...")
    for cf in core_files:
        fn = os.path.basename(cf)
        if fn in scanned_set:
            continue
        meta = {"doc_id": fn.replace(".pdf", ""), "filename": fn, "material": fn.split(".")[0]}
        scan_single_pdf(cf, meta, ckpt, crystal_stats)

    # 2. Scan scratch downloaded PDFs
    scratch_files = glob.glob(os.path.join(SCRATCH_DIR, "*.pdf"))
    print(f"Scanning {len(scratch_files)} scratch PDFs...")
    for sf in scratch_files:
        fn = os.path.basename(sf)
        if fn in scanned_set:
            continue
        meta = {"doc_id": fn.replace(".pdf", ""), "filename": fn, "material": fn.split(".")[0]}
        scan_single_pdf(sf, meta, ckpt, crystal_stats)

    # 3. Scan Drive papers manifest
    manifest = json.load(open(os.path.join(DATA_DIR, "drive_papers_manifest.json")))
    pending = [m for m in manifest if m["id"] not in scanned_set and m["filename"] not in scanned_set][:max_papers]
    print(f"Scanning batch of {len(pending)} Drive papers...")

    def process_drive_item(item):
        tid = threading.get_ident()
        tmp_pdf = os.path.join(SCRATCH_DIR, f"scan_tmp_{tid}.pdf")
        try:
            if os.path.exists(tmp_pdf):
                try:
                    os.remove(tmp_pdf)
                except Exception:
                    pass
            gdown.download(id=item["id"], output=tmp_pdf, quiet=True)
            if os.path.exists(tmp_pdf) and os.path.getsize(tmp_pdf) > 500:
                scan_single_pdf(tmp_pdf, item, ckpt, crystal_stats)
            if os.path.exists(tmp_pdf):
                try:
                    os.remove(tmp_pdf)
                except Exception:
                    pass
        except Exception as e:
            with LOCK:
                ckpt["scanned_ids"].append(item["id"])
                save_checkpoint(ckpt)

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(process_drive_item, item) for item in pending]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception:
                pass

    generate_summary_md(crystal_stats, ckpt["total_scanned"])
    print(f"Scan complete! Total papers scanned: {ckpt['total_scanned']}")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    run_collection_scan(max_papers=count)
