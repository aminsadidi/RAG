#!/usr/bin/env python3
"""
Task 2: Review and verbatim transcription of tables in Petrov 2012 and Petrov 2015.
Files:
  - petrov2012.pdf (Table 2)
  - petrov2015.pdf (Table 2 and Table 3)
Output: research_package/candidates/petrov_tables.jsonl
"""

import os
import json

CANDIDATES_DIR = "/home/aminsadidi11584/RAG/research_package/candidates"
os.makedirs(CANDIDATES_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(CANDIDATES_DIR, "petrov_tables.jsonl")

records = []

# =============================================================================
# PETROV 2012 (Optical Materials 34 (2012) 536-554, DOI: 10.1016/j.mser.2012.04.001)
# Table 2, Page 6 (PDF page 6)
# =============================================================================
caption_2012 = (
    "Table 2. Summary of important properties of birefringent NLCs that can be pumped at 1064 nm to generate 6.45 um light: "
    "The effective nonlinearity deff (column 3) is calculated at the corresponding phase-matching angle theta or phi (column 2), "
    "the nonlinear tensor components, dil, used for this calculation were derived from the literature (column 6) applying "
    "Miller's rule (column 7). The wavelength lambda_F (fundamental) at which the nonlinear coefficients have been estimated "
    "by SHG is also shown in column 6. For Sn2P2S6, deff is taken directly from the literature [9]."
)
footnote_2012 = "* Crystals for which OPO with ~1 um pump wavelength has been already demonstrated."
doc_2012 = "10.1016/j.mser.2012.04.001"
pdf_2012 = "petrov2012.pdf"

rows_2012 = [
    {
        "material": "AgGaS2",
        "label": "Table 2, row AgGaS2",
        "quote": "AgGaS2* | -42m | 40.50 (oo-e) deff=8.86 | 45.53 (eo-e) deff=13.65 | Thermal cond: 1.4 // c, 1.5 perp c [W/mK] | Eg=2.70 eV | delta_36=0.12 [pm/V] | d36=13.65 [pm/V] +Miller",
        "values": {"d36": 13.65, "unit": "pm/V", "deff_oo_e": 8.86, "deff_eo_e": 13.65, "theta_oo_e_deg": 40.50, "theta_eo_e_deg": 45.53, "Eg_eV": 2.70},
        "ref": "Literature standard d36 derived from Miller's delta=0.12 pm/V"
    },
    {
        "material": "HgGa2S4",
        "label": "Table 2, row HgGa2S4",
        "quote": "HgGa2S4* | -4 | 45.87 (oo-e) deff=15.57 | 51.21 (eo-e) deff=21.18 | Thermal cond: 2.49-2.85 // c, 2.36-2.31 perp c | Eg=2.79 eV | d36=27.2 @ 1064 nm | d36=24.56 +Miller",
        "values": {"d36": 27.2, "d36_miller": 24.56, "unit": "pm/V", "wavelength_um": 1.064, "deff_oo_e": 15.57, "deff_eo_e": 21.18, "Eg_eV": 2.79},
        "ref": "SHG @ 1064 nm d36=27.2 pm/V"
    },
    {
        "material": "CdxHg1-xGa2S4",
        "label": "Table 2, row CdxHg1-xGa2S4",
        "quote": "CdxHg1-xGa2S4* (theta=90°, x=0.55) | -4 (x=0.27-0.3) | 90.00 (oo-e) deff=24.94 | Thermal cond: 1.8-1.92 // c, 1.62-1.81 perp c | Eg=3.22 (x=0.55) | d36=27.2 @ 1064 nm | d36=24.94 +Miller",
        "values": {"d36": 27.2, "d36_miller": 24.94, "unit": "pm/V", "wavelength_um": 1.064, "deff_oo_e": 24.94, "theta_deg": 90.0, "x_composition": 0.55, "Eg_eV": 3.22},
        "ref": "Composition x=0.55 NCPM OPO; d36 estimated from parent HGS"
    },
    {
        "material": "LiGaS2",
        "label": "Table 2, row LiGaS2",
        "quote": "LiGaS2 | mm2 | xz 47.77 (oo-e) deff=4.23 | xy 40.36 (eo-e) deff=5.50 | Thermal cond: NA | Eg=3.76 eV | d31=5.8, d24=5.1 @ 2300 nm | d31=5.71, d24=5.21 +Miller",
        "values": {"d31": 5.8, "d24": 5.1, "d31_miller": 5.71, "d24_miller": 5.21, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 4.23, "deff_eo_e": 5.50, "Eg_eV": 3.76},
        "ref": "SHG @ 2300 nm (2.3 um) literature measurements"
    },
    {
        "material": "LiInS2",
        "label": "Table 2, row LiInS2",
        "quote": "LiInS2 | mm2 | xz 40.01 (oo-e) deff=4.65 | xy 36.37 (eo-e) deff=6.77 | Thermal cond: 6.2 // x, 6.0 // y, 7.6 // z | Eg=3.57 eV | d31=7.25, d24=5.66 @ 2300 nm | d31=7.23, d24=5.93 +Miller",
        "values": {"d31": 7.25, "d24": 5.66, "d31_miller": 7.23, "d24_miller": 5.93, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 4.65, "deff_eo_e": 6.77, "Eg_eV": 3.57},
        "ref": "SHG @ 2300 nm (2.3 um), Fossier et al. (2004)"
    },
    {
        "material": "LiGaSe2",
        "label": "Table 2, row LiGaSe2",
        "quote": "LiGaSe2 | mm2 | xz 51.45 (oo-e) deff=7.82 | xy 37.61 (eo-e) deff=9.31 | Thermal cond: NA | Eg=3.65 eV | d31=9.9, d24=7.7 @ 2300 nm | d31=10, d24=8.16 +Miller",
        "values": {"d31": 9.9, "d24": 7.7, "d31_miller": 10.0, "d24_miller": 8.16, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 7.82, "deff_eo_e": 9.31, "Eg_eV": 3.65},
        "ref": "SHG @ 2300 nm (2.3 um)"
    },
    {
        "material": "LiInSe2",
        "label": "Table 2, row LiInSe2",
        "quote": "LiInSe2* | mm2 | xz 36.97 (oo-e) deff=7.26 | xy 41.62 (eo-e) deff=10.57 | Thermal cond: 4.7-4.5 // x, 4.7-4.8 // y, 5.5-5.8 // z | Eg=2.86 eV | d31=11.78, d24=8.17 @ 2300 nm | d31=12.08, d24=8.65 +Miller",
        "values": {"d31": 11.78, "d24": 8.17, "d31_miller": 12.08, "d24_miller": 8.65, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 7.26, "deff_eo_e": 10.57, "Eg_eV": 2.86},
        "ref": "SHG @ 2300 nm (2.3 um), Petrov et al. (2010)"
    },
    {
        "material": "LiGaTe2",
        "label": "Table 2, row LiGaTe2",
        "quote": "LiGaTe2 | -42m | 36.38 (ee-o) deff=46.20 | 40.05 (oe-o) deff=31.12 | Thermal cond: NA | Eg=2.41 eV | d36=43 @ 4600 nm | d36=48.37 +Miller",
        "values": {"d36": 43.0, "d36_miller": 48.37, "unit": "pm/V", "wavelength_um": 4.6, "deff_ee_o": 46.20, "deff_oe_o": 31.12, "Eg_eV": 2.41},
        "ref": "SHG @ 4600 nm (4.6 um)"
    },
    {
        "material": "BaGa4S7",
        "label": "Table 2, row BaGa4S7",
        "quote": "BaGa4S7 | mm2 | xz 4.64 (oo-e) deff=NA | Thermal cond: NA | Eg=3.54 eV | dil=NA | +Miller=NA",
        "values": {"theta_oo_e_deg": 4.64, "Eg_eV": 3.54},
        "ref": "Crystal properties reported in [19]; nonlinearity unknown at time of Petrov 2012"
    },
    {
        "material": "BaGa4Se7",
        "label": "Table 2, row BaGa4Se7",
        "quote": "BaGa4Se7 | m | yz 30.30 (oe-o) | xz 50.68 (ee-o) | xz 54.38 (oe-o) deff=NA | Thermal cond: NA | Eg=2.64 eV | dil=NA | +Miller=NA",
        "values": {"theta_yz_deg": 30.30, "theta_xz_ee_o_deg": 50.68, "theta_xz_oe_o_deg": 54.38, "Eg_eV": 2.64},
        "ref": "Crystal properties reported in [19]; nonlinearity unknown at time of Petrov 2012"
    },
    {
        "material": "InPS4",
        "label": "Table 2, row InPS4",
        "quote": "InPS4 | -4 | 38.80 (ee-o) deff=34.40 | 42.67 (oe-o) deff=23.87 @ optimum phi | Thermal cond: NA | Eg=3.2 eV | delta_31=0.39, delta_36=0.30 | d31=27.87, d36=21.53 +Miller",
        "values": {"delta_31": 0.39, "delta_36": 0.30, "d31": 27.87, "d36": 21.53, "unit": "pm/V", "deff_ee_o": 34.40, "deff_oe_o": 23.87, "Eg_eV": 3.2},
        "ref": "Miller delta values delta_31=0.39, delta_36=0.30"
    },
    {
        "material": "Sn2P2S6",
        "label": "Table 2, row Sn2P2S6",
        "quote": "Sn2P2S6 | m | (ss-f) deff approx 4 | (fs-f) deff approx 2 | Thermal cond: 0.4-0.55 | Eg=2.35 eV | dil: ... | +Miller: ...",
        "values": {"deff_ss_f": 4.0, "deff_fs_f": 2.0, "unit": "pm/V", "Eg_eV": 2.35},
        "ref": "deff taken directly from literature [9] (Haertle et al.)"
    },
    {
        "material": "GaS0.4Se0.6",
        "label": "Table 2, row GaS0.4Se0.6",
        "quote": "GaS0.4Se0.6 | -62m | 22.31 (oo-e) deff=45.80 | 24.67 (eo-e) deff=40.88 | Thermal cond: 1.3 // c, 10 perp c | Eg=2.4 eV | d22=44.1 @ 4.65 um | d22=49.51 +Miller",
        "values": {"d22": 44.1, "d22_miller": 49.51, "unit": "pm/V", "wavelength_um": 4.65, "deff_oo_e": 45.80, "deff_eo_e": 40.88, "Eg_eV": 2.4},
        "ref": "SHG @ 4.65 um"
    },
    {
        "material": "CdSiP2",
        "label": "Table 2, row CdSiP2",
        "quote": "CdSiP2* | -42m | 80.46 (oo-e) deff=90.99 | Thermal cond: 13.6 | Eg=2.2-2.45 eV | d36=84.5 @ 4.56 um | d36=92.27 +Miller",
        "values": {"d36": 84.5, "d36_miller": 92.27, "unit": "pm/V", "wavelength_um": 4.56, "deff_oo_e": 90.99, "theta_oo_e_deg": 80.46, "Eg_eV": 2.45},
        "ref": "SHG @ 4.56 um, Schunemann et al. (2010)"
    },
    {
        "material": "AgGaGeS4",
        "label": "Table 2, row AgGaGeS4",
        "quote": "AgGaGeS4 | mm2 | xz 53.99 (oo-e) deff=3.32 | xy 35.74 (oo-e) deff=5.43 | Thermal cond: 0.399 | Eg=3.0 eV | d32=6.2, d31=10.2 @ 1064 nm | d32=5.65, d31=9.30 +Miller",
        "values": {"d32": 6.2, "d31": 10.2, "d32_miller": 5.65, "d31_miller": 9.30, "unit": "pm/V", "wavelength_um": 1.064, "deff_xz": 3.32, "deff_xy": 5.43, "Eg_eV": 3.0},
        "ref": "SHG @ 1064 nm"
    },
    {
        "material": "Ag3AsS3",
        "label": "Table 2, row Ag3AsS3 (Proustite)",
        "quote": "Ag3AsS3* | 3m | 22.04 (oo-e) deff=22.89 | 24.01 (eo-e) deff=16.44 | 65.63 (oe-e) deff=3.35 | Thermal cond: 0.113 // c, 0.092 perp c | Eg=2.2 eV | d31=10.4, d22=16.6 @ 10.6 um | d31=12.34, d22=19.70 +Miller",
        "values": {"d31": 10.4, "d22": 16.6, "d31_miller": 12.34, "d22_miller": 19.70, "unit": "pm/V", "wavelength_um": 10.6, "deff_oo_e": 22.89, "deff_eo_e": 16.44, "Eg_eV": 2.2},
        "ref": "SHG @ 10.6 um"
    },
    {
        "material": "Ag3SbS3",
        "label": "Table 2, row Ag3SbS3 (Pyrargyrite)",
        "quote": "Ag3SbS3 | 3m | 47.14 (oo-e) deff=14.34 | 52.84 (eo-e) deff=3.80 | Thermal cond: ~0.1 // c, ~0.09 perp c | Eg=2.2 eV | d31=7.8, d22=8.2 @ 10.6 um | d31=9.90, d22=10.41 +Miller",
        "values": {"d31": 7.8, "d22": 8.2, "d31_miller": 9.90, "d22_miller": 10.41, "unit": "pm/V", "wavelength_um": 10.6, "deff_oo_e": 14.34, "deff_eo_e": 3.80, "Eg_eV": 2.2},
        "ref": "SHG @ 10.6 um"
    }
]

for r in rows_2012:
    records.append({
        "task": "dij",
        "material": r["material"],
        "doc_id": doc_2012,
        "pdf_file": pdf_2012,
        "pdf_page": 6,
        "label": r["label"],
        "quote": r["quote"],
        "values": r["values"],
        "frame_quote": caption_2012 + " " + footnote_2012,
        "status": "candidate",
        "note": r["ref"]
    })

# =============================================================================
# PETROV 2015 (Prog. Quantum Electron. 42 (2015) 1-105, DOI: 10.1016/j.pquantelec.2015.04.001)
# Table 2, Pages 30-31 (PDF pages 30-31)
# =============================================================================
caption_2015_t2 = (
    "Table 2. Summary of important properties of birefringent NLCs that can be pumped at 1.064 um to generate "
    "6.45 um light: The effective nonlinearity deff (column 3) is calculated at the corresponding PM angle theta or phi "
    "(column 2), the nonlinear tensor components, dil, used for this calculation were derived from the literature (column "
    "6) applying Miller's rule (column 7). The wavelength lambda_F (fundamental) at which the nonlinear coefficients have "
    "been estimated by SHG is also shown in column 6. For Sn2P2S6, deff is taken directly from the literature [49]."
)
footnote_2015_t2 = (
    "*crystals for which OPO with ~1 um pump wavelength has been already demonstrated, "
    "**more general notations outside the principal planes of biaxial crystals [5], angles and dil components omitted for simplicity (...); NA: not available"
)
doc_2015 = "10.1016/j.pquantelec.2015.04.001"
pdf_2015 = "petrov2015.pdf"

rows_2015_t2 = [
    {
        "material": "AgGaS2",
        "pdf_page": 30,
        "label": "Table 2, row AgGaS2",
        "quote": "AgGaS2* | -42m | 40.50 (oo-e) deff=8.86 | 45.53 (eo-e) deff=13.65 | Thermal cond: 1.4 // c, 1.5 perp c | Eg=2.70 eV | delta_36=0.12 | d36=13.65 +Miller",
        "values": {"d36": 13.65, "unit": "pm/V", "deff_oo_e": 8.86, "deff_eo_e": 13.65, "theta_oo_e_deg": 40.50, "theta_eo_e_deg": 45.53, "Eg_eV": 2.70},
        "ref": "Literature standard d36 derived from Miller's delta=0.12 pm/V"
    },
    {
        "material": "HgGa2S4",
        "pdf_page": 30,
        "label": "Table 2, row HgGa2S4",
        "quote": "HgGa2S4* | -4 | 45.87 (oo-e) deff=15.57 | 51.21 (eo-e) deff=21.18 | Thermal cond: 2.49-2.85 // c, 2.36-2.31 perp c | Eg=2.79 eV | d36=27.2 @ 1.064 um | d36=24.56 +Miller",
        "values": {"d36": 27.2, "d36_miller": 24.56, "unit": "pm/V", "wavelength_um": 1.064, "deff_oo_e": 15.57, "deff_eo_e": 21.18, "Eg_eV": 2.79},
        "ref": "SHG @ 1.064 um d36=27.2 pm/V"
    },
    {
        "material": "CdxHg1-xGa2S4",
        "pdf_page": 30,
        "label": "Table 2, row CdxHg1-xGa2S4",
        "quote": "CdxHg1-xGa2S4* (theta=90°, x=0.55) | -4 (x=0.27-0.3) | 90.00 (oo-e) deff=24.94 | Thermal cond: 1.8-1.92 // c, 1.62-1.81 perp c | Eg=3.22 (x=0.55) | d36=27.2 @ 1.064 um | d36=24.94 +Miller",
        "values": {"d36": 27.2, "d36_miller": 24.94, "unit": "pm/V", "wavelength_um": 1.064, "deff_oo_e": 24.94, "theta_deg": 90.0, "x_composition": 0.55, "Eg_eV": 3.22},
        "ref": "Composition x=0.55 NCPM OPO; d36 from HGS"
    },
    {
        "material": "LiGaS2",
        "pdf_page": 30,
        "label": "Table 2, row LiGaS2",
        "quote": "LiGaS2* | mm2 | XZ 47.77 (oo-e) deff=4.23 | XY 40.36 (eo-e) deff=5.50 | Thermal cond: NA | Eg=3.76 eV | d31=5.8, d24=5.1 @ 2.3 um | d31=5.71, d24=5.21 +Miller",
        "values": {"d31": 5.8, "d24": 5.1, "d31_miller": 5.71, "d24_miller": 5.21, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 4.23, "deff_eo_e": 5.50, "Eg_eV": 3.76},
        "ref": "SHG @ 2.3 um"
    },
    {
        "material": "LiInS2",
        "pdf_page": 30,
        "label": "Table 2, row LiInS2",
        "quote": "LiInS2 | mm2 | XZ 40.01 (oo-e) deff=4.65 | XY 36.37 (eo-e) deff=6.77 | Thermal cond: 6.2 // x, 6.0 // y, 7.6 // z | Eg=3.57 eV | d31=7.25, d24=5.66 @ 2.3 um | d31=7.23, d24=5.93 +Miller",
        "values": {"d31": 7.25, "d24": 5.66, "d31_miller": 7.23, "d24_miller": 5.93, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 4.65, "deff_eo_e": 6.77, "Eg_eV": 3.57},
        "ref": "SHG @ 2.3 um, Fossier et al. (2004)"
    },
    {
        "material": "LiGaSe2",
        "pdf_page": 30,
        "label": "Table 2, row LiGaSe2",
        "quote": "LiGaSe2 | mm2 | XZ 51.45 (oo-e) deff=7.82 | XY 37.61 (eo-e) deff=9.31 | Thermal cond: NA | Eg=3.65 eV | d31=9.9, d24=7.7 @ 2.3 um | d31=10, d24=8.16 +Miller",
        "values": {"d31": 9.9, "d24": 7.7, "d31_miller": 10.0, "d24_miller": 8.16, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 7.82, "deff_eo_e": 9.31, "Eg_eV": 3.65},
        "ref": "SHG @ 2.3 um"
    },
    {
        "material": "LiInSe2",
        "pdf_page": 30,
        "label": "Table 2, row LiInSe2",
        "quote": "LiInSe2* | mm2 | XZ 36.97 (oo-e) deff=7.26 | XY 41.62 (eo-e) deff=10.57 | Thermal cond: 4.7-4.5 // x, 4.7-4.8 // y, 5.5-5.8 // z | Eg=2.86 eV | d31=11.78, d24=8.17 @ 2.3 um | d31=12.08, d24=8.65 +Miller",
        "values": {"d31": 11.78, "d24": 8.17, "d31_miller": 12.08, "d24_miller": 8.65, "unit": "pm/V", "wavelength_um": 2.3, "deff_oo_e": 7.26, "deff_eo_e": 10.57, "Eg_eV": 2.86},
        "ref": "SHG @ 2.3 um, Petrov et al. (2010)"
    },
    {
        "material": "LiGaTe2",
        "pdf_page": 30,
        "label": "Table 2, row LiGaTe2",
        "quote": "LiGaTe2 | -42m | 36.38 (ee-o) deff=46.20 | 40.05 (oe-o) deff=31.12 | Thermal cond: NA | Eg=2.41 eV | d36=43 @ 4.6 um | d36=48.37 +Miller",
        "values": {"d36": 43.0, "d36_miller": 48.37, "unit": "pm/V", "wavelength_um": 4.6, "deff_ee_o": 46.20, "deff_oe_o": 31.12, "Eg_eV": 2.41},
        "ref": "SHG @ 4.6 um"
    },
    {
        "material": "BaGa4S7",
        "pdf_page": 30,
        "label": "Table 2, row BaGa4S7",
        "quote": "BaGa4S7* | mm2 | XZ 10.47 (oo-e) deff=4.99 | Thermal cond: 1.68 // x, 1.58 // y, 1.45 // z | Eg=3.54 eV | d31=5.1 @ 2.26 um | d31=5.07 +Miller",
        "values": {"d31": 5.1, "d31_miller": 5.07, "unit": "pm/V", "wavelength_um": 2.26, "deff_oo_e": 4.99, "theta_oo_e_deg": 10.47, "Eg_eV": 3.54},
        "ref": "SHG @ 2.26 um"
    },
    {
        "material": "BaGa4Se7",
        "pdf_page": 30,
        "label": "Table 2, row BaGa4Se7",
        "quote": "BaGa4Se7 | m | YZ 30.30 (oe-o) | XZ 50.68 (ee-o) | XZ 54.38 (oe-o) deff=NA | Thermal cond: 0.56-0.74 | Eg=2.64 eV | dil=NA | +Miller=NA",
        "values": {"theta_yz_deg": 30.30, "theta_xz_ee_o_deg": 50.68, "theta_xz_oe_o_deg": 54.38, "Eg_eV": 2.64},
        "ref": "Nonlinearity not yet quantified in Table 2"
    },
    {
        "material": "InPS4",
        "pdf_page": 30,
        "label": "Table 2, row InPS4",
        "quote": "InPS4 | -4 | 38.80 (ee-o) deff=34.40 | 42.67 (oe-o) deff=23.87 @ optimum phi | Thermal cond: NA | Eg=3.2 eV | delta_31=0.39, delta_36=0.30 | d31=27.87, d36=21.53 +Miller",
        "values": {"delta_31": 0.39, "delta_36": 0.30, "d31": 27.87, "d36": 21.53, "unit": "pm/V", "deff_ee_o": 34.40, "deff_oe_o": 23.87, "Eg_eV": 3.2},
        "ref": "Miller delta values delta_31=0.39, delta_36=0.30"
    },
    {
        "material": "Sn2P2S6",
        "pdf_page": 30,
        "label": "Table 2, row Sn2P2S6",
        "quote": "Sn2P2S6 | m | (ss-f)** deff approx 4 | (fs-f)** deff approx 2 | Thermal cond: 0.4-0.55 | Eg=2.35 eV | dil: ... | +Miller: ...",
        "values": {"deff_ss_f": 4.0, "deff_fs_f": 2.0, "unit": "pm/V", "Eg_eV": 2.35},
        "ref": "deff taken directly from literature [49] (Haertle et al.)"
    },
    {
        "material": "GaS0.4Se0.6",
        "pdf_page": 30,
        "label": "Table 2, row GaS0.4Se0.6",
        "quote": "GaS0.4Se0.6 | -62m | 22.31 (oo-e) deff=45.80 | 24.67 (eo-e) deff=40.88 | Thermal cond: 1.3 // c, 10 perp c | Eg=2.4 eV | d22=44.1 @ 4.65 um | d22=49.51 +Miller",
        "values": {"d22": 44.1, "d22_miller": 49.51, "unit": "pm/V", "wavelength_um": 4.65, "deff_oo_e": 45.80, "deff_eo_e": 40.88, "Eg_eV": 2.4},
        "ref": "SHG @ 4.65 um"
    },
    {
        "material": "CdSiP2",
        "pdf_page": 31,
        "label": "Table 2, row CdSiP2",
        "quote": "CdSiP2* | -42m | 80.46 (oo-e) deff=90.99 | Thermal cond: 13.6 | Eg=2.2-2.45 eV | d36=84.5 @ 4.56 um | d36=92.27 +Miller",
        "values": {"d36": 84.5, "d36_miller": 92.27, "unit": "pm/V", "wavelength_um": 4.56, "deff_oo_e": 90.99, "theta_oo_e_deg": 80.46, "Eg_eV": 2.45},
        "ref": "SHG @ 4.56 um, Schunemann et al. (2010)"
    },
    {
        "material": "AgGaGeS4",
        "pdf_page": 31,
        "label": "Table 2, row AgGaGeS4",
        "quote": "AgGaGeS4 | mm2 | XZ 53.99 (oo-e) deff=3.32 | XY 35.74 (oo-e) deff=5.43 | Thermal cond: 0.399 | Eg=3.0 eV | d32=6.2, d31=10.2 @ 1.064 um | d32=5.65, d31=9.30 +Miller",
        "values": {"d32": 6.2, "d31": 10.2, "d32_miller": 5.65, "d31_miller": 9.30, "unit": "pm/V", "wavelength_um": 1.064, "deff_xz": 3.32, "deff_xy": 5.43, "Eg_eV": 3.0},
        "ref": "SHG @ 1.064 um"
    },
    {
        "material": "Ag3AsS3",
        "pdf_page": 31,
        "label": "Table 2, row Ag3AsS3 (Proustite)",
        "quote": "Ag3AsS3* | 3m | 22.04 (oo-e) deff=22.89 | 24.01 (eo-e) deff=16.44 | 65.63 (oe-e) deff=3.35 | Thermal cond: 0.113 // c, 0.092 perp c | Eg=2.2 eV | d31=10.4, d22=16.6 @ 10.6 um | d31=12.34, d22=19.70 +Miller",
        "values": {"d31": 10.4, "d22": 16.6, "d31_miller": 12.34, "d22_miller": 19.70, "unit": "pm/V", "wavelength_um": 10.6, "deff_oo_e": 22.89, "deff_eo_e": 16.44, "Eg_eV": 2.2},
        "ref": "SHG @ 10.6 um"
    },
    {
        "material": "Ag3SbS3",
        "pdf_page": 31,
        "label": "Table 2, row Ag3SbS3 (Pyrargyrite)",
        "quote": "Ag3SbS3 | 3m | 47.14 (oo-e) deff=14.34 | 52.84 (eo-e) deff=3.80 | Thermal cond: ~0.1 // c, ~0.09 perp c | Eg=2.2 eV | d31=7.8, d22=8.2 @ 10.6 um | d31=9.90, d22=10.41 +Miller",
        "values": {"d31": 7.8, "d22": 8.2, "d31_miller": 9.90, "d22_miller": 10.41, "unit": "pm/V", "wavelength_um": 10.6, "deff_oo_e": 14.34, "deff_eo_e": 3.80, "Eg_eV": 2.2},
        "ref": "SHG @ 10.6 um"
    }
]

for r in rows_2015_t2:
    records.append({
        "task": "dij",
        "material": r["material"],
        "doc_id": doc_2015,
        "pdf_file": pdf_2015,
        "pdf_page": r["pdf_page"],
        "label": r["label"],
        "quote": r["quote"],
        "values": r["values"],
        "frame_quote": caption_2015_t2 + " " + footnote_2015_t2,
        "status": "candidate",
        "note": r["ref"]
    })

# =============================================================================
# PETROV 2015 Table 3, Page 33 (PDF page 33)
# =============================================================================
caption_2015_t3 = (
    "Table 3. Important properties of cubic semiconductor NLCs investigated for QPM. A lot of data but also a lot of "
    "scatter in the values exist in the corresponding literature. The table is compiled on a best effort basis using some "
    "values from [70,71]. Only for GaAs the d14 value has been refined from SHG measurements with OPGaAs."
)
footnote_2015_t3 = "Cubic point group -43m (43m in symbol font). FM = (2 d14 / pi)^2 / n^3."

rows_2015_t3 = [
    {
        "material": "GaAs",
        "label": "Table 3, row GaAs",
        "quote": "GaAs | -43m | Transparency: 0.85-18.5 um at 3 cm^-1 | Thermal cond: 55 W/mK | Band-gap Eg: 1.42-1.435 eV direct | d14: 83-86 pm/V SHG @ 10.6 um | FM=(2 d14 / pi)^2 / n^3: 78-83 pm^2/V^2",
        "values": {"d14_min": 83.0, "d14_max": 86.0, "d14": 84.5, "unit": "pm/V", "wavelength_um": 10.6, "Eg_eV": 1.42, "thermal_cond_W_mK": 55.0, "FM_pm2_V2": 80.5},
        "ref": "Refined from SHG measurements with OPGaAs, [70,71]"
    },
    {
        "material": "GaP",
        "label": "Table 3, row GaP",
        "quote": "GaP | -43m | Transparency: 0.57-13.2 um at 3 cm^-1 | Thermal cond: 110 W/mK | Band-gap Eg: 2.23-2.78 eV indirect/direct | d14: 37 pm/V SHG @ 10.6 um | FM=(2 d14 / pi)^2 / n^3: 20.6 pm^2/V^2",
        "values": {"d14": 37.0, "unit": "pm/V", "wavelength_um": 10.6, "Eg_eV": 2.23, "thermal_cond_W_mK": 110.0, "FM_pm2_V2": 20.6},
        "ref": "Compiled on best effort basis from [70,71]"
    },
    {
        "material": "ZnSe",
        "label": "Table 3, row ZnSe (cubic form)",
        "quote": "ZnSe (cubic form) | -43m | Transparency: 0.55-20 um at 3 cm^-1 | Thermal cond: 18-19 W/mK | Band-gap Eg: 2.58-2.7 eV direct | d14: 26.4 pm/V SHG @ 10.6 um | FM=(2 d14 / pi)^2 / n^3: 20 pm^2/V^2",
        "values": {"d14": 26.4, "unit": "pm/V", "wavelength_um": 10.6, "Eg_eV": 2.58, "thermal_cond_W_mK": 18.5, "FM_pm2_V2": 20.0},
        "ref": "Compiled on best effort basis from [70,71]"
    }
]

for r in rows_2015_t3:
    records.append({
        "task": "dij",
        "material": r["material"],
        "doc_id": doc_2015,
        "pdf_file": pdf_2015,
        "pdf_page": 33,
        "label": r["label"],
        "quote": r["quote"],
        "values": r["values"],
        "frame_quote": caption_2015_t3 + " " + footnote_2015_t3,
        "status": "candidate",
        "note": r["ref"]
    })

print(f"Total transcribed Petrov table rows: {len(records)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for rec in records:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"Saved {len(records)} records to {OUTPUT_FILE}")
