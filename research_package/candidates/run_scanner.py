#!/usr/bin/env python3
"""
Task 3: Whole collection paper scanner for NLO crystal candidate passages.
Scans all papers (~2,000 papers: 34 core + scratch + 1,960 drive papers) for:
  (a) d_ij, d_eff, second-order nonlinear coefficients
  (b) dn/dT and thermo-optic formulas / parameters
  (c) Sellmeier dispersion formulas and equations

Features:
  - Broad pattern matching as specified by guidelines
  - Captures verbatim quote (sentence + next line) AND raw_quote
  - Checkpoints after every paper to candidates/scan_checkpoint.json
  - Logs unextractable/failed papers to candidates/scan_failed.md
  - Generates comprehensive candidates/SCAN_SUMMARY.md with:
      - per crystal counts for dij, thermo, sellmeier
      - top 5 most promising papers per crystal with pages
"""

import os
import sys
import json
import re
import glob
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import pypdf
import gdown

BASE_DIR = "/home/aminsadidi11584/RAG"
CANDIDATES_DIR = os.path.join(BASE_DIR, "research_package/candidates")
DATA_DIR = os.path.join(BASE_DIR, "research_package/data")
PAPERS_CORE = "/home/aminsadidi11584/papers_core"
SCRATCH_DIR = os.path.join(BASE_DIR, "research_package/scratch")

os.makedirs(CANDIDATES_DIR, exist_ok=True)
os.makedirs(SCRATCH_DIR, exist_ok=True)

SCAN_DIJ_FILE = os.path.join(CANDIDATES_DIR, "scan_dij.jsonl")
SCAN_THERMO_FILE = os.path.join(CANDIDATES_DIR, "scan_thermo.jsonl")
SCAN_SELLMEIER_FILE = os.path.join(CANDIDATES_DIR, "scan_sellmeier.jsonl")
SUMMARY_MD_FILE = os.path.join(CANDIDATES_DIR, "SCAN_SUMMARY.md")
CHECKPOINT_FILE = os.path.join(CANDIDATES_DIR, "scan_checkpoint.json")
FAILED_MD_FILE = os.path.join(CANDIDATES_DIR, "scan_failed.md")

LOCK = threading.RLock()

# ---------------------------------------------------------------------------
# BROAD PATTERNS AS REQUESTED
# ---------------------------------------------------------------------------
# 1. Thermo-optic:
# dn/dT, dn_o/dT, dn_e/dT, dnx/dT, dny/dT, dnz/dT, ∂n/∂T, "thermo-optic", "thermooptic",
# "thermo-optical", "temperature dependence of the refractive", "temperature-dependent Sellmeier",
# "temperature dispersion", "noncritical phase-matching temperature", "phase-matching temperature",
# "temperature tuning", "×10-5 /°C", "10^-5 K^-1", "10−6 /K", "°C−1", "K−1", etc.
RE_THERMO = re.compile(
    r'(?:dn_?[oexyz]?\s*/\s*dT|∂n/∂T|thermo[- ]?optic(?:al)?|'
    r'temperature\s+dependence\s+of\s+(?:the\s+)?refractive|'
    r'temperature[- ]dependent\s+Sellmeier|temperature\s+dispersion|'
    r'noncritical\s+phase[- ]matching\s+temperature|phase[- ]matching\s+temperature|'
    r'temperature\s+tuning|'
    r'[×x]\s*10[-–]?\d+\s*[/ ]°C|10\^[-–]?\d+\s*K\^?[-–]?1|10[-–−]\d+\s*[/ ]K|'
    r'[°º]C[-–−\^]1|K[-–−\^]1|ppm/K|\bthermal\s+refractive\b)',
    re.IGNORECASE
)

# 2. Nonlinear coefficients d_ij / deff:
# "pm/V", "pmV", "esu", "relative to d36(KDP)", "relative to d11 (quartz)",
# "d_eff", "deff", "nonlinear coefficient", "nonlinear optical coefficient",
# "second-order susceptibility", "χ(2)"
RE_DIJ = re.compile(
    r'(?:pm\s*/\s*V|pm\s*V|\besu\b|'
    r'relative\s+to\s+(?:d_?36\s*\(?KDP\)?|d_?11\s*\(?quartz\)?|KDP|quartz)|'
    r'\bd_?eff\b|\bdeff\b|'
    r'nonlinear\s+(?:optical\s+)?coefficients?|'
    r'second[- ]order\s+(?:nonlinear\s+)?susceptibilit(?:y|ies)|'
    r'χ\(?2\)?|chi\(?2\)?|\bd_?\{?\d{2}\}?\b)',
    re.IGNORECASE
)

