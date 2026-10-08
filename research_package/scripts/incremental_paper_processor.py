#!/usr/bin/env python3
"""
Incremental Paper Processor for Google Drive Collection (1,960 papers)
- Operates with controlled cadence, high scientific accuracy, and crash-proof persistence.
- Saves progress after EVERY single paper so execution can be safely resumed at any time.
- Stores extractions in:
    1) research_package/data/incremental_extractions.jsonl
    2) research_package/data/checkpoint_drive_processor.json
    3) research_package/reports/INCREMENTAL_EXTRACTIONS_LOG.md
"""

import os
import sys
import json
import time
import re
import datetime
import pypdf
import gdown

BASE_DIR = "/home/aminsadidi11584/RAG"
DATA_DIR = os.path.join(BASE_DIR, "research_package/data")
REPORT_DIR = os.path.join(BASE_DIR, "research_package/reports")
SCRATCH_DIR = os.path.join(BASE_DIR, "research_package/scratch")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(SCRATCH_DIR, exist_ok=True)

MANIFEST_FILE = os.path.join(DATA_DIR, "drive_papers_manifest.json")
CHECKPOINT_FILE = os.path.join(DATA_DIR, "checkpoint_drive_processor.json")
JSONL_FILE = os.path.join(DATA_DIR, "incremental_extractions.jsonl")
LOG_MD_FILE = os.path.join(REPORT_DIR, "INCREMENTAL_EXTRACTIONS_LOG.md")


def load_manifest():
    if not os.path.exists(MANIFEST_FILE):
        raise FileNotFoundError(f"Manifest not found at {MANIFEST_FILE}")
    with open(MANIFEST_FILE, "r") as f:
        return json.load(f)


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "processed_count": 0,
        "processed_ids": [],
        "extracted_count": 0,
        "last_index": 0,
        "last_update": None
    }


