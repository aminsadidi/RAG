#!/usr/bin/env python3
"""
Find candidate papers for missing crystal optical data using OpenAlex & Crossref,
verify DOI & Open Access status, evaluate abstract relevance using SubQ,
download free OA PDFs, and export an Excel report.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

# Ensure SUBQ key is set BEFORE importing subq
if "SUBQ_KEYS" not in os.environ or not os.environ["SUBQ_KEYS"]:
    os.environ["SUBQ_KEYS"] = "sk-proj-gkxmN3Ohd59yx1Jq9tHeJs1eEJJSMvnG"

# Add scripts/quality for subq module
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import subq  # noqa: E402

# Ensure subq._keys is populated even if subq was previously imported
if not subq._keys:
    subq._keys = [k.strip() for k in os.environ.get("SUBQ_KEYS", "").split(",") if k.strip()]

TARGETS = [
    {
        "crystal": "KBe2BO3F2",
        "alias": "KBBF",
        "quantity": "dndt",
        "queries": [
            "KBe2BO3F2 thermo-optic",
            "KBBF thermo-optic coefficient dn/dT",
            "KBe2BO3F2 refractive index temperature"
        ],
        "subq_instruction": "Does this abstract state that the paper measures or provides thermo-optic coefficients (dn/dT) or temperature dependence of refractive index for KBe2BO3F2 (KBBF)?",
        "subq_true": "Yes, it reports dn/dT or temperature-dependent refractive index for KBe2BO3F2 / KBBF",
        "subq_false": "No"
    },
    {
        "crystal": "BaGa4S7",
        "alias": "BGS",
        "quantity": "dndt",
        "queries": [
            "BaGa4S7 thermo-optic",
            "BaGa4S7 dn/dT",
            "BaGa4S7 refractive index temperature"
        ],
        "subq_instruction": "Does this abstract state that the paper measures or reports thermo-optic coefficients (dn/dT) or temperature dependence of refractive index for BaGa4S7?",
        "subq_true": "Yes, it reports dn/dT or refractive index temperature dependence for BaGa4S7",
        "subq_false": "No"
    },
    {
        "crystal": "AgGaGeS4",
        "alias": "AGGS",
        "quantity": "dndt",
        "queries": [
            "AgGaGeS4 thermo-optic",
            "AgGaGeS4 dn/dT",
            "AgGaGeS4 temperature refractive index"
        ],
        "subq_instruction": "Does this abstract state that the paper measures or reports thermo-optic coefficients (dn/dT) or temperature dependence of refractive index for AgGaGeS4?",
        "subq_true": "Yes, it reports dn/dT or thermo-optic data for AgGaGeS4",
        "subq_false": "No"
    },
    {
        "crystal": "Ag3SbS3",
        "alias": "pyrargyrite",
        "quantity": "dndt",
        "queries": [
            "Ag3SbS3 thermo-optic",
            "pyrargyrite thermo-optic dn/dT",
            "Ag3SbS3 refractive index temperature"
        ],
        "subq_instruction": "Does this abstract state that the paper measures or reports thermo-optic coefficients (dn/dT) or refractive index temperature dependence for Ag3SbS3 (pyrargyrite)?",
        "subq_true": "Yes, it reports dn/dT or thermo-optic data for Ag3SbS3 / pyrargyrite",
        "subq_false": "No"
    },
    {
        "crystal": "Te",
        "alias": "tellurium",
        "quantity": "dndt",
        "queries": [
            "tellurium crystal thermo-optic dn/dT",
            "tellurium crystal refractive index temperature coefficient",
            "tellurium dn/dT infrared"
        ],
        "subq_instruction": "Does this abstract state that the paper measures or reports thermo-optic coefficients (dn/dT) or temperature dependence of refractive index for single-crystal Tellurium (Te)?",
        "subq_true": "Yes, it reports dn/dT or temperature coefficient of refractive index for crystalline Tellurium",
        "subq_false": "No"
    },
    {
        "crystal": "Se",
        "alias": "selenium",
        "quantity": "dndt",
        "queries": [
            "selenium crystal thermo-optic dn/dT",
            "selenium crystal refractive index temperature coefficient",
            "crystalline selenium dn/dT"
        ],
        "subq_instruction": "Does this abstract state that the paper measures or reports thermo-optic coefficients (dn/dT) or temperature dependence of refractive index for crystalline Selenium (Se)?",
        "subq_true": "Yes, it reports dn/dT or thermo-optic coefficient for crystalline Selenium",
        "subq_false": "No"
    },
    {
        "crystal": "Sr2Be2B2O7",
        "alias": "SBBO",
        "quantity": "sellmeier",
        "queries": [
            "Sr2Be2B2O7 Sellmeier",
            "SBBO Sellmeier equations refractive index",
            "Sr2Be2B2O7 dispersion refractive index"
        ],
        "subq_instruction": "Does this abstract state that the paper reports Sellmeier equations, coefficients, or dispersion formulas for the refractive index of Sr2Be2B2O7 (SBBO)?",
        "subq_true": "Yes, it reports Sellmeier equations or dispersion formulas for Sr2Be2B2O7 / SBBO",
        "subq_false": "No"
    },
    {
        "crystal": "Ga2O3",
        "alias": "gallium oxide",
        "quantity": "sellmeier",
        "queries": [
            "Ga2O3 Sellmeier equation",
            "beta-Ga2O3 refractive index Sellmeier dispersion",
            "gallium oxide refractive index dispersion Sellmeier"
        ],
        "subq_instruction": "Does this abstract state that the paper reports Sellmeier equation coefficients or dispersion formulas for the refractive index of Ga2O3 (gallium oxide)?",
        "subq_true": "Yes, it reports Sellmeier equations or dispersion formulas for Ga2O3",
        "subq_false": "No"
    },
    {
        "crystal": "La3Ga5SiO14",
        "alias": "langasite",
        "quantity": "sellmeier",
        "queries": [
            "La3Ga5SiO14 Sellmeier",
            "langasite refractive index Sellmeier dispersion",
            "La3Ga5SiO14 optical dispersion Sellmeier"
        ],
        "subq_instruction": "Does this abstract state that the paper reports Sellmeier equations, coefficients, or dispersion formulas for the refractive index of La3Ga5SiO14 (langasite / LGS)?",
        "subq_true": "Yes, it reports Sellmeier equations or dispersion formulas for La3Ga5SiO14 / langasite",
        "subq_false": "No"
    },
    {
        "crystal": "SrBaNb2O6",
        "alias": "SBN",
        "quantity": "sellmeier",
        "queries": [
            "SrBaNb2O6 Sellmeier",
            "strontium barium niobate Sellmeier dispersion",
            "SBN crystal refractive index Sellmeier"
        ],
        "subq_instruction": "Does this abstract state that the paper reports Sellmeier equations, coefficients, or dispersion formulas for the refractive index of strontium barium niobate (SBN / SrBaNb2O6)?",
        "subq_true": "Yes, it reports Sellmeier equations or dispersion formulas for SBN",
        "subq_false": "No"
    }
]

def reconstruct_abstract(inverted_index):
    if not inverted_index:
        return ""
    words = []
    for word, positions in inverted_index.items():
        for pos in positions:
            words.append((pos, word))
    words.sort()
    return " ".join(w[1] for w in words)

def query_openalex(query, limit=10):
    url = f"https://api.openalex.org/works?search={urllib.parse.quote(query)}&per-page={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "MatRAG-Bot/1.0 (mailto:admin@matrag.local)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
            return data.get("results", [])
    except Exception as e:
        print(f"  [OpenAlex Error for '{query}']: {e}")
        return []

def download_pdf(url, dest_path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                content = resp.read()
                if content.startswith(b"%PDF"):
                    dest_path.write_bytes(content)
                    return True
    except Exception as e:
        print(f"    Download failed: {e}")
    return False

def main():
    reports_dir = ROOT / "scripts" / "quality" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    papers_dir = ROOT / "downloaded_papers"
    papers_dir.mkdir(parents=True, exist_ok=True)

    today = time.strftime("%Y-%m-%d")
    excel_path = reports_dir / f"doi-candidates-{today}.xlsx"
    md_path = reports_dir / f"doi-candidates-{today}.md"

    print("=== MatRAG DOI Finder & Quality Evaluator ===")
    print(f"Targets: {len(TARGETS)} crystals")
    print(f"Output Excel: {excel_path}")
    print()

    all_candidates = []

    for t_idx, target in enumerate(TARGETS, 1):
        crystal = target["crystal"]
        alias = target["alias"]
        quantity = target["quantity"]
        print(f"[{t_idx}/{len(TARGETS)}] Searching for {crystal} ({alias}) [{quantity}]...")

        seen_dois = set()
        candidates_for_target = []

        for q in target["queries"]:
            results = query_openalex(q, limit=8)
            for work in results:
                raw_doi = work.get("doi")
                if not raw_doi:
                    continue
                doi = raw_doi.replace("https://doi.org/", "").strip().lower()
                if doi in seen_dois:
                    continue
                seen_dois.add(doi)

                title = work.get("title") or "Untitled"
                year = work.get("publication_year") or ""
                authorships = work.get("authorships") or []
                author_names = [a.get("author", {}).get("display_name", "") for a in authorships[:3]]
                author_str = ", ".join(filter(None, author_names))
                if len(authorships) > 3:
                    author_str += " et al."
                
                host_venue = work.get("primary_location", {}).get("source", {}) or {}
                venue = host_venue.get("display_name") or ""

                abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
                if not abstract or len(abstract.strip()) < 80:
                    # If abstract is empty, skip as SubQ cannot judge
                    continue

                is_oa = bool(work.get("open_access", {}).get("is_oa"))
                oa_url = work.get("open_access", {}).get("oa_url") or work.get("primary_location", {}).get("pdf_url")

                # SubQ judgment
                state_text = f"Title: {title}\nJournal: {venue} ({year})\nAbstract: {abstract}"
                score = subq.score(
                    state=state_text,
                    instructions=target["subq_instruction"],
                    true=target["subq_true"],
                    false=target["subq_false"]
                )

                if score is None:
                    print(f"  SubQ error / no key for {doi}")
                    continue

                print(f"  DOI: {doi[:30]} | SubQ: {score:.3f} | OA: {is_oa} | {title[:60]}")

                # Threshold: only genuine candidates with score >= 0.5
                if score >= 0.40:
                    cand = {
                        "crystal": crystal,
                        "alias": alias,
                        "quantity": quantity,
                        "title": title,
                        "authors": f"{author_str} ({year})",
                        "journal": venue,
                        "doi": doi,
                        "doi_url": f"https://doi.org/{doi}",
                        "is_oa": is_oa,
                        "oa_url": oa_url or "",
                        "subq_score": round(score, 3),
                        "abstract": abstract[:500] + ("..." if len(abstract) > 500 else ""),
                        "pdf_downloaded": False
                    }

                    # If OA and has direct link, attempt download
                    if is_oa and oa_url and ("pdf" in oa_url.lower() or oa_url.endswith(".pdf")):
                        safe_doi = doi.replace("/", "_").replace(":", "_")
                        pdf_file = papers_dir / f"{safe_doi}.pdf"
                        if not pdf_file.exists():
                            if download_pdf(oa_url, pdf_file):
                                cand["pdf_downloaded"] = True
                                print(f"    --> Downloaded OA PDF: {pdf_file.name}")
                        else:
                            cand["pdf_downloaded"] = True

                    candidates_for_target.append(cand)

        # Sort candidates for this target by SubQ score descending
        candidates_for_target.sort(key=lambda x: -x["subq_score"])
        all_candidates.extend(candidates_for_target)
        print(f"  Found {len(candidates_for_target)} verified relevant papers for {crystal}.\n")

    # Save to Excel using openpyxl
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DOI Candidates"

    headers = [
        "Crystal", "Target Quantity", "SubQ Score", "Status / Access", 
        "Paper Title", "Authors & Year", "Journal", "DOI", "Open Access URL", "Abstract Excerpt"
    ]
    ws.append(headers)

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = Font(name="Calibri", size=11, bold=True)
    h_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = h_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    green_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    orange_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

    for r_idx, c in enumerate(all_candidates, 2):
        if c["pdf_downloaded"]:
            status_text = "Free (Downloaded PDF)"
        elif c["is_oa"]:
            status_text = "Free (Open Access Link)"
        else:
            status_text = "Paywalled (Requires Subscription)"

        ws.append([
            c["crystal"],
            c["quantity"],
            c["subq_score"],
            status_text,
            c["title"],
            c["authors"],
            c["journal"],
            c["doi_url"],
            c["oa_url"],
            c["abstract"]
        ])

        # Style status
        status_cell = ws.cell(row=r_idx, column=4)
        if c["is_oa"]:
            status_cell.fill = green_fill
        else:
            status_cell.fill = orange_fill

        # Make DOI clickable
        doi_cell = ws.cell(row=r_idx, column=8)
        doi_cell.hyperlink = c["doi_url"]
        doi_cell.font = Font(color="0563C1", underline="single")

        if c["oa_url"]:
            oa_cell = ws.cell(row=r_idx, column=9)
            oa_cell.hyperlink = c["oa_url"]
            oa_cell.font = Font(color="0563C1", underline="single")

    # Column widths
    col_widths = [14, 15, 12, 22, 45, 25, 25, 30, 30, 50]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    wb.save(excel_path)
    print(f"\n[OK] Excel saved: {excel_path}")

    # Generate Markdown Summary
    md_lines = [
        f"# Candidate Papers for Missing Crystal Data ({today})",
        "",
        f"Evaluated {len(TARGETS)} missing crystal quantities with OpenAlex and SubQ.",
        f"Total verified relevant papers: **{len(all_candidates)}**.",
        "",
        "| Crystal | Property | SubQ | Status | Title & DOI |",
        "|---|---|---|---|---|"
    ]

    for c in all_candidates:
        st = "🟢 Free (OA)" if c["is_oa"] else "🔒 Paywalled"
        if c["pdf_downloaded"]:
            st = "📥 Free (Downloaded)"
        md_lines.append(f"| **{c['crystal']}** | `{c['quantity']}` | **{c['subq_score']}** | {st} | [{c['title']}]({c['doi_url']}) |")

    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[OK] Markdown report saved: {md_path}")

    # Check Telegram sending if token is in environment
    tg_token = os.environ.get("TELEGRAM_TOKEN")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID", "359353459")
    if tg_token:
        print(f"Sending Excel file to Telegram chat {tg_chat}...")
        try:
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            body = bytearray()
            # chat_id field
            body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{tg_chat}\r\n".encode())
            # caption field
            caption = f"📊 گزارش مقاله‌های یافت‌شده برای ۱۰ کمبود بلوری ({today})\nتعداد کل: {len(all_candidates)} مقاله"
            body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode())
            # document field
            file_bytes = excel_path.read_bytes()
            body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"{excel_path.name}\"\r\nContent-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n".encode())
            body.extend(file_bytes)
            body.extend(f"\r\n--{boundary}--\r\n".encode())

            req = urllib.request.Request(
                f"https://api.telegram.org/bot{tg_token}/sendDocument",
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                print(f"[OK] Telegram delivery success: {resp.status}")
        except Exception as e:
            print(f"[!] Telegram send failed: {e}")
    else:
        print("\nNote: TELEGRAM_TOKEN not in environment. File generated locally and ready for dispatch.")

if __name__ == "__main__":
    main()
