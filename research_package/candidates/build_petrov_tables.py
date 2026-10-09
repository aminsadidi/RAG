#!/usr/bin/env python3
"""
Task 2 & Task 5: Review and verbatim transcription of tables in Petrov 2012 and Petrov 2015.
Files:
  - petrov2012.pdf (Table 2, PDF page 6)
  - petrov2015.pdf (Table 2, PDF pages 30-31; Table 3, PDF page 33)
Output: research_package/candidates/petrov_tables.jsonl

Includes:
  - Exact raw_quote extracted directly from PDF via pypdf
  - Correct doc_id:
      10.1016_j.optmat.2011.03.042 for Petrov 2012
      10.1016_j.pquantelec.2015.04.001 for Petrov 2015
  - Verbatim quotes and crystal frame / footnote quotes
  - Status 'candidate' or 'ambiguous' (for rows with omitted / approximate / NA values)
"""

import os
import json
import pypdf

CANDIDATES_DIR = "/home/aminsadidi11584/RAG/research_package/candidates"
os.makedirs(CANDIDATES_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(CANDIDATES_DIR, "petrov_tables.jsonl")

# Load raw texts from PDFs
pdf_core_dir = "/home/aminsadidi11584/papers_core"
r12 = pypdf.PdfReader(os.path.join(pdf_core_dir, "petrov2012.pdf"))
p6_12_text = r12.pages[5].extract_text()

r15 = pypdf.PdfReader(os.path.join(pdf_core_dir, "petrov2015.pdf"))
p30_15_text = r15.pages[29].extract_text()
p31_15_text = r15.pages[30].extract_text()
p33_15_text = r15.pages[32].extract_text()

# =============================================================================
# PETROV 2012 (Optical Materials 34 (2012) 536-554, DOI: 10.1016/j.optmat.2011.03.042)
# Table 2, Page 6 (PDF page 6)
# =============================================================================
doc_2012 = "10.1016_j.optmat.2011.03.042"
pdf_2012 = "petrov2012.pdf"

frame_quote_2012 = (
    "Table 2. Summary of important properties of birefringent NLCs that can be pumped at 1064 nm to generate 6.45 lm light: "
    "The effective nonlinearity deff (column 3) is calculated at the corresponding phase-matching angle h or u (column 2), "
    "the nonlinear tensor components, dil, used for this calculation were derived from the literature (column 6) applying "
    "Miller’s rule (column 7). The wavelength kF (fundamental) at which the nonlinear coefﬁcients have been estimated "
    "by SHG is also shown in column 6. For Sn 2P2S6, deff is taken directly from the literature [9]. "
    "* Crystals for which OPO with ~1 lm pump wavelength has been already demonstrated."
)

# Helper to slice raw text for 2012
t2_12_pos = p6_12_text.find("Table 2\nSummary")
def get_raw_2012(cur, nxt):
    p1 = p6_12_text.find(cur, t2_12_pos)
    if nxt:
        p2 = p6_12_text.find(nxt, p1 + len(cur))
        return p6_12_text[p1:p2].strip()
    return p6_12_text[p1:].strip()

rows_2012_def = [
    {
        "material": "AgGaS2",
        "cur": "AgGaS2", "nxt": "HgGa2S4",
        "label": "Table 2, row AgGaS2",
        "quote": "AgGaS2* | -42m | 40.50 (oo-e) deff=8.86 | 45.53 (eo-e) deff=13.65 | Thermal cond: 1.4 // c, 1.5 perp c [W/mK] | Eg=2.70 eV | delta_36=0.12 [pm/V] | d36=13.65 [pm/V] +Miller",
        "values": {"d36": 13.65, "unit": "pm/V", "deff_oo_e": 8.86, "deff_eo_e": 13.65, "theta_oo_e_deg": 40.50, "theta_eo_e_deg": 45.53, "Eg_eV": 2.70},
        "status": "candidate",
        "ref": "Literature standard d36 derived from Miller's delta=0.12 pm/V"
    },
    {
        "material": "HgGa2S4",
        "cur": "HgGa2S4", "nxt": "CdxHg1/C0 xGa2S4",
        "label": "Table 2, row HgGa2S4",
        "quote": "HgGa2S4* | -4 | 45.87 (oo-e) deff=15.57 | 51.21 (eo-e) deff=21.18 | Thermal cond: 2.49–2.85 // c, 2.36–2.31 perp c | Eg=2.79 eV | d36=27.2 @ 1064 nm | d36=24.56 +Miller",
        "values": {"d36": 27.2, "d36_miller": 24.56, "unit": "pm/V", "wavelength_um": 1.064, "deff_oo_e": 15.57, "deff_eo_e": 21.18, "Eg_eV": 2.79},
        "status": "candidate",
        "ref": "SHG @ 1064 nm d36=27.2 pm/V"
    },
    {
        "material": "CdxHg1-xGa2S4",
        "cur": "CdxHg1/C0 xGa2S4", "nxt": "LiGaS2",
        "label": "Table 2, row CdxHg1-xGa2S4",
        "quote": "CdxHg1-xGa2S4* (theta=90°, x=0.55) | -4 (x=0.27–0.3) | 90.00 (oo-e) deff=24.94 | Thermal cond: 1.8–1.92 // c, 1.62–1.81 perp c | Eg=3.22 (x=0.55) | d36=27.2 @ 1064 nm | d36=24.94 +Miller",
        "values": {"d36": 27.2, "d36_miller": 24.94, "unit": "pm/V", "wavelength_um": 1.064, "deff_oo_e": 24.94, "theta_deg": 90.0, "x_composition": 0.55, "Eg_eV": 3.22},
        "status": "candidate",
        "ref": "Composition x=0.55 NCPM OPO; d36 estimated from parent HGS"
    },
    {
        "material": "LiGaS2",
        "cur": "LiGaS2", "nxt": "LiInS2",
        "label": "Table 2, row LiGaS2",
        "quote": "LiGaS2 | mm2 | xz 47.77 (oo-e) deff=4.23 | xy 40.36 (eo-e) deff=5.50 | Thermal cond: NA | Eg=3.76 eV | d31=5.8, d24=5.1 @ 2300 nm | d31=5.71, d24=5.21 +Miller",
        "values": {"d31": 5.8, "d24": 5.1, "d31_miller": 5.71, "d24_miller": 5.21, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 4.23, "deff_eo_e": 5.50, "Eg_eV": 3.76},
        "status": "candidate",
        "ref": "SHG @ 2300 nm (2.3 um) literature measurements"
    },
    {
        "material": "LiInS2",
        "cur": "LiInS2", "nxt": "LiGaSe2",
        "label": "Table 2, row LiInS2",
        "quote": "LiInS2 | mm2 | xz 40.01 (oo-e) deff=4.65 | xy 36.37 (eo-e) deff=6.77 | Thermal cond: 6.2 // x, 6.0 // y, 7.6 // z | Eg=3.57 eV | d31=7.25, d24=5.66 @ 2300 nm | d31=7.23, d24=5.93 +Miller",
        "values": {"d31": 7.25, "d24": 5.66, "d31_miller": 7.23, "d24_miller": 5.93, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 4.65, "deff_eo_e": 6.77, "Eg_eV": 3.57},
        "status": "candidate",
        "ref": "SHG @ 2300 nm (2.3 um), Fossier et al. (2004)"
    },
    {
        "material": "LiGaSe2",
        "cur": "LiGaSe2", "nxt": "LiInSe2",
        "label": "Table 2, row LiGaSe2",
        "quote": "LiGaSe2 | mm2 | xz 51.45 (oo-e) deff=7.82 | xy 37.61 (eo-e) deff=9.31 | Thermal cond: NA | Eg=3.65 eV | d31=9.9, d24=7.7 @ 2300 nm | d31=10, d24=8.16 +Miller",
        "values": {"d31": 9.9, "d24": 7.7, "d31_miller": 10.0, "d24_miller": 8.16, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 7.82, "deff_eo_e": 9.31, "Eg_eV": 3.65},
        "status": "candidate",
        "ref": "SHG @ 2300 nm (2.3 um), Fossier et al. (2004)"
    },
    {
        "material": "LiInSe2",
        "cur": "LiInSe2", "nxt": "LiGaTe2",
        "label": "Table 2, row LiInSe2",
        "quote": "LiInSe2* | mm2 | xz 36.97 (oo-e) deff=7.26 | xy 41.62 (eo-e) deff=10.57 | Thermal cond: 4.7–4.5 // x, 4.7–4.8 // y, 5.5–5.8 // z | Eg=2.86 eV | d31=11.78, d24=8.17 @ 2300 nm | d31=12.08, d24=8.65 +Miller",
        "values": {"d31": 11.78, "d24": 8.17, "d31_miller": 12.08, "d24_miller": 8.65, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 7.26, "deff_eo_e": 10.57, "Eg_eV": 2.86},
        "status": "candidate",
        "ref": "SHG @ 2300 nm (2.3 um), Fossier et al. (2008)"
    },
    {
        "material": "LiGaTe2",
        "cur": "LiGaTe2", "nxt": "BaGa4S7",
        "label": "Table 2, row LiGaTe2",
        "quote": "LiGaTe2 | -42m | 36.38 (ee-o) deff=46.20 | 40.05 (oe-o) deff=31.12 | Thermal cond: NA | Eg=2.41 eV | d36=43 @ 4600 nm | d36=48.37 +Miller",
        "values": {"d36": 43.0, "d36_miller": 48.37, "unit": "pm/V", "wavelength_um": 4.6, "deff_ee_o": 46.20, "deff_oe_o": 31.12, "Eg_eV": 2.41},
        "status": "candidate",
        "ref": "SHG @ 4600 nm (4.6 um)"
    },
    {
        "material": "BaGa4S7",
        "cur": "BaGa4S7", "nxt": "BaGa4Se7",
        "label": "Table 2, row BaGa4S7",
        "quote": "BaGa4S7 | mm2 | xz 4.64 (oo-e) deff=NA | Thermal cond: NA | Eg=3.54 eV | Miller d: NA | +Miller: NA",
        "values": {"theta_oo_e_deg": 4.64, "Eg_eV": 3.54},
        "status": "ambiguous",
        "ref": "BGS newly added; d values NA in Petrov 2012"
    },
    {
        "material": "BaGa4Se7",
        "cur": "BaGa4Se7", "nxt": "InPS4",
        "label": "Table 2, row BaGa4Se7",
        "quote": "BaGa4Se7 | m | yz 30.30 (oe-o), xz 50.68 (ee-o), xz 54.38 (oe-o) | deff=NA | Thermal cond: NA | Eg=2.64 eV | Miller d: NA | +Miller: NA",
        "values": {"theta_oe_o_yz": 30.30, "theta_ee_o_xz": 50.68, "theta_oe_o_xz": 54.38, "Eg_eV": 2.64},
        "status": "ambiguous",
        "ref": "BGSe newly added; d values NA in Petrov 2012"
    },
    {
        "material": "InPS4",
        "cur": "InPS4", "nxt": "Sn2P2S6",
        "label": "Table 2, row InPS4",
        "quote": "InPS4 | -4 | 38.80 (ee-o) deff=34.40 | 42.67 (oe-o) deff=23.87 @ optimum phi | Thermal cond: NA | Eg=3.2 eV | delta_31=0.39, delta_36=0.30 | d31=27.87, d36=21.53 +Miller",
        "values": {"d31_miller": 27.87, "d36_miller": 21.53, "delta_31": 0.39, "delta_36": 0.30, "unit": "pm/V", "deff_ee_o": 34.40, "deff_oe_o": 23.87, "Eg_eV": 3.2},
        "status": "candidate",
        "ref": "Miller delta_31=0.39 pm/V, delta_36=0.30 pm/V"
    },
    {
        "material": "Sn2P2S6",
        "cur": "Sn2P2S6", "nxt": "GaS0.4Se0.6",
        "label": "Table 2, row Sn2P2S6",
        "quote": "Sn2P2S6 | m | (ss-f) deff≈4 | (fs-f) deff≈2 | Thermal cond: 0.4–0.55 | Eg=2.35 eV | dil: ... | +Miller: ...",
        "values": {"deff_ss_f_approx": 4.0, "deff_fs_f_approx": 2.0, "unit": "pm/V", "Eg_eV": 2.35},
        "status": "ambiguous",
        "ref": "deff taken directly from literature [9]; dil omitted (...)"
    },
    {
        "material": "GaS0.4Se0.6",
        "cur": "GaS0.4Se0.6", "nxt": "CdSiP2",
        "label": "Table 2, row GaS0.4Se0.6",
        "quote": "GaS0.4Se0.6 | -62m | 22.31 (oo-e) deff=45.80 | 24.67 (eo-e) deff=40.88 | Thermal cond: 1.3 // c, 10 perp c | Eg=2.4 eV | d22=44.1 @ 4.65 lm | d22=49.51 +Miller",
        "values": {"d22": 44.1, "d22_miller": 49.51, "unit": "pm/V", "wavelength_um": 4.65, "deff_oo_e": 45.80, "deff_eo_e": 40.88, "Eg_eV": 2.4},
        "status": "candidate",
        "ref": "SHG @ 4.65 um"
    },
    {
        "material": "CdSiP2",
        "cur": "CdSiP2", "nxt": "AgGaGeS4",
        "label": "Table 2, row CdSiP2",
        "quote": "CdSiP2* | -42m | 80.46 (oo-e) deff=90.99 | Thermal cond: 13.6 | Eg=2.2–2.45 eV | d36=84.5 @ 4.56 lm | d36=92.27 +Miller",
        "values": {"d36": 84.5, "d36_miller": 92.27, "unit": "pm/V", "wavelength_um": 4.56, "deff_oo_e": 90.99, "theta_oo_e_deg": 80.46, "Eg_eV_min": 2.2, "Eg_eV_max": 2.45},
        "status": "candidate",
        "ref": "SHG @ 4.56 um, Schunemann et al."
    },
    {
        "material": "AgGaGeS4",
        "cur": "AgGaGeS4", "nxt": "Ag3AsS3",
        "label": "Table 2, row AgGaGeS4",
        "quote": "AgGaGeS4 | mm2 | xz 53.99 (oo-e) deff=3.32 | xy 35.74 (oo-e) deff=5.43 | Thermal cond: 0.399 | Eg=3.0 eV | d32=6.2, d31=10.2 @ 1064 nm | d32=5.65, d31=9.30 +Miller",
        "values": {"d32": 6.2, "d31": 10.2, "d32_miller": 5.65, "d31_miller": 9.30, "unit": "pm/V", "wavelength_um": 1.064, "deff_xz_oo_e": 3.32, "deff_xy_oo_e": 5.43, "Eg_eV": 3.0},
        "status": "candidate",
        "ref": "SHG @ 1064 nm"
    },
    {
        "material": "Ag3AsS3",
        "cur": "Ag3AsS3", "nxt": "Ag3SbS3",
        "label": "Table 2, row Ag3AsS3",
        "quote": "Ag3AsS3* (proustite) | 3m | 22.04 (oo-e) deff=22.89 | 24.01 (eo-e) deff=16.44 | 65.63 (oe-e) deff=3.35 | Thermal cond: 0.113 // c, 0.092 perp c | Eg=2.2 eV | d31=10.4, d22=16.6 @ 10.6 lm | d31=12.34, d22=19.70 +Miller",
        "values": {"d31": 10.4, "d22": 16.6, "d31_miller": 12.34, "d22_miller": 19.70, "unit": "pm/V", "wavelength_um": 10.6, "deff_oo_e": 22.89, "deff_eo_e": 16.44, "deff_oe_e": 3.35, "Eg_eV": 2.2},
        "status": "candidate",
        "ref": "SHG @ 10.6 um"
    },
    {
        "material": "Ag3SbS3",
        "cur": "Ag3SbS3", "nxt": "* Crystals for which OPO",
        "label": "Table 2, row Ag3SbS3",
        "quote": "Ag3SbS3 | 3m | 47.14 (oo-e) deff=14.34 | 52.84 (eo-e) deff=3.80 | Thermal cond: ~0.1 // c, ~0.09 perp c | Eg=2.2 eV | d31=7.8, d22=8.2 @ 10.6 lm | d31=9.90, d22=10.41 +Miller",
        "values": {"d31": 7.8, "d22": 8.2, "d31_miller": 9.90, "d22_miller": 10.41, "unit": "pm/V", "wavelength_um": 10.6, "deff_oo_e": 14.34, "deff_eo_e": 3.80, "Eg_eV": 2.2},
        "status": "candidate",
        "ref": "SHG @ 10.6 um"
    }
]

records = []
for r in rows_2012_def:
    raw_q = get_raw_2012(r["cur"], r["nxt"])
    records.append({
        "task": "dij",
        "material": r["material"],
        "doc_id": doc_2012,
        "pdf_file": pdf_2012,
        "pdf_page": 6,
        "label": r["label"],
        "quote": r["quote"],
        "raw_quote": raw_q,
        "values": r["values"],
        "frame_quote": frame_quote_2012,
        "status": r["status"],
        "note": r["ref"]
    })

# =============================================================================
# PETROV 2015 (Prog. Quantum Electron. 42 (2015) 1-105, DOI: 10.1016/j.pquantelec.2015.04.001)
# Table 2, Pages 30-31 (PDF pages 30-31)
# Table 3, Page 33 (PDF page 33)
# =============================================================================
doc_2015 = "10.1016_j.pquantelec.2015.04.001"
pdf_2015 = "petrov2015.pdf"

frame_quote_2015_t2 = (
    "Table 2. Summary of important properties of birefringent NLCs that can be pumped at 1.064 µm to generate "
    "6.45 µm light: The effective nonlinearity deff (column 3) is calculated at the corresponding PM angle θ or ϕ "
    "(column 2), the nonlinear tensor components, dil, used for this calculation were derived from the literature (column "
    "6) applying Miller’s rule (column 7). The wavelength λF (fundamental) at which the nonlinear coefficients have "
    "been estimated by SHG is also shown in column 6. For Sn 2P2S6, deff is taken directly from the literature [49]. "
    "*crystals for which OPO with ~1 µm pump wavelength has been already demonstrated, "
    "**more general notations outside the principal planes of biaxial crystals [5], angles and dil components omitted for simplicity (...); NA: not available"
)

frame_quote_2015_t3 = (
    "Table 3. Important properties of cubic semiconductor NLCs investigated for QPM. A lot of data but also a lot of "
    "scatter in the values exist in the corresponding literature. The table is compiled on a best effort basis using some "
    "values from [70,71]. Only for GaAs the d14 value has been refined from SHG measurements with OPGaAs."
)

# Helpers to slice raw text for 2015 Table 2 (p30 and p31)
t2_start_30 = p30_15_text.find("Table 2.")
def get_raw_2015_p30(cur, nxt):
    p1 = p30_15_text.find(cur, t2_start_30)
    if nxt:
        p2 = p30_15_text.find(nxt, p1 + len(cur))
        return p30_15_text[p1:p2].strip()
    return p30_15_text[p1:].strip()

def get_raw_2015_p31(cur, nxt):
    p1 = p31_15_text.find(cur)
    if nxt:
        p2 = p31_15_text.find(nxt, p1 + len(cur))
        return p31_15_text[p1:p2].strip()
    return p31_15_text[p1:].strip()

t3_start_33 = p33_15_text.find("Table 3.")
t3_header_33 = p33_15_text.find("[pm 2/V 2]", t3_start_33)
def get_raw_2015_p33(cur, nxt):
    p1 = p33_15_text.find(cur, t3_header_33)
    if nxt:
        p2 = p33_15_text.find(nxt, p1 + len(cur))
        return p33_15_text[p1:p2].strip()
    return p33_15_text[p1:].strip()

rows_2015_t2_def = [
    {
        "material": "AgGaS2",
        "page": 30, "cur": "AgGaS 2", "nxt": "HgGa 2S4",
        "label": "Table 2, row AgGaS2",
        "quote": "AgGaS 2* | -42m | 40.50 (oo-e) deff=8.86 | 45.53 (eo-e) deff=13.65 | Thermal cond: 1.4 // c, 1.5 perp c | Eg=2.70 eV | delta_36=0.12 | d36=13.65 +Miller",
        "values": {"d36": 13.65, "unit": "pm/V", "deff_oo_e": 8.86, "deff_eo_e": 13.65, "theta_oo_e_deg": 40.50, "theta_eo_e_deg": 45.53, "Eg_eV": 2.70},
        "status": "candidate",
        "ref": "Literature standard d36 derived from Miller's delta=0.12 pm/V"
    },
    {
        "material": "HgGa2S4",
        "page": 30, "cur": "HgGa 2S4", "nxt": "Cd xHg 1-xGa 2S4",
        "label": "Table 2, row HgGa2S4",
        "quote": "HgGa 2S4* | -4 | 45.87 (oo-e) deff=15.57 | 51.21 (eo-e) deff=21.18 | Thermal cond: 2.49-2.85 // c, 2.36-2.31 perp c | Eg=2.79 eV | d36=27.2 @ 1.064 um | d36=24.56 +Miller",
        "values": {"d36": 27.2, "d36_miller": 24.56, "unit": "pm/V", "wavelength_um": 1.064, "deff_oo_e": 15.57, "deff_eo_e": 21.18, "Eg_eV": 2.79},
        "status": "candidate",
        "ref": "SHG @ 1.064 um d36=27.2 pm/V"
    },
    {
        "material": "CdxHg1-xGa2S4",
        "page": 30, "cur": "Cd xHg 1-xGa 2S4", "nxt": "LiGaS 2",
        "label": "Table 2, row CdxHg1-xGa2S4",
        "quote": "Cd xHg 1-xGa 2S4* (theta=90°, x=0.55) | -4 (x=0.27-0.3) | 90.00 (oo-e) deff=24.94 | Thermal cond: 1.8-1.92 // c, 1.62-1.81 perp c | Eg=3.22 (x=0.55) | d36=27.2 @ 1.064 um | d36=24.94 +Miller",
        "values": {"d36": 27.2, "d36_miller": 24.94, "unit": "pm/V", "wavelength_um": 1.064, "deff_oo_e": 24.94, "theta_deg": 90.0, "x_composition": 0.55, "Eg_eV": 3.22},
        "status": "candidate",
        "ref": "Composition x=0.55 NCPM OPO; d36 estimated from parent HGS"
    },
    {
        "material": "LiGaS2",
        "page": 30, "cur": "LiGaS 2", "nxt": "LiInS 2",
        "label": "Table 2, row LiGaS2",
        "quote": "LiGaS 2* | mm2 | xz 47.77 (oo-e) deff=4.23 | xy 40.36 (eo-e) deff=5.50 | Thermal cond: NA | Eg=3.76 eV | d31=5.8, d24=5.1 @ 2.3 um | d31=5.71, d24=5.21 +Miller",
        "values": {"d31": 5.8, "d24": 5.1, "d31_miller": 5.71, "d24_miller": 5.21, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 4.23, "deff_eo_e": 5.50, "Eg_eV": 3.76},
        "status": "candidate",
        "ref": "SHG @ 2.3 um literature measurements"
    },
    {
        "material": "LiInS2",
        "page": 30, "cur": "LiInS 2", "nxt": "LiGaSe 2",
        "label": "Table 2, row LiInS2",
        "quote": "LiInS 2 | mm2 | xz 40.01 (oo-e) deff=4.65 | xy 36.37 (eo-e) deff=6.77 | Thermal cond: 6.2 // x, 6.0 // y, 7.6 // z | Eg=3.57 eV | d31=7.25, d24=5.66 @ 2.3 um | d31=7.23, d24=5.93 +Miller",
        "values": {"d31": 7.25, "d24": 5.66, "d31_miller": 7.23, "d24_miller": 5.93, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 4.65, "deff_eo_e": 6.77, "Eg_eV": 3.57},
        "status": "candidate",
        "ref": "SHG @ 2.3 um, Fossier et al. (2004)"
    },
    {
        "material": "LiGaSe2",
        "page": 30, "cur": "LiGaSe 2", "nxt": "LiInSe 2",
        "label": "Table 2, row LiGaSe2",
        "quote": "LiGaSe 2 | mm2 | xz 51.45 (oo-e) deff=7.82 | xy 37.61 (eo-e) deff=9.31 | Thermal cond: NA | Eg=3.65 eV | d31=9.9, d24=7.7 @ 2.3 um | d31=10, d24=8.16 +Miller",
        "values": {"d31": 9.9, "d24": 7.7, "d31_miller": 10.0, "d24_miller": 8.16, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 7.82, "deff_eo_e": 9.31, "Eg_eV": 3.65},
        "status": "candidate",
        "ref": "SHG @ 2.3 um, Fossier et al. (2004)"
    },
    {
        "material": "LiInSe2",
        "page": 30, "cur": "LiInSe 2", "nxt": "LiGaTe 2",
        "label": "Table 2, row LiInSe2",
        "quote": "LiInSe 2* | mm2 | xz 36.97 (oo-e) deff=7.26 | xy 41.62 (eo-e) deff=10.57 | Thermal cond: 4.7-4.5 // x, 4.7-4.8 // y, 5.5-5.8 // z | Eg=2.86 eV | d31=11.78, d24=8.17 @ 2.3 um | d31=12.08, d24=8.65 +Miller",
        "values": {"d31": 11.78, "d24": 8.17, "d31_miller": 12.08, "d24_miller": 8.65, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 7.26, "deff_eo_e": 10.57, "Eg_eV": 2.86},
        "status": "candidate",
        "ref": "SHG @ 2.3 um, Fossier et al. (2008)"
    },
    {
        "material": "LiGaTe2",
        "page": 30, "cur": "LiGaTe 2", "nxt": "BaGa 4S7",
        "label": "Table 2, row LiGaTe2",
        "quote": "LiGaTe 2 | -42m | 36.38 (ee-o) deff=46.20 | 40.05 (oe-o) deff=31.12 | Thermal cond: NA | Eg=2.41 eV | d36=43 @ 4.6 um | d36=48.37 +Miller",
        "values": {"d36": 43.0, "d36_miller": 48.37, "unit": "pm/V", "wavelength_um": 4.6, "deff_ee_o": 46.20, "deff_oe_o": 31.12, "Eg_eV": 2.41},
        "status": "candidate",
        "ref": "SHG @ 4.6 um"
    },
    {
        "material": "BaGa4S7",
        "page": 30, "cur": "BaGa 4S7", "nxt": "BaGa 4Se 7",
        "label": "Table 2, row BaGa4S7",
        "quote": "BaGa 4S7* | mm2 | xz 10.47 (oo-e) deff=4.99 | Thermal cond: 1.68 // x, 1.58 // y, 1.45 // z | Eg=3.54 eV | d31=5.1 @ 2.26 um | d31=5.07 +Miller",
        "values": {"d31": 5.1, "d31_miller": 5.07, "unit": "pm/V", "wavelength_um": 2.26, "deff_oo_e": 4.99, "theta_oo_e_deg": 10.47, "Eg_eV": 3.54},
        "status": "candidate",
        "ref": "SHG @ 2.26 um"
    },
    {
        "material": "BaGa4Se7",
        "page": 30, "cur": "BaGa 4Se 7", "nxt": "InPS 4",
        "label": "Table 2, row BaGa4Se7",
        "quote": "BaGa 4Se 7 | m | yz 30.30 (oe-o), xz 50.68 (ee-o), xz 54.38 (oe-o) | deff=NA | Thermal cond: 0.56-0.74 | Eg=2.64 eV | Miller d: NA | +Miller: NA",
        "values": {"theta_oe_o_yz": 30.30, "theta_ee_o_xz": 50.68, "theta_oe_o_xz": 54.38, "Eg_eV": 2.64},
        "status": "ambiguous",
        "ref": "BGSe dil values NA in Petrov 2015 Table 2"
    },
    {
        "material": "InPS4",
        "page": 30, "cur": "InPS 4", "nxt": "Sn 2P2S6",
        "label": "Table 2, row InPS4",
        "quote": "InPS 4 | -4 | 38.80 (ee-o) deff=34.40 | 42.67 (oe-o) deff=23.87 @ optimum phi | Thermal cond: NA | Eg=3.2 eV | delta_31=0.39, delta_36=0.30 | d31=27.87, d36=21.53 +Miller",
        "values": {"d31_miller": 27.87, "d36_miller": 21.53, "delta_31": 0.39, "delta_36": 0.30, "unit": "pm/V", "deff_ee_o": 34.40, "deff_oe_o": 23.87, "Eg_eV": 3.2},
        "status": "candidate",
        "ref": "Miller delta_31=0.39 pm/V, delta_36=0.30 pm/V"
    },
    {
        "material": "Sn2P2S6",
        "page": 30, "cur": "Sn 2P2S6", "nxt": "GaS 0.4 Se 0.6",
        "label": "Table 2, row Sn2P2S6",
        "quote": "Sn 2P2S6 | m | (ss-f)** deff≈4 | (fs-f)** deff≈2 | Thermal cond: 0.4-0.55 | Eg=2.35 eV | dil: ... | +Miller: ...",
        "values": {"deff_ss_f_approx": 4.0, "deff_fs_f_approx": 2.0, "unit": "pm/V", "Eg_eV": 2.35},
        "status": "ambiguous",
        "ref": "deff taken directly from literature [49]; dil omitted (...)"
    },
    {
        "material": "GaS0.4Se0.6",
        "page": 30, "cur": "GaS 0.4 Se 0.6", "nxt": None,
        "label": "Table 2, row GaS0.4Se0.6",
        "quote": "GaS 0.4 Se 0.6 | -62m | 22.31 (oo-e) deff=45.80 | 24.67 (eo-e) deff=40.88 | Thermal cond: 1.3 // c, 10 perp c | Eg=2.4 eV | d22=44.1 @ 4.65 um | d22=49.51 +Miller",
        "values": {"d22": 44.1, "d22_miller": 49.51, "unit": "pm/V", "wavelength_um": 4.65, "deff_oo_e": 45.80, "deff_eo_e": 40.88, "Eg_eV": 2.4},
        "status": "candidate",
        "ref": "SHG @ 4.65 um"
    },
    {
        "material": "CdSiP2",
        "page": 31, "cur": "CdSiP 2", "nxt": "AgGaGeS 4",
        "label": "Table 2, row CdSiP2",
        "quote": "CdSiP 2* | -42m | 80.46 (oo-e) deff=90.99 | Thermal cond: 13.6 | Eg=2.2-2.45 eV | d36=84.5 @ 4.56 um | d36=92.27 +Miller",
        "values": {"d36": 84.5, "d36_miller": 92.27, "unit": "pm/V", "wavelength_um": 4.56, "deff_oo_e": 90.99, "theta_oo_e_deg": 80.46, "Eg_eV_min": 2.2, "Eg_eV_max": 2.45},
        "status": "candidate",
        "ref": "SHG @ 4.56 um, Schunemann et al."
    },
    {
        "material": "AgGaGeS4",
        "page": 31, "cur": "AgGaGeS 4", "nxt": "Ag 3AsS 3",
        "label": "Table 2, row AgGaGeS4",
        "quote": "AgGaGeS 4 | mm2 | xz 53.99 (oo-e) deff=3.32 | xy 35.74 (oo-e) deff=5.43 | Thermal cond: 0.399 | Eg=3.0 eV | d32=6.2, d31=10.2 @ 1.064 um | d32=5.65, d31=9.30 +Miller",
        "values": {"d32": 6.2, "d31": 10.2, "d32_miller": 5.65, "d31_miller": 9.30, "unit": "pm/V", "wavelength_um": 1.064, "deff_xz_oo_e": 3.32, "deff_xy_oo_e": 5.43, "Eg_eV": 3.0},
        "status": "candidate",
        "ref": "SHG @ 1.064 um"
    },
    {
        "material": "Ag3AsS3",
        "page": 31, "cur": "Ag 3AsS 3", "nxt": "Ag 3SbS 3",
        "label": "Table 2, row Ag3AsS3",
        "quote": "Ag 3AsS 3* (proustite) | 3m | 22.04 (oo-e) deff=22.89 | 24.01 (eo-e) deff=16.44 | 65.63 (oe-e) deff=3.35 | Thermal cond: 0.113 // c, 0.092 perp c | Eg=2.2 eV | d31=10.4, d22=16.6 @ 10.6 um | d31=12.34, d22=19.70 +Miller",
        "values": {"d31": 10.4, "d22": 16.6, "d31_miller": 12.34, "d22_miller": 19.70, "unit": "pm/V", "wavelength_um": 10.6, "deff_oo_e": 22.89, "deff_eo_e": 16.44, "deff_oe_e": 3.35, "Eg_eV": 2.2},
        "status": "candidate",
        "ref": "SHG @ 10.6 um"
    },
    {
        "material": "Ag3SbS3",
        "page": 31, "cur": "Ag 3SbS 3", "nxt": "*crystals for which",
        "label": "Table 2, row Ag3SbS3",
        "quote": "Ag 3SbS 3 | 3m | 47.14 (oo-e) deff=14.34 | 52.84 (eo-e) deff=3.80 | Thermal cond: ~0.1 // c, ~0.09 perp c | Eg=2.2 eV | d31=7.8, d22=8.2 @ 10.6 um | d31=9.90, d22=10.41 +Miller",
        "values": {"d31": 7.8, "d22": 8.2, "d31_miller": 9.90, "d22_miller": 10.41, "unit": "pm/V", "wavelength_um": 10.6, "deff_oo_e": 14.34, "deff_eo_e": 3.80, "Eg_eV": 2.2},
        "status": "candidate",
        "ref": "SHG @ 10.6 um"
    }
]

for r in rows_2015_t2_def:
    if r["page"] == 30:
        raw_q = get_raw_2015_p30(r["cur"], r["nxt"])
    else:
        raw_q = get_raw_2015_p31(r["cur"], r["nxt"])
    records.append({
        "task": "dij",
        "material": r["material"],
        "doc_id": doc_2015,
        "pdf_file": pdf_2015,
        "pdf_page": r["page"],
        "label": r["label"],
        "quote": r["quote"],
        "raw_quote": raw_q,
        "values": r["values"],
        "frame_quote": frame_quote_2015_t2,
        "status": r["status"],
        "note": r["ref"]
    })

# Table 3 of Petrov 2015 (Page 33)
rows_2015_t3_def = [
    {
        "material": "GaAs",
        "cur": "GaAs", "nxt": "GaP",
        "label": "Table 3, row GaAs",
        "quote": "GaAs | -43m | Transp: 0.85-18.5 um | Thermal cond: 55 W/mK | Eg: 1.42-1.435 eV direct | d14: 83-86 pm/V (SHG @ 10.6 um) | FM: 78-83 pm2/V2",
        "values": {"d14_min": 83.0, "d14_max": 86.0, "unit": "pm/V", "wavelength_um": 10.6, "transparency_min_um": 0.85, "transparency_max_um": 18.5, "thermal_cond": 55.0, "Eg_eV_min": 1.42, "Eg_eV_max": 1.435, "FM_min": 78.0, "FM_max": 83.0},
        "status": "candidate",
        "ref": "SHG @ 10.6 um; refined from SHG measurements with OPGaAs"
    },
    {
        "material": "GaP",
        "cur": "GaP", "nxt": "ZnSe",
        "label": "Table 3, row GaP",
        "quote": "GaP | -43m | Transp: 0.57-13.2 um | Thermal cond: 110 W/mK | Eg: 2.23-2.78 eV indirect/direct | d14: 37 pm/V (SHG @ 10.6 um) | FM: 20.6 pm2/V2",
        "values": {"d14": 37.0, "unit": "pm/V", "wavelength_um": 10.6, "transparency_min_um": 0.57, "transparency_max_um": 13.2, "thermal_cond": 110.0, "Eg_eV_min": 2.23, "Eg_eV_max": 2.78, "FM": 20.6},
        "status": "candidate",
        "ref": "SHG @ 10.6 um; values compiled from [70,71]"
    },
    {
        "material": "ZnSe",
        "cur": "ZnSe (cubic form)", "nxt": "OPGaAs was the first",
        "label": "Table 3, row ZnSe",
        "quote": "ZnSe (cubic form) | -43m | Transp: 0.55-20 um | Thermal cond: 18-19 W/mK | Eg: 2.58-2.7 eV direct | d14: 26.4 pm/V (SHG @ 10.6 um) | FM: 20 pm2/V2",
        "values": {"d14": 26.4, "unit": "pm/V", "wavelength_um": 10.6, "transparency_min_um": 0.55, "transparency_max_um": 20.0, "thermal_cond_min": 18.0, "thermal_cond_max": 19.0, "Eg_eV_min": 2.58, "Eg_eV_max": 2.7, "FM": 20.0},
        "status": "candidate",
        "ref": "SHG @ 10.6 um; cubic form"
    }
]

for r in rows_2015_t3_def:
    raw_q = get_raw_2015_p33(r["cur"], r["nxt"])
    records.append({
        "task": "dij",
        "material": r["material"],
        "doc_id": doc_2015,
        "pdf_file": pdf_2015,
        "pdf_page": 33,
        "label": r["label"],
        "quote": r["quote"],
        "raw_quote": raw_q,
        "values": r["values"],
        "frame_quote": frame_quote_2015_t3,
        "status": r["status"],
        "note": r["ref"]
    })

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for rec in records:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"Successfully wrote {len(records)} records with raw_quote to {OUTPUT_FILE}")