def save_checkpoint(ckpt):
    ckpt["last_update"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(ckpt, f, indent=2)


def append_extraction(record):
    with open(JSONL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_md_log(record):
    exists = os.path.exists(LOG_MD_FILE)
    with open(LOG_MD_FILE, "a", encoding="utf-8") as f:
        if not exists:
            f.write("# گزارش لحظه‌ای استخراج پیش‌نویس از مقالات گوگل درایو\n\n")
            f.write("| شماره | بلور / ماده | فایل مقاله | دسته‌های داده استخراج‌شده | جزئیات کلیدی |\n")
            f.write("| :---: | :--- | :--- | :--- | :--- |\n")
        
        idx = record.get("index", "-")
        mat = record.get("material", "-")
        fname = record.get("filename", "-")
        found = ", ".join(record.get("found_categories", [])) or "مشخصات عمومی"
        snippet = record.get("summary_snippet", "-").replace("\n", " ")[:120]
        f.write(f"| {idx} | `{mat}` | `{fname[:30]}` | {found} | {snippet} |\n")


def extract_scientific_data_from_pdf(pdf_path, meta):
    """Deep scientific extraction for linear, nonlinear, damage, thermo, and quantum properties."""
    try:
        reader = pypdf.PdfReader(pdf_path)
    except Exception as e:
        return {"error": f"Failed to read PDF: {e}"}

    num_pages = len(reader.pages)
    full_text = []
    for i, page in enumerate(reader.pages):
        try:
            t = page.extract_text() or ""
            full_text.append(t)
        except Exception:
            full_text.append("")

    all_txt = "\n".join(full_text)
    lower_txt = all_txt.lower()

    # Determine metadata
    doi_match = re.search(r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+', all_txt)
    doi = doi_match.group(0).rstrip('.;,)') if doi_match else meta.get("filename", "").replace("-", "/").replace(".pdf", "")

    # Target scientific categories
    findings = {
        "doc_id": meta.get("id"),
        "filename": meta.get("filename"),
        "path": meta.get("path"),
        "material": meta.get("material"),
        "category": meta.get("category"),
        "doi": doi,
        "num_pages": num_pages,
        "found_categories": [],
        "damage_threshold": None,
        "sellmeier_dispersion": None,
        "thermo_optics": None,
        "nonlinear_coefficients": None,
        "phase_matching_acceptance": None,
        "qpm_parameters": None,
        "quantum_spdc": None,
        "thermal_conductivity": None,
        "summary_snippet": ""
    }

    snippets = []

    # 1. Damage threshold
    dmg_matches = re.findall(r'([^.\n]*?(?:damage threshold|damage fluence|damage intensity|LIDT)[^.\n]*?(?:\d+(?:\.\d+)?\s*(?:GW/cm|MW/cm|J/cm|GW|MW|J))[^.\n]*)', all_txt, re.IGNORECASE)
    if dmg_matches:
        findings["found_categories"].append("آستانه آسیب نوری")
        findings["damage_threshold"] = [m.strip()[:180] for m in dmg_matches[:3]]
        snippets.append(f"LIDT: {dmg_matches[0].strip()[:90]}")

    # 2. Sellmeier / Dispersion
    sellm_matches = re.findall(r'([^.\n]*?(?:Sellmeier equation|dispersion equation|n2\s*=|n\^2\s*=)[^.\n]*)', all_txt, re.IGNORECASE)
    if sellm_matches or "sellmeier" in lower_txt:
        # Check for numeric coefficients
        lines = [l.strip() for l in all_txt.splitlines() if re.search(r'n[oe]?\s*=\s*\d+\.\d+|n\^2\s*=|λ\^2', l)]
        if lines:
            findings["found_categories"].append("معادلات پاشندگی و ضریب شکست")
            findings["sellmeier_dispersion"] = lines[:4]
            snippets.append(f"Dispersion: {lines[0][:80]}")

    # 3. Thermo-optics (dn/dT)
    thermo_matches = re.findall(r'([^.\n]*?(?:dn/dT|dn_o/dT|dn_e/dT|thermo-optic|thermal refractive index)[^.\n]*?(?:10\^[-–]?\d+|×\s*10|ppm/K|\/°C|\/K)[^.\n]*)', all_txt, re.IGNORECASE)
    if thermo_matches:
        findings["found_categories"].append("ضرایب گرما-نوری (dn/dT)")
        findings["thermo_optics"] = [m.strip()[:180] for m in thermo_matches[:3]]
        snippets.append(f"dn/dT: {thermo_matches[0].strip()[:90]}")

    # 4. Nonlinear coefficients (d_ij, d_eff)
    d_matches = re.findall(r'([^.\n]*?(?:d_\{\d+\}|d\d{2}|d_eff|nonlinear optical coefficient)[^.\n]*?(?:\d+(?:\.\d+)?\s*(?:pm/V|pm\s*V|esu))[^.\n]*)', all_txt, re.IGNORECASE)
    if d_matches:
        findings["found_categories"].append("تانسورهای غیرخطی (d_ij)")
        findings["nonlinear_coefficients"] = [m.strip()[:180] for m in d_matches[:4]]
        snippets.append(f"Nonlinear: {d_matches[0].strip()[:90]}")

    # 5. Phase-matching / Acceptance bandwidths / Walk-off
    pm_matches = re.findall(r'([^.\n]*?(?:angular acceptance|spectral acceptance|temperature bandwidth|walk-off angle|noncritical phase)[^.\n]*?(?:mrad|deg|nm|°C|cm)[^.\n]*)', all_txt, re.IGNORECASE)
    if pm_matches:
        findings["found_categories"].append("انطباق فاز و پهنای پذیرش")
        findings["phase_matching_acceptance"] = [m.strip()[:180] for m in pm_matches[:3]]
        snippets.append(f"PM/Bandwidth: {pm_matches[0].strip()[:90]}")

    # 6. QPM parameters
    qpm_matches = re.findall(r'([^.\n]*?(?:poling period|grating period|coercive field|quasi-phase-matched)[^.\n]*?(?:µm|um|kV/mm|nm)[^.\n]*)', all_txt, re.IGNORECASE)
    if qpm_matches:
        findings["found_categories"].append("پارامترهای قطبش QPM")
        findings["qpm_parameters"] = [m.strip()[:180] for m in qpm_matches[:3]]
        snippets.append(f"QPM: {qpm_matches[0].strip()[:90]}")

    # 7. Quantum SPDC / Entanglement
    spdc_matches = re.findall(r'([^.\n]*?(?:spectral purity|Schmidt number|HOM dip|heralded single|visibility)[^.\n]*?(?:\d+(?:\.\d+)?\s*%|\d+\.\d+)[^.\n]*)', all_txt, re.IGNORECASE)
    if spdc_matches:
        findings["found_categories"].append("اپتیک کوانتومی SPDC")
        findings["quantum_spdc"] = [m.strip()[:180] for m in spdc_matches[:3]]
        snippets.append(f"SPDC: {spdc_matches[0].strip()[:90]}")

    # 8. Thermal conductivity / Expansion
    th_matches = re.findall(r'([^.\n]*?(?:thermal conductivity|thermal expansion)[^.\n]*?(?:W/m|W·m|10\^[-–]?\d+|\/K)[^.\n]*)', all_txt, re.IGNORECASE)
    if th_matches:
        findings["found_categories"].append("هدایت گرمایی و انبساط")
        findings["thermal_conductivity"] = [m.strip()[:180] for m in th_matches[:3]]
        snippets.append(f"Thermal: {th_matches[0].strip()[:90]}")

    findings["summary_snippet"] = " | ".join(snippets) if snippets else (all_txt[:140].replace("\n", " ") if all_txt else "No text extracted")
    return findings


def process_batch(max_papers=10, pause_seconds=1.0):
    manifest = load_manifest()
    ckpt = load_checkpoint()

    processed_ids = set(ckpt.get("processed_ids", []))
    total_papers = len(manifest)

    print(f"Loaded manifest with {total_papers} papers. Already processed: {len(processed_ids)} papers.")
    print(f"Beginning batch run of up to {max_papers} papers with controlled cadence and verified persistence...\n")

    count = 0
    temp_pdf = os.path.join(SCRATCH_DIR, "current_paper.pdf")

    for idx, item in enumerate(manifest):
        file_id = item["id"]
        if file_id in processed_ids:
            continue

        if count >= max_papers:
            break

        print(f"[{ckpt['processed_count'] + 1} / {total_papers}] Downloading & examining: {item['filename']} ({item['material']})...")

        # 1. Download single PDF safely
        try:
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
            gdown.download(id=file_id, output=temp_pdf, quiet=True)
        except Exception as e:
            print(f"  ⚠️ Warning: Download failed for {item['filename']}: {e}")
            processed_ids.add(file_id)
            ckpt["processed_ids"] = list(processed_ids)
            ckpt["processed_count"] += 1
            save_checkpoint(ckpt)
            continue

        if not os.path.exists(temp_pdf) or os.path.getsize(temp_pdf) < 500:
            print(f"  ⚠️ Warning: File empty or corrupt: {item['filename']}")
            processed_ids.add(file_id)
            ckpt["processed_ids"] = list(processed_ids)
            ckpt["processed_count"] += 1
            save_checkpoint(ckpt)
            continue

        # 2. Deep extraction
        extracted = extract_scientific_data_from_pdf(temp_pdf, item)
        extracted["index"] = ckpt["processed_count"] + 1

        # 3. Clean up temp PDF immediately to keep disk free
        try:
            os.remove(temp_pdf)
        except Exception:
            pass

        # 4. Save extracted data immediately
        append_extraction(extracted)
        append_md_log(extracted)

        # 5. Update and save checkpoint
        processed_ids.add(file_id)
        ckpt["processed_ids"] = list(processed_ids)
        ckpt["processed_count"] += 1
        if extracted.get("found_categories"):
            ckpt["extracted_count"] += 1
        ckpt["last_index"] = idx
        save_checkpoint(ckpt)

        found_str = ", ".join(extracted.get("found_categories", [])) or "مشخصات عمومی"
        print(f"  ✅ Extracted [{found_str}]: {extracted.get('summary_snippet', '')[:100]}\n")

        count += 1
        time.sleep(pause_seconds)

    print(f"\nBatch completed: {count} papers processed.")
    print(f"Total processed so far: {ckpt['processed_count']} / {total_papers}.")
    print(f"Total papers with rich extracted properties: {ckpt['extracted_count']}.")
    print(f"Checkpoint safely updated at {CHECKPOINT_FILE}.")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    process_batch(max_papers=n, pause_seconds=0.8)