# 3. Sellmeier dispersion formulas:
# "Sellmeier", "dispersion formula", "dispersion equation", "n^2 =", "n2 =", "n²(λ)"
RE_SELLMEIER = re.compile(
    r'(?:Sellmeier|dispersion\s+formula|dispersion\s+equation|'
    r'refractive\s+index\s+formula|'
    r'n\^?2\s*=|n2\s*=|n²\s*\(?λ\)?|n\^2\s*\(?λ\)?|n2\s*\(?λ\)?|\bSellmeier\s+coefficients?\b)',
    re.IGNORECASE
)

RE_NUMBER = re.compile(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?')


def load_checkpoint():
    with LOCK:
        if os.path.exists(CHECKPOINT_FILE):
            try:
                with open(CHECKPOINT_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"scanned_ids": [], "total_scanned": 0, "crystal_stats": {}}


def save_checkpoint(ckpt):
    with LOCK:
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(ckpt, f, indent=2)


def append_hit(filepath, record):
    with LOCK:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_failed(doc_id, filename, reason):
    with LOCK:
        file_exists = os.path.exists(FAILED_MD_FILE)
        with open(FAILED_MD_FILE, "a", encoding="utf-8") as f:
            if not file_exists:
                f.write("# Failed Paper Extractions (scan_failed.md)\n\n")
                f.write("| doc_id | File Name | Reason |\n")
                f.write("| :--- | :--- | :--- |\n")
            f.write(f"| `{doc_id}` | `{filename}` | {reason} |\n")


def extract_passage(lines, idx):
    """Extract current sentence/line plus the next line."""
    l1 = lines[idx].strip()
    l2 = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
    raw = lines[idx] + ("\n" + lines[idx + 1] if idx + 1 < len(lines) else "")
    quote = l1 + (" " + l2 if l2 else "")
    return quote[:350], raw[:500]


def scan_single_pdf(pdf_path, meta, ckpt):
    doc_id = meta.get("doc_id") or meta.get("id") or os.path.basename(pdf_path)
    mat = meta.get("material", "Unknown")
    filename = meta.get("filename", os.path.basename(pdf_path))

    try:
        reader = pypdf.PdfReader(pdf_path)
        num_pages = len(reader.pages)
        if num_pages == 0:
            log_failed(doc_id, filename, "Empty PDF (0 pages)")
            return
    except Exception as e:
        log_failed(doc_id, filename, f"pypdf reader error: {str(e)[:80]}")
        return

    extracted_any = False
    dij_pages = []
    thermo_pages = []
    sellm_pages = []
    num_numeric_values = 0

    for page_idx in range(num_pages):
        page_num = page_idx + 1
        try:
            text = reader.pages[page_idx].extract_text() or ""
        except Exception:
            continue

        if not text.strip():
            continue

        extracted_any = True
        lines = text.splitlines()

        # Check Dij
        for idx, line in enumerate(lines):
            line_str = line.strip()
            if len(line_str) < 10:
                continue
            if RE_DIJ.search(line_str):
                quote, raw_quote = extract_passage(lines, idx)
                record = {
                    "task": "dij",
                    "material": mat,
                    "doc_id": doc_id,
                    "pdf_file": filename,
                    "pdf_page": page_num,
                    "label": f"Page {page_num} passage",
                    "quote": quote,
                    "raw_quote": raw_quote,
                    "values": {},
                    "frame_quote": "",
                    "status": "candidate",
                    "note": ""
                }
                append_hit(SCAN_DIJ_FILE, record)
                if page_num not in dij_pages:
                    dij_pages.append(page_num)
                num_numeric_values += len(RE_NUMBER.findall(quote))
                break  # Record top candidate per page

        # Check Thermo
        for idx, line in enumerate(lines):
            line_str = line.strip()
            if len(line_str) < 10:
                continue
            if RE_THERMO.search(line_str):
                quote, raw_quote = extract_passage(lines, idx)
                record = {
                    "task": "thermo",
                    "material": mat,
                    "doc_id": doc_id,
                    "pdf_file": filename,
                    "pdf_page": page_num,
                    "label": f"Page {page_num} passage",
                    "quote": quote,
                    "raw_quote": raw_quote,
                    "values": {},
                    "frame_quote": "",
                    "status": "candidate",
                    "note": ""
                }
                append_hit(SCAN_THERMO_FILE, record)
                if page_num not in thermo_pages:
                    thermo_pages.append(page_num)
                num_numeric_values += len(RE_NUMBER.findall(quote))
                break

        # Check Sellmeier
        for idx, line in enumerate(lines):
            line_str = line.strip()
            if len(line_str) < 10:
                continue
            if RE_SELLMEIER.search(line_str):
                quote, raw_quote = extract_passage(lines, idx)
                record = {
                    "task": "sellmeier",
                    "material": mat,
                    "doc_id": doc_id,
                    "pdf_file": filename,
                    "pdf_page": page_num,
                    "label": f"Page {page_num} passage",
                    "quote": quote,
                    "raw_quote": raw_quote,
                    "values": {},
                    "frame_quote": "",
                    "status": "candidate",
                    "note": ""
                }
                append_hit(SCAN_SELLMEIER_FILE, record)
                if page_num not in sellm_pages:
                    sellm_pages.append(page_num)
                num_numeric_values += len(RE_NUMBER.findall(quote))
                break

    if not extracted_any:
        log_failed(doc_id, filename, "No extractable text found in any page (likely scanned image)")

    with LOCK:
        ckpt["scanned_ids"].append(doc_id)
        ckpt["total_scanned"] += 1

        stats = ckpt["crystal_stats"]
        if mat not in stats:
            stats[mat] = {
                "papers_count": 0,
                "dij_count": 0,
                "thermo_count": 0,
                "sellm_count": 0,
                "dij_pages": {},
                "thermo_pages": {},
                "sellm_pages": {},
                "promising_papers": {}  # doc_id: {"filename": fn, "numeric_count": count, "pages": [...]}
            }

        st = stats[mat]
        st["papers_count"] += 1
        st["dij_count"] += len(dij_pages)
        st["thermo_count"] += len(thermo_pages)
        st["sellm_count"] += len(sellm_pages)

        if dij_pages:
            st["dij_pages"][doc_id] = dij_pages
        if thermo_pages:
            st["thermo_pages"][doc_id] = thermo_pages
        if sellm_pages:
            st["sellm_pages"][doc_id] = sellm_pages

        all_hit_pages = sorted(list(set(dij_pages + thermo_pages + sellm_pages)))
        if all_hit_pages:
            st["promising_papers"][doc_id] = {
                "filename": filename,
                "numeric_count": num_numeric_values,
                "hit_pages": all_hit_pages
            }

        save_checkpoint(ckpt)


def generate_summary_md(ckpt):
    with LOCK:
        stats = ckpt.get("crystal_stats", {})
        total_papers = ckpt.get("total_scanned", 0)

        with open(SUMMARY_MD_FILE, "w", encoding="utf-8") as f:
            f.write("# خلاصه اسکن جامع مقالات اپتیک غیرخطی (Task 3 Summary)\n\n")
            f.write(f"گزارش استخراج کاندیداها از مجموعه مقالات MatRAG (تعداد مقالات اسکن شده: {total_papers}).\n\n")
            f.write("## ۱. آمار قطعات کاندید به تفکیک بلورها\n\n")
            f.write("| نام بلور / رده ماده | مقالات اسکن‌شده | کاندیداهای d_ij | کاندیداهای dn/dT | کاندیداهای Sellmeier | مجموع گزیده‌ها |\n")
            f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")

            sorted_mats = sorted(stats.keys(), key=lambda m: (stats[m]["dij_count"] + stats[m]["thermo_count"] + stats[m]["sellm_count"]), reverse=True)
            for mat in sorted_mats:
                st = stats[mat]
                p_cnt = st["papers_count"]
                d_cnt = st["dij_count"]
                t_cnt = st["thermo_count"]
                s_cnt = st["sellm_count"]
                tot = d_cnt + t_cnt + s_cnt
                f.write(f"| `{mat}` | {p_cnt} | {d_cnt} | {t_cnt} | {s_cnt} | **{tot}** |\n")

            f.write("\n---\n\n## ۲. ۵ مقاله برتر و امیدوارکننده به تفکیک هر بلور (بیشترین چگالی مقادیر عددی)\n\n")
            for mat in sorted_mats:
                st = stats[mat]
                promising = st.get("promising_papers", {})
                if not promising:
                    continue
                sorted_papers = sorted(promising.items(), key=lambda x: x[1].get("numeric_count", 0), reverse=True)[:5]
                f.write(f"### بلور `{mat}`\n")
                f.write("| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |\n")
                f.write("| :--- | :--- | :--- | :---: |\n")
                for pid, pdata in sorted_papers:
                    fn = pdata.get("filename", "")
                    pgs = ", ".join(str(p) for p in pdata.get("hit_pages", [])[:8])
                    nc = pdata.get("numeric_count", 0)
                    f.write(f"| `{pid}` | `{fn}` | ص {pgs} | {nc} |\n")
                f.write("\n")

            f.write("\n---\n*ثبت لحظه‌ای در فایل‌های `scan_dij.jsonl`، `scan_thermo.jsonl` و `scan_sellmeier.jsonl` تکمیل شد.*\n")


def run_collection_scan(batch_limit=200):
    ckpt = load_checkpoint()
    scanned_set = set(ckpt["scanned_ids"])

    # 1. Scan core PDFs
    core_files = sorted(glob.glob(os.path.join(PAPERS_CORE, "*.pdf")))
    for cf in core_files:
        fn = os.path.basename(cf)
        doc_id = fn.replace(".pdf", "")
        if doc_id in scanned_set or fn in scanned_set:
            continue
        meta = {"doc_id": doc_id, "filename": fn, "material": fn.split(".")[0].split("-")[0]}
        scan_single_pdf(cf, meta, ckpt)

    # 2. Scan scratch PDFs
    scratch_files = sorted(glob.glob(os.path.join(SCRATCH_DIR, "*.pdf")))
    for sf in scratch_files:
        fn = os.path.basename(sf)
        doc_id = fn.replace(".pdf", "")
        if doc_id in scanned_set or fn in scanned_set or "tmp" in fn:
            continue
        meta = {"doc_id": doc_id, "filename": fn, "material": "scratch"}
        scan_single_pdf(sf, meta, ckpt)

    # 3. Scan Drive papers manifest
    manifest_path = os.path.join(DATA_DIR, "drive_papers_manifest.json")
    if not os.path.exists(manifest_path):
        print("Manifest not found!")
        return

    manifest = json.load(open(manifest_path))
    pending = [m for m in manifest if m["id"] not in scanned_set and m["filename"] not in scanned_set and m["filename"].replace(".pdf", "") not in scanned_set]
    batch = pending[:batch_limit]
    print(f"Starting batch of {len(batch)} Drive papers (Remaining pending: {len(pending)})...")

    def process_item(item):
        tid = threading.get_ident()
        tmp_pdf = os.path.join(SCRATCH_DIR, f"scan_{tid}.pdf")
        try:
            if os.path.exists(tmp_pdf):
                try:
                    os.remove(tmp_pdf)
                except Exception:
                    pass
            gdown.download(id=item["id"], output=tmp_pdf, quiet=True)
            if os.path.exists(tmp_pdf) and os.path.getsize(tmp_pdf) > 400:
                scan_single_pdf(tmp_pdf, item, ckpt)
            else:
                log_failed(item["id"], item["filename"], "Download returned empty or failed file")
                with LOCK:
                    ckpt["scanned_ids"].append(item["id"])
                    save_checkpoint(ckpt)
            if os.path.exists(tmp_pdf):
                try:
                    os.remove(tmp_pdf)
                except Exception:
                    pass
        except Exception as e:
            log_failed(item["id"], item["filename"], f"Exception: {str(e)[:80]}")
            with LOCK:
                ckpt["scanned_ids"].append(item["id"])
                save_checkpoint(ckpt)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_item, item) for item in batch]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception:
                pass

    generate_summary_md(ckpt)
    print(f"Batch complete! Total scanned so far: {ckpt['total_scanned']}")


if __name__ == "__main__":
    b_limit = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    run_collection_scan(b_limit)
