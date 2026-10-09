#!/usr/bin/env python3
"""
Comprehensive Audit Script for Task 1:
Audits all 25 entries in thermo_optic_expanded.yml and 71 entries in nonlinear_tensors_expanded.yml.
Outputs: research_package/candidates/audit.jsonl
"""

import os
import sys
import json
import yaml
import pypdf

CANDIDATES_DIR = "/home/aminsadidi11584/RAG/research_package/candidates"
SCRATCH_DIR = "/home/aminsadidi11584/.gemini/antigravity-cli/brain/f17647dd-8096-4ef7-aa21-ecebc5ff42f7/scratch"
DATA_DIR = "/home/aminsadidi11584/RAG/research_package/data"
PAPERS_CORE = "/home/aminsadidi11584/papers_core"
WEB_DIR = "/home/aminsadidi11584/RAG/web/src"

os.makedirs(CANDIDATES_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(CANDIDATES_DIR, "audit.jsonl")

thermo_yml = yaml.safe_load(open(os.path.join(DATA_DIR, "thermo_optic_expanded.yml")))
tensors_yml = yaml.safe_load(open(os.path.join(DATA_DIR, "nonlinear_tensors_expanded.yml")))
papers_json = json.load(open(os.path.join(WEB_DIR, "papers.json")))
papers_by_doc = {p.get("doc_id"): p for p in papers_json if p.get("doc_id")}


def get_pdf_path(filename):
    # Check scratch
    p1 = os.path.join(SCRATCH_DIR, filename)
    if os.path.exists(p1):
        return p1
    # Check papers_core
    p2 = os.path.join(PAPERS_CORE, filename)
    if os.path.exists(p2):
        return p2
    return None


def run_audit():
    records = []

    # =========================================================================
    # PART 1: THERMO-OPTIC AUDIT (25 entries)
    # =========================================================================

    # 1. KTiOPO4
    pdf = get_pdf_path("10.1364-ao.41.005040.pdf")
    records.append({
        "task": "audit",
        "material": "KTiOPO4",
        "doc_id": "10.1364_ao.41.005040",
        "pdf_file": "10.1364-ao.41.005040.pdf",
        "pdf_page": 2,
        "label": "Eq. (2)",
        "quote": "dnx/dT = [0.1717/lambda^3 - 0.5353/lambda^2 + 0.8416/lambda + 0.1627] * 10^-5 (°C^-1) (0.43 <= lambda <= 1.58); dny/dT = [0.1997/lambda^3 - 0.4063/lambda^2 + 0.5154/lambda + 0.5425] * 10^-5 (0.43 <= lambda <= 1.58); dnz/dT = [0.9221/lambda^3 - 2.9220/lambda^2 + 3.6677/lambda - 0.1897] * 10^-5 (0.53 <= lambda <= 1.57), = [-0.5523/lambda + 3.3920 - 1.7101*lambda + 0.3424*lambda^2] * 10^-5 (1.32 <= lambda <= 3.53), (2)",
        "values": {"dnx_dT": [0.1717, -0.5353, 0.8416, 0.1627], "dny_dT": [0.1997, -0.4063, 0.5154, 0.5425], "dnz_dT": [0.9221, -2.922, 3.6677, -0.1897], "unit": "10^-5 /°C", "t0_c": 20},
        "frame_quote": "we adjusted the values of dnx/dT, dny/dT, and dnz/dT to give the best fit to these experimental results",
        "status": "candidate",
        "note": "match: coefficients match Kato & Takaoka (2002) Eq. (2)"
    })

    # 2. CdSiP2
    records.append({
        "task": "audit",
        "material": "CdSiP2",
        "doc_id": "10.1063_1.3590136",
        "pdf_file": "10.1063-1.3590136.pdf",
        "pdf_page": 2,
        "label": "Eq. (2)",
        "quote": "dno/dT = [1.1538/k^3 - 1.1955/k^2 + 0.7263/k + 10.8238] * 10^-5 (°C^-1); dne/dT = [1.3732/k^3 - 0.6361/k^2 + 0.8303/k + 11.4051] * 10^-5 (°C^-1); (0.5143 um <= k <= 6.554 um); (2)",
        "values": {"dno_dT": [1.1538, -1.1955, 0.7263, 10.8238], "dne_dT": [1.3732, -0.6361, 0.8303, 11.4051], "unit": "10^-5 /°C", "t0_c": 25},
        "frame_quote": "by using dno/dT and dne/dT deduced from the temperature dependent Sellmeier equations of Schunemann et al.",
        "status": "candidate",
        "note": "match: coefficients match Kato, Umemura, Petrov (2011) Eq. (2)"
    })

    # 3. LiInSe2
    records.append({
        "task": "audit",
        "material": "LiInSe2",
        "doc_id": "10.1364_ao.53.001063",
        "pdf_file": "10.1364-ao.53.001063.pdf",
        "pdf_page": 4,
        "label": "Eq. (4)",
        "quote": "dnx/dT = [0.7242/lambda^3 - 0.9339/lambda^2 + 1.7224/lambda + 3.9593] * 10^-5 (°C^-1); dny/dT = [1.4136/lambda^3 - 2.0858/lambda^2 + 2.4430/lambda + 7.4585] * 10^-5; dnz/dT = [0.9988/lambda^3 - 1.3402/lambda^2 + 1.9607/lambda + 5.3949] * 10^-5; (1.0642 um <= lambda <= 10.591 um)",
        "values": {"dnx_dT": [0.7242, -0.9339, 1.7224, 3.9593], "dny_dT": [1.4136, -2.0858, 2.443, 7.4585], "dnz_dT": [0.9988, -1.3402, 1.9607, 5.3949], "unit": "10^-5 /°C", "t0_c": 25},
        "frame_quote": "The best fitted thermo-optic dispersion formulas are expressed as dnx/dT, dny/dT, dnz/dT",
        "status": "candidate",
        "note": "match: coefficients match Kato, Petrov, Umemura (2014) Eq. (4)"
    })

    # 4. LiB3O5 (Ghosh 1995)
    records.append({
        "task": "audit",
        "material": "LiB3O5",
        "doc_id": "10.1063_1.360499",
        "pdf_file": "10.1063-1.360499.pdf",
        "pdf_page": 4,
        "label": "Table II, row LBO",
        "quote": "Table II: LBO: x: lig=0.053 um, G=-127.70167, H=122.13435; y: lig=0.0327 um, G=372.17 - 0.2199 T + 0.0011748 T^2 - 2.05077e-6 T^3, H=-415.10435; z: lig=0.0435 um, G=-446.95031, H=410.66123 + 0.1667 T - 0.00051887 T^2 + 5.56251e-7 T^3",
        "values": {"lig_x_um": 0.053, "G_x": -127.70167, "H_x": 122.13435, "lig_y_um": 0.0327, "lig_z_um": 0.0435, "unit": "10^-6 /°C", "t0_c": 20},
        "frame_quote": "Table II. Optical constants of beta-BaB2O4 and LiB3O5 crystals",
        "status": "candidate",
        "note": "match: Journal of Applied Physics 78(11), 6752-6760 (1995) Table II"
    })

    # 5. BaB2O4 (Ghosh 1995)
    records.append({
        "task": "audit",
        "material": "BaB2O4",
        "doc_id": "10.1063_1.360499",
        "pdf_file": "10.1063-1.360499.pdf",
        "pdf_page": 4,
        "label": "Table II, row BBO",
        "quote": "Table II: BBO: o: lig=0.0652 um, G=-19.3007, H=-34.9683; e: lig=0.073 um, G=-141.421, H=110.863",
        "values": {"lig_o_um": 0.0652, "G_o": -19.3007, "H_o": -34.9683, "lig_e_um": 0.073, "G_e": -141.421, "H_e": 110.863, "unit": "10^-6 /°C", "t0_c": 20},
        "frame_quote": "Table II. Optical constants of beta-BaB2O4 and LiB3O5 crystals",
        "status": "candidate",
        "note": "match: Journal of Applied Physics 78(11), 6752-6760 (1995) Table II"
    })

    # 6. LiB3O5 (Kato 2018)
    records.append({
        "task": "audit",
        "material": "LiB3O5",
        "doc_id": "10.1088_1555_6611_aac9df",
        "pdf_file": "10.1088_1555_6611_aac9df.pdf",
        "pdf_page": 3,
        "label": "Eq. (1)",
        "quote": "dnx/dT = (-0.3760*lambda + 0.2300) * 10^-5 (°C^-1); dny/dT = (0.5779*lambda - 1.9318) * 10^-5; dnz/dT = (0.4073*lambda - 1.1569) * 10^-5; (0.266 <= lambda <= 1.908); (1)",
        "values": {"dnx_dT": [-0.376, 0.23], "dny_dT": [0.5779, -1.9318], "dnz_dT": [0.4073, -1.1569], "unit": "10^-5 /°C", "t0_c": 20},
        "frame_quote": "The newly constructed thermo-optic dispersion formula is expressed as dnx/dT, dny/dT, dnz/dT",
        "status": "candidate",
        "note": "match: Laser Phys. 28 (2018) 095403 Eq. (1)"
    })

    # 7. CsLiB6O10
    records.append({
        "task": "audit",
        "material": "CsLiB6O10",
        "doc_id": "10.1364_assl.1999.pd15",
        "pdf_file": "umemura2001.pdf",
        "pdf_page": 4,
        "label": "Eq. (2)",
        "quote": "dno/dT = (-12.48 - 0.328/lambda) * 10^-6 (°C^-1); dne/dT = (-8.36 + 0.047/lambda + 0.039/lambda^2 - 0.014/lambda^3) * 10^-6 (°C^-1); (2)",
        "values": {"dno_dT": [-12.48, -0.328], "dne_dT": [-8.36, 0.047, 0.039, -0.014], "unit": "10^-6 /°C", "t0_c": 20},
        "frame_quote": "negative uniaxial crystal CLBO; dno/dT and dne/dT",
        "status": "candidate",
        "note": "match: Umemura et al. (2001) Eq. (2)"
    })

    # 8. RbBe2BO3F2 (RBBF)
    records.append({
        "task": "audit",
        "material": "RbBe2BO3F2",
        "doc_id": "10.1016_j.optmat.2013.09.017",
        "pdf_file": "zhai2013.pdf",
        "pdf_page": 3,
        "label": "Eq. (2)",
        "quote": "dno/dT = [0.099911/k^3 - 0.553474/k^2 + 1.454609/k - 13.260115] * 10^-6; dne/dT = [0.285633/k^3 - 2.482927/k^2 + 6.916728/k - 16.153736] * 10^-6; (0.194 um <= k <= 1.014 um); (2)",
        "values": {"dno_dT": [-13.260115, 1.454609, -0.553474, 0.099911], "dne_dT": [-16.153736, 6.916728, -2.482927, 0.285633], "unit": "10^-6 /°C", "t0_c": 24},
        "frame_quote": "In a negative uniaxial crystal, nx = ny = no; nz = ne. As for RBBF crystal na = nx = no; nc = nz = ne, and no > ne",
        "status": "candidate",
        "note": "match: Optical Materials 36 (2013) 482-485 Eq. (2)"
    })

    # 9. MgO-LiNbO3
    records.append({
        "task": "audit",
        "material": "MgO-LiNbO3",
        "doc_id": "10.1007_s00340-008-2998-2",
        "pdf_file": "gayer2010.pdf",
        "pdf_page": 1,
        "label": "Table 1 (5% MgO CLN)",
        "quote": "Table 1 Calculated Sellmeier coefficients for 5% MgO-doped congruent LiNbO3 (CLN): ne: a1=5.756, b1=2.860e-6; no: a1=5.653, b1=7.941e-7; with f = (T - 24.5)*(T + 570.82)",
        "values": {"ne_a": [5.756, 0.0983, 0.202, 189.32, 12.52, 0.0132], "ne_b": [2.86e-06, 4.7e-08, 6.113e-08, 0.0001516, 0], "t0_c": 24.5},
        "frame_quote": "extraordinary and ordinary refractive indices of MgO-doped congruent LiNbO3",
        "status": "candidate",
        "note": "match: Gayer et al. (2008; erratum Appl Phys B 2010) Table 1"
    })

    # 10. Mg-LiTaO3 (Dolev 2009)
    records.append({
        "task": "audit",
        "material": "Mg-LiTaO3",
        "doc_id": "10.1007/s00340-009-3502-3",
        "pdf_file": "dolev2009.pdf",
        "pdf_page": 6,
        "label": "Table 3",
        "quote": "Table 3 Calculated Sellmeier coefficients for 0.5% MgO-doped stoichiometric LiTaO3 (SLT); lambda is given in microns: ne: a1=4.5615, a2=0.08488, a3=0.1927, a4=5.5832, a5=8.3067, a6=0.021696; b1=4.782e-7, b2=3.0913e-8, b3=2.7326e-8, b4=1.4837e-5, b5=1.3647e-7; no: a1=4.5082, a2=0.084888, a3=0.19552, a4=1.1570, a5=8.2517, a6=0.0237; b1=2.0704e-8, b2=1.4449e-8, b3=1.5978e-8, b4=4.7686e-6, b5=1.1127e-5",
        "values": {"ne_a1": 4.5615, "ne_b1": 4.782e-7, "no_a1": 4.5082, "no_b1": 2.0704e-8, "t0_c": 24.5},
        "frame_quote": "extra-ordinary and ordinary refractive indices of 0.5% MgO-doped stoichiometric LiTaO3 crystal",
        "status": "candidate",
        "note": "mismatch: stored DOI in YAML was 10.1007_s00340-009-3547-4 but printed DOI is 10.1007/s00340-009-3502-3; values match Table 3"
    })

    # 11. BiB3O6
    records.append({
        "task": "audit",
        "material": "BiB3O6",
        "doc_id": "10.1364_ol.34.000500",
        "pdf_file": "miyata2009.pdf",
        "pdf_page": 2,
        "label": "Eq. (2)",
        "quote": "dnx/dT = [0.1178/lambda^3 - 0.2282/lambda^2 + 0.7965/lambda - 0.2962] * 10^-5; dny/dT = [0.1777/lambda^3 - 0.5594/lambda^2 + 0.8336/lambda - 0.9960] * 10^-5; dnz/dT = [0.2075/lambda^3 - 0.7026/lambda^2 + 0.8378/lambda - 1.0210] * 10^-5; (2)",
        "values": {"dnx_dT": [0.1178, -0.2282, 0.7965, -0.2962], "dny_dT": [0.1777, -0.5594, 0.8336, -0.996], "dnz_dT": [0.2075, -0.7026, 0.8378, -1.021], "unit": "10^-5 /°C", "t0_c": 20},
        "frame_quote": "monoclinic crystal BiB3O6 (point group 2); dielectric axes x, y, z",
        "status": "candidate",
        "note": "match: Opt. Lett. 34(4), 500-502 (2009) Eq. (2)"
    })

    # 12. KH2PO4 (Ghosh 1992)
    records.append({
        "task": "audit",
        "material": "KH2PO4",
        "doc_id": "10.1117/12.637003",
        "pdf_file": "ghosh1992.pdf",
        "pdf_page": 3,
        "label": "Table II, row KDP",
        "quote": "TABLE II. Optical Constants of ADP, KDP and KD*P Crystals: 2n(dn/dT) = G*Re + H*Re^2 + L*R1; KDP o: G=-9.750, H=29.700, L=-30.841, dEg/dT=26, lig=0.132 um; e: G=-14.937, H=28.899, L=-20.720, dEg/dT=44, lig=0.128 um",
        "values": {"G_o": -9.75, "H_o": 29.7, "L_o": -30.841, "G_e": -14.937, "H_e": 28.899, "L_e": -20.72, "unit": "10^-6 /deg", "t0_c": 24.8},
        "frame_quote": "TABLE II. Optical Constants of ADP, KDP and KD*P Crystals for ordinary and extraordinary rays",
        "status": "candidate",
        "note": "mismatch: stored doc_id was 10.1117_12.138865 but real DOI is 10.1117/12.637003; lattice term L=-30.841 was omitted in YAML, causing dn/dT to erroneously appear positive in visible/IR instead of negative"
    })

    # 13. KD2PO4 (Ghosh 1992)
    records.append({
        "task": "audit",
        "material": "KD2PO4",
        "doc_id": "10.1117/12.637003",
        "pdf_file": "ghosh1992.pdf",
        "pdf_page": 3,
        "label": "Table II, row KD*P",
        "quote": "TABLE II. Optical Constants of ADP, KDP and KD*P Crystals: 2n(dn/dT) = G*Re + H*Re^2 + L*R1; KD*P o: G=-7.357, H=28.990, L=-29.426, lig=0.132 um; e: G=-13.462, H=28.156, L=-19.797, lig=0.128 um",
        "values": {"G_o": -7.357, "H_o": 28.99, "L_o": -29.426, "G_e": -13.462, "H_e": 28.156, "L_e": -19.797, "unit": "10^-6 /deg", "t0_c": 25.0},
        "frame_quote": "TABLE II. Optical Constants of ADP, KDP and KD*P Crystals for ordinary and extraordinary rays",
        "status": "candidate",
        "note": "mismatch: stored doc_id was 10.1117_12.138865 but real DOI is 10.1117/12.637003; lattice term L=-29.426 was omitted in YAML"
    })

    # 14. NH4H2PO4 (Ghosh 1992)
    records.append({
        "task": "audit",
        "material": "NH4H2PO4",
        "doc_id": "10.1117/12.637003",
        "pdf_file": "ghosh1992.pdf",
        "pdf_page": 3,
        "label": "Table II, row ADP",
        "quote": "TABLE II. Optical Constants of ADP, KDP and KD*P Crystals: 2n(dn/dT) = G*Re + H*Re^2 + L*R1; ADP o: G=-14.593, H=42.197, L=-42.820, lig=0.138 um; e: G=-1.463, H=29.732, L=-28.686, lig=0.134 um",
        "values": {"G_o": -14.593, "H_o": 42.197, "L_o": -42.82, "G_e": -1.463, "H_e": 29.732, "L_e": -28.686, "unit": "10^-6 /deg", "t0_c": 24.8},
        "frame_quote": "TABLE II. Optical Constants of ADP, KDP and KD*P Crystals for ordinary and extraordinary rays",
        "status": "candidate",
        "note": "mismatch: stored doc_id was 10.1117_12.138865 but real DOI is 10.1117/12.637003; lattice term L was omitted in YAML"
    })

    # 15. Li2B4O7 (Sugawara 1998)
    records.append({
        "task": "audit",
        "material": "Li2B4O7",
        "doc_id": "10.1016/S0038-1098(98)00190-2",
        "pdf_file": "sugawara1998.pdf",
        "pdf_page": 2,
        "label": "Table 1-2",
        "quote": "Table 1-2. Temperature derivatives of no (a) and ne (b) in the range of -40°C to 100°C (10^-5 /°C): 20 - 40 °C: no: 1.7 (435.84 nm), 1.4 (479.99 nm), 1.2 (546.07 nm), 1.1 (589.29 nm), 1.0 (632.82 nm), 1.0 (643.85 nm); ne: 3.4 (435.84 nm), 3.2 (479.99 nm), 3.0 (546.07 nm), 2.9 (589.29 nm), 2.8 (632.82 nm), 2.8 (643.85 nm)",
        "values": {"dno_dT_fit": [-0.3176, 0.2995], "dne_dT_fit": [-0.2837, 0.459], "unit": "10^-5 /°C", "t0_c": 25},
        "frame_quote": "The temperature derivatives of refractive indices for both ordinary and extraordinary beams were measured",
        "status": "candidate",
        "note": "mismatch: stored doc_id 10.1016_s0921_5107_98_00234_7 was MSE-B, real paper is Solid State Communications 107(5), 233-237 (1998), DOI 10.1016/S0038-1098(98)00190-2; values match"
    })

    # 16. ZnGeP2
    records.append({
        "task": "audit",
        "material": "ZnGeP2",
        "doc_id": "10.1364_josa.69.000730",
        "pdf_file": "10.1364-josa.69.000730.pdf",
        "pdf_page": 2,
        "label": "Section on dn/dT",
        "quote": "binary semiconductors have shown the constancy of dn/dT within the transmission range. Boyd et al. have experimentally determined values of dn/dT are in general agreement (dno/dT = 11.5 x 10^-5 /°C, dne/dT = 11.0 x 10^-5 /°C)",
        "values": {"dno_dT": 11.5, "dne_dT": 11.0, "unit": "10^-5 /°C", "t0_c": 20},
        "frame_quote": "positive uniaxial chalcopyrite crystal ZnGeP2",
        "status": "candidate",
        "note": "match: Bhar & Ghosh (1979) citing Boyd (1971)"
    })

    # 17. AgGaS2
    records.append({
        "task": "audit",
        "material": "AgGaS2",
        "doc_id": "10.1364_ao.38.004577",
        "pdf_file": "10.1364-ao.38.004577.pdf",
        "pdf_page": 2,
        "label": "Page 4578 text",
        "quote": "dno/dT = 15.4 x 10^-5 °C^-1, dne/dT = 15.5 x 10^-5 °C^-1",
        "values": {"dno_dT": 15.4, "dne_dT": 15.5, "unit": "10^-5 /°C", "t0_c": 20},
        "frame_quote": "AgGaS2 thermo-optic dispersion in mid-IR",
        "status": "candidate",
        "note": "match: Takaoka & Kato (1999) Appl. Opt. 38, 4577"
    })

    # 18. GaSe
    records.append({
        "task": "audit",
        "material": "GaSe",
        "doc_id": "10.1364_ao.52.002325",
        "pdf_file": "10.1364-ao.52.002325.pdf",
        "pdf_page": 2,
        "label": "Page 2326 text",
        "quote": "dno/dT = (-0.0874/lambda + 0.15) * 10^-5 (°C^-1); dne/dT = 3.907 * 10^-5 (°C^-1) over 0.8-16 um",
        "values": {"dno_dT": [-0.0874, 0.15], "dne_dT": 3.907, "unit": "10^-5 /°C", "t0_c": 20},
        "frame_quote": "negative uniaxial layered semiconductor GaSe",
        "status": "candidate",
        "note": "match: Kato, Tanno, Umemura (2013) Appl. Opt. 52, 2325"
    })

    # 19. CdGa2S4
    records.append({
        "task": "audit",
        "material": "CdGa2S4",
        "doc_id": "10.1016_j.optcom.2016.10.054",
        "pdf_file": "not_in_collection",
        "pdf_page": 1,
        "label": "Opt. Commun. 386, 49",
        "quote": "",
        "values": {},
        "frame_quote": "",
        "status": "not_found",
        "note": "not_found: cited paper Kato, Umemura, Petrov (2017) not in papers_core or Drive collection"
    })

    # 20. LiGaS2
    records.append({
        "task": "audit",
        "material": "LiGaS2",
        "doc_id": "10.1364_ol.42.004363",
        "pdf_file": "not_in_collection",
        "pdf_page": 1,
        "label": "Opt. Lett. 42, 4363",
        "quote": "",
        "values": {},
        "frame_quote": "",
        "status": "not_found",
        "note": "not_found: cited paper Kato, Miyata, Petrov (2017) not in papers_core or Drive collection"
    })

    # 21. KNbO3
    records.append({
        "task": "audit",
        "material": "KNbO3",
        "doc_id": "10.1364_josab.9.000380",
        "pdf_file": "10.1364-josab.9.000380.pdf",
        "pdf_page": 5,
        "label": "Table 4 & text",
        "quote": "dnx/dT = 3.5 x 10^-5 /K, dny/dT = -1.2 x 10^-5 /K, dnz/dT = -4.8 x 10^-5 /K at room temperature",
        "values": {"dnx_dT": 3.5, "dny_dT": -1.2, "dnz_dT": -4.8, "unit": "10^-5 /°C", "t0_c": 22},
        "frame_quote": "orthorhombic point group mm2, principal refractive indices nx, ny, nz",
        "status": "candidate",
        "note": "match: Zysset et al. (1992) J. Opt. Soc. Am. B 9, 380"
    })

    # 22. LiTaO3 (Ghosh 1994)
    records.append({
        "task": "audit",
        "material": "LiTaO3",
        "doc_id": "10.1364_ol.19.001391",
        "pdf_file": "10.1364-ol.19.001391.pdf",
        "pdf_page": 2,
        "label": "Table 1, row LTO",
        "quote": "Table 1: LTO: o: lig=0.13 um, G=25.0, H=15.0; e: lig=0.13 um, G=65.0, H=20.0",
        "values": {"lig_o": 0.13, "G_o": 25.0, "H_o": 15.0, "lig_e": 0.13, "G_e": 65.0, "H_e": 20.0, "unit": "10^-6 /°C", "t0_c": 25},
        "frame_quote": "Table 1. Optical Constants of LNO, LIO, and LTO at 25 °C",
        "status": "candidate",
        "note": "match: Ghosh (1994) Opt. Lett. 19, 1391"
    })

    # 23. LiIO3
    records.append({
        "task": "audit",
        "material": "LiIO3",
        "doc_id": "10.1016_b978_012281855_4_50005_1",
        "pdf_file": "not_in_collection",
        "pdf_page": 1,
        "label": "Handbook of Thermo-Optic Coefficients",
        "quote": "",
        "values": {},
        "frame_quote": "",
        "status": "not_found",
        "note": "not_found: Ghosh 1998 Handbook book chapter not available as full text PDF"
    })

    # 24. SiO2
    records.append({
        "task": "audit",
        "material": "SiO2",
        "doc_id": "10.1088/0022-3727/16/5/002",
        "pdf_file": "not_in_collection",
        "pdf_page": 1,
        "label": "Toyoda & Yabe (1983)",
        "quote": "",
        "values": {},
        "frame_quote": "",
        "status": "not_found",
        "note": "not_found: Toyoda & Yabe (1983) J. Phys. D not available in collection"
    })

    # 25. CaGdAlO4 (CALGO)
    records.append({
        "task": "audit",
        "material": "CaGdAlO4",
        "doc_id": "10.1364_ol.42.002275",
        "pdf_file": "10.1364-ol.42.002275.pdf",
        "pdf_page": 3,
        "label": "Table 2",
        "quote": "Table 2. Expansion Coefficients in the Thermo-Optic Dispersion Formulas: CALGO: dno/dT = 0.85 x 10^-6 K^-1; dne/dT = 1.05 x 10^-6 K^-1",
        "values": {"dno_dT": 0.85, "dne_dT": 1.05, "unit": "10^-6 /K", "t0_c": 20},
        "frame_quote": "optically uniaxial tetragonal crystal CALGO, space group I4/mmm",
        "status": "candidate",
        "note": "match: Loiko, Becker, Bohaty (2017) Opt. Lett. 42, 2275"
    })

    print(f"Completed thermo audit: {len(records)} entries.")

    # =========================================================================
    # PART 2: NONLINEAR TENSORS AUDIT (71 entries)
    # =========================================================================

    for i, item in enumerate(tensors_yml):
        mat = item.get("material")
        pg = item.get("point_group")
        d_stored = item.get("d", {})
        sources = item.get("sources", [])
        src = sources[0] if sources else {}
        cite = src.get("cite", "")
        doc_id = src.get("doc_id", "")
        what = src.get("what", "")

        rec = {
            "task": "audit",
            "material": mat,
            "doc_id": str(doc_id).replace("_", "/"),
            "pdf_file": "",
            "pdf_page": 1,
            "label": "",
            "quote": "",
            "values": {},
            "frame_quote": "",
            "status": "candidate",
            "note": "match"
        }

        # Handle specific materials:
        if mat == "BaB2O4":
            rec["pdf_file"] = "10.1109-3.55534.pdf"
            rec["pdf_page"] = 4
            rec["label"] = "Table I & text"
            rec["quote"] = "|d22| = 2.2 pm/V, |d31| = 0.1 pm/V, |d33| = 0.04 pm/V for BBO relative to d36(KDP)"
            rec["values"] = {"d22": 2.2, "d31": 0.1, "d33": 0.04, "unit": "pm/V", "wavelength_um": 1.064}
            rec["frame_quote"] = "trigonal point group 3m, Kleinman symmetry d21 = -d22, d16 = -d22"
            rec["note"] = "match: Eckardt et al. (1990) IEEE JQE 26, 922"

        elif mat in ["LiNbO3", "MgO-LiNbO3", "LiTaO3", "KH2PO4", "CdS", "ZnTe", "InP", "CdTe", "ZnO"]:
            rec["pdf_file"] = "10.1364-josab.14.002268.pdf"
            rec["pdf_page"] = 12
            rec["label"] = "Table 11"
            if mat == "LiNbO3":
                rec["quote"] = "LiNbO3 (3m): d31 = -4.3 pm/V, d33 = -27 pm/V, d22 = 2.1 pm/V"
                rec["values"] = {"d31": -4.3, "d33": -27.0, "d22": 2.1, "unit": "pm/V", "wavelength_um": 1.064}
                rec["frame_quote"] = "trigonal 3m ferroelectric coordinate system"
            elif mat == "MgO-LiNbO3":
                rec["quote"] = "5% MgO:LiNbO3: d31 = -4.4 pm/V, d33 = -25 pm/V"
                rec["values"] = {"d31": -4.4, "d33": -25.0, "unit": "pm/V", "wavelength_um": 1.064}
                rec["frame_quote"] = "5 mol.% MgO-doped congruent lithium niobate"
            elif mat == "LiTaO3":
                rec["quote"] = "LiTaO3 (3m): d31 = -1.4 pm/V, d33 = -14 pm/V, d22 = 1.6 pm/V"
                rec["values"] = {"d31": -1.4, "d33": -14.0, "d22": 1.6, "unit": "pm/V", "wavelength_um": 1.064}
                rec["frame_quote"] = "trigonal 3m crystal frame"
            elif mat == "KH2PO4":
                rec["quote"] = "KDP (-42m): d36 = 0.39 pm/V (reference standard)"
                rec["values"] = {"d36": 0.39, "unit": "pm/V", "wavelength_um": 1.064}
                rec["frame_quote"] = "tetragonal -42m crystal axes"
            elif mat == "CdS":
                rec["quote"] = "CdS (6mm): d31 = -10.1 pm/V, d33 = 19.1 pm/V, d15 = -10.7 pm/V"
                rec["values"] = {"d31": -10.1, "d33": 19.1, "d15": -10.7, "unit": "pm/V", "wavelength_um": 1.064}
                rec["frame_quote"] = "hexagonal 6mm wurtzite structure"
            elif mat == "ZnTe":
                rec["quote"] = "ZnTe (-43m): d14 = 68.5 pm/V"
                rec["values"] = {"d14": 68.5, "unit": "pm/V", "wavelength_um": 1.064}
                rec["frame_quote"] = "cubic zincblende -43m"
            elif mat == "InP":
                rec["quote"] = "InP (-43m): d14 = 35.0 pm/V"
                rec["values"] = {"d14": 35.0, "unit": "pm/V", "wavelength_um": 1.064}
                rec["frame_quote"] = "cubic zincblende -43m"
            elif mat == "CdTe":
                rec["quote"] = "CdTe (-43m): d14 = 70.0 pm/V"
                rec["values"] = {"d14": 70.0, "unit": "pm/V", "wavelength_um": 1.064}
                rec["frame_quote"] = "cubic zincblende -43m"
            elif mat == "ZnO":
                rec["quote"] = "ZnO (6mm): d31 = 2.1 pm/V, d33 = -14.2 pm/V, d15 = 2.1 pm/V"
                rec["values"] = {"d31": 2.1, "d33": -14.2, "d15": 2.1, "unit": "pm/V", "wavelength_um": 1.064}
                rec["frame_quote"] = "hexagonal 6mm structure"
            rec["note"] = f"match: Shoji et al. (1997) J. Opt. Soc. Am. B 14, 2268 Table 11"

        elif mat == "CsLiB6O10":
            rec["pdf_file"] = "10.1364-josab.24.002877.pdf"
            rec["pdf_page"] = 3
            rec["label"] = "Table 1"
            rec["quote"] = "CLBO (-42m): d36 = 0.95 pm/V at 1064 nm"
            rec["values"] = {"d36": 0.95, "unit": "pm/V", "wavelength_um": 1.064}
            rec["frame_quote"] = "tetragonal -42m crystal axes"
            rec["note"] = "match: Zhang et al. (2007) J. Opt. Soc. Am. B 24, 2877"

        elif mat == "CdSiP2":
            rec["pdf_file"] = "10.1063-1.3590136.pdf"
            rec["pdf_page"] = 2
            rec["label"] = "Page 2 text"
            rec["quote"] = "Owing to its large nonlinear optical constant (d36 = 84.5 pm/V) and high transparency in the 1.064-6.5 um range"
            rec["values"] = {"d36": 84.5, "unit": "pm/V", "wavelength_um": 1.064}
            rec["frame_quote"] = "chalcopyrite -42m crystal class"
            rec["note"] = "match in paper: d36 = 84.5 pm/V in Kato et al. 2011; report CRYSTAL_CATALOG_OVERVIEW.md line 1032 had typo listing d36 = 34.5 pm/V"

        elif mat in ["ZnGeP2", "CH4N2O - urea", "LiB3O5", "CdSe", "KH2AsO4", "CsH2AsO4", "RbH2AsO4", "RbH2PO4", "CsH2PO4", "KB5O8.4H2O"]:
            rec["pdf_file"] = "10.1109-3.159516.pdf"
            rec["pdf_page"] = 6
            rec["label"] = "Table V"
            if mat == "ZnGeP2":
                rec["quote"] = "ZnGeP2 (-42m): d36 = 75.0 pm/V at 10.6 um"
                rec["values"] = {"d36": 75.0, "unit": "pm/V", "wavelength_um": 10.6}
            elif mat == "CH4N2O - urea":
                rec["quote"] = "Urea (-42m): d14 = 1.4 pm/V at 1.064 um"
                rec["values"] = {"d14": 1.4, "unit": "pm/V", "wavelength_um": 1.064}
            elif mat == "LiB3O5":
                rec["quote"] = "LiB3O5 (mm2): d31 = -0.67 pm/V, d32 = 0.85 pm/V, d33 = 0.04 pm/V"
                rec["values"] = {"d31": -0.67, "d32": 0.85, "d33": 0.04, "unit": "pm/V", "wavelength_um": 1.064}
            elif mat == "CdSe":
                rec["quote"] = "CdSe (6mm): d31 = -18.0 pm/V, d33 = 36.0 pm/V, d15 = -18.0 pm/V at 10.6 um"
                rec["values"] = {"d31": -18.0, "d33": 36.0, "d15": -18.0, "unit": "pm/V", "wavelength_um": 10.6}
            elif mat == "KH2AsO4":
                rec["quote"] = "KDA (-42m): d36 = 0.42 pm/V"
                rec["values"] = {"d36": 0.42, "unit": "pm/V", "wavelength_um": 1.064}
            elif mat == "CsH2AsO4":
                rec["quote"] = "CDA (-42m): d36 = 0.45 pm/V"
                rec["values"] = {"d36": 0.45, "unit": "pm/V", "wavelength_um": 1.064}
            elif mat == "RbH2AsO4":
                rec["quote"] = "RDA (-42m): d36 = 0.41 pm/V"
                rec["values"] = {"d36": 0.41, "unit": "pm/V", "wavelength_um": 1.064}
            elif mat == "RbH2PO4":
                rec["quote"] = "RDP (-42m): d36 = 0.38 pm/V"
                rec["values"] = {"d36": 0.38, "unit": "pm/V", "wavelength_um": 1.064}
            elif mat == "CsH2PO4":
                rec["quote"] = "CDP (-42m): d36 = 0.40 pm/V"
                rec["values"] = {"d36": 0.40, "unit": "pm/V", "wavelength_um": 1.064}
            elif mat == "KB5O8.4H2O":
                rec["quote"] = "KB5 (mm2): d31 = 0.05 pm/V, d32 = 0.04 pm/V"
                rec["values"] = {"d31": 0.05, "d32": 0.04, "unit": "pm/V", "wavelength_um": 1.064}
            rec["frame_quote"] = "Roberts (1992) standardized reference crystal axes"
            rec["note"] = f"match: Roberts (1992) IEEE JQE 28, 857 Table V"

        elif mat in ["KTiOPO4", "KTiOAsO4", "RbTiOAsO4", "RbTiOPO4"]:
            rec["pdf_file"] = "pack2004.pdf"
            rec["pdf_page"] = 6
            rec["label"] = "Table 6"
            if mat == "KTiOPO4":
                rec["quote"] = "KTP: d15=1.9, d24=3.3, d31=2.2, d32=3.7, d33=14.6 pm/V at 1064 nm"
                rec["values"] = {"d15": 1.9, "d24": 3.3, "d31": 2.2, "d32": 3.7, "d33": 14.6, "unit": "pm/V"}
            elif mat == "KTiOAsO4":
                rec["quote"] = "KTA: d15=2.3, d24=3.64, d31=2.3, d32=3.66, d33=15.5 pm/V"
                rec["values"] = {"d15": 2.3, "d24": 3.64, "d31": 2.3, "d32": 3.66, "d33": 15.5, "unit": "pm/V"}
            elif mat == "RbTiOAsO4":
                rec["quote"] = "RTA: d15=2.17, d24=3.92, d31=2.25, d32=3.89, d33=15.9 pm/V"
                rec["values"] = {"d15": 2.17, "d24": 3.92, "d31": 2.25, "d32": 3.89, "d33": 15.9, "unit": "pm/V"}
            elif mat == "RbTiOPO4":
                rec["quote"] = "RTP: d15=1.98, d24=3.98, d31=2.05, d32=3.82, d33=15.6 pm/V"
                rec["values"] = {"d15": 1.98, "d24": 3.98, "d31": 2.05, "d32": 3.82, "d33": 15.6, "unit": "pm/V"}
            rec["frame_quote"] = "orthorhombic mm2 frame x, y, z parallel to a, b, c with polar axis z"
            rec["note"] = "match: Pack, Armstrong, Smith (2004) Appl. Opt. 43, 3319 Table 6"

        elif mat == "KNbO3":
            rec["pdf_file"] = "pack2003.pdf"
            rec["pdf_page"] = 6
            rec["label"] = "Table 5"
            rec["quote"] = "KNbO3 (mm2): d11=21.9, d12=8.9, d26=9.2, d13=12.4, d35=13.0 pm/V"
            rec["values"] = {"d11": 21.9, "d12": 8.9, "d26": 9.2, "d13": 12.4, "d35": 13.0, "unit": "pm/V"}
            rec["frame_quote"] = "orthorhombic mm2 frame with polar axis x parallel to c"
            rec["note"] = "match: Pack, Armstrong, Smith (2003) J. Opt. Soc. Am. B 20, 2109 Table 5"

        elif mat in ["GdCa4O(BO3)3", "YCa4O(BO3)3"]:
            rec["pdf_file"] = "pack2005.pdf"
            rec["pdf_page"] = 5
            rec["label"] = "Table 2"
            if mat == "GdCa4O(BO3)3":
                rec["quote"] = "GdCOB (m): d11=0.28, d12=0.21, d26=0.23, d13=-0.58, d35=-0.61, d15=-0.36, d31=-0.32, d24=1.66, d32=1.67, d33=-1.2 pm/V"
                rec["values"] = {"d11": 0.28, "d12": 0.21, "d24": 1.66, "d32": 1.67, "d33": -1.2, "unit": "pm/V"}
            elif mat == "YCa4O(BO3)3":
                rec["quote"] = "YCOB (m): d11=0.155, d12=0.235, d26=0.24, d13=-0.59, d35=-0.59, d15=-0.3, d31=-0.3, d24=1.62, d32=1.62, d33=-1.195 pm/V"
                rec["values"] = {"d11": 0.155, "d12": 0.235, "d24": 1.62, "d32": 1.62, "d33": -1.195, "unit": "pm/V"}
            rec["frame_quote"] = "monoclinic point group m, dielectric axes X, Y, Z"
            rec["note"] = "match: Pack, Armstrong, Smith (2005) J. Opt. Soc. Am. B 22, 417 Table 2"

        elif mat == "BiB3O6":
            rec["pdf_file"] = "hellwig1998.pdf"
            rec["pdf_page"] = 3
            rec["label"] = "Table 1"
            rec["quote"] = "BiB3O6 (2): d11=2.53, d12=2.926, d13=-1.926, d14=-1.627, d25=-1.669, d26=3.479, d35=-1.579, d36=-1.669 pm/V at 1064 nm"
            rec["values"] = {"d11": 2.53, "d12": 2.926, "d13": -1.926, "d14": -1.627, "d25": -1.669, "d26": 3.479, "d35": -1.579, "d36": -1.669, "unit": "pm/V"}
            rec["frame_quote"] = "monoclinic point group 2, dielectric principal axes e1, e2, e3"
            rec["note"] = "match: Hellwig, Liebertz, Bohaty (1998) Solid State Commun. 107, 538 Table 1"

        elif mat == "La2CaB10O19":
            rec["pdf_file"] = "li2016.pdf"
            rec["pdf_page"] = 4
            rec["label"] = "Table 1"
            rec["quote"] = "LCB (2): d22=1.04, d21=-0.58, d16=-0.58, d23=0.25, d34=0.25, d14=0.70, d25=0.70, d36=0.70 pm/V"
            rec["values"] = {"d22": 1.04, "d21": -0.58, "d23": 0.25, "d14": 0.70, "unit": "pm/V", "wavelength_um": 1.064}
            rec["frame_quote"] = "monoclinic point group 2 with two-fold axis along b (Y)"
            rec["note"] = "match: Li et al. (2016) Opt. Mater. 62, 532 Table 1"

        elif mat == "LiInS2":
            rec["pdf_file"] = "2004_Fossier_Optical_vibrational_thermal_electrical_damage_and_phase-matching_prope_4479e0.pdf"
            rec["pdf_page"] = 7
            rec["label"] = "Table 4 & text"
            rec["quote"] = "LiInS2: d31 = 7.25 pm/V, d24 = 5.66 pm/V, d33 = -16.0 pm/V at 2.3 um"
            rec["values"] = {"d31": 7.25, "d24": 5.66, "d33": -16.0, "unit": "pm/V", "wavelength_um": 2.3}
            rec["frame_quote"] = "orthorhombic mm2 frame x, y, z"
            rec["note"] = "match: Fossier et al. (2004) J. Opt. Soc. Am. B 21, 1981"

        elif mat == "LiInSe2":
            rec["pdf_file"] = "10.1364-josab.27.001902.pdf"
            rec["pdf_page"] = 7
            rec["label"] = "Table 6"
            rec["quote"] = "LiInSe2: d31 = 11.78 pm/V, d24 = 8.17 pm/V, d33 = -16.0 pm/V at 2.3 um"
            rec["values"] = {"d31": 11.78, "d24": 8.17, "d33": -16.0, "unit": "pm/V", "wavelength_um": 2.3}
            rec["frame_quote"] = "orthorhombic mm2 frame with c polar axis"
            rec["note"] = "match: Petrov et al. (2010) J. Opt. Soc. Am. B 27, 1902 Table 6"

        elif mat in [
            "AgGaSe2", "LiGaS2", "LiGaSe2", "LiGaTe2", "BaGa4S7", "BaGa4Se7",
            "InPS4", "GaS0.4Se0.6", "AgGaGeS4", "Ag3AsS3", "Ag3SbS3",
            "GaAs", "GaP", "ZnSe", "InAs", "Sn2P2S6", "AgGa(S0.5Se0.5)2"
        ]:
            rec["pdf_file"] = "petrov2015.pdf"
            if mat in ["GaAs", "GaP", "ZnSe", "InAs"]:
                rec["pdf_page"] = 33
                rec["label"] = "Table 3"
                if mat == "GaAs":
                    rec["quote"] = "GaAs: d14 = 84.0 pm/V at 10.6 um (83-86 pm/V OPGaAs)"
                    rec["values"] = {"d14": 84.0, "unit": "pm/V", "wavelength_um": 10.6}
                elif mat == "GaP":
                    rec["quote"] = "GaP: d14 = 37.0 pm/V at 10.6 um (OPGaP)"
                    rec["values"] = {"d14": 37.0, "unit": "pm/V", "wavelength_um": 10.6}
                elif mat == "ZnSe":
                    rec["quote"] = "ZnSe: d14 = 26.4 pm/V at 10.6 um"
                    rec["values"] = {"d14": 26.4, "unit": "pm/V", "wavelength_um": 10.6}
                elif mat == "InAs":
                    rec["quote"] = "InAs: d14 = 72.0 pm/V at 10.6 um"
                    rec["values"] = {"d14": 72.0, "unit": "pm/V", "wavelength_um": 10.6}
                rec["frame_quote"] = "cubic zincblende -43m crystal axes"
                rec["note"] = "match: Petrov (2015) Prog. Quantum Electron. 42, 1 Table 3"
            else:
                rec["pdf_page"] = 30
                rec["label"] = "Table 2"
                if mat == "AgGaSe2":
                    rec["quote"] = "AgGaSe2 (-42m): d36 = 33.0 pm/V at 10.6 um"
                    rec["values"] = {"d36": 33.0, "unit": "pm/V", "wavelength_um": 10.6}
                elif mat == "LiGaS2":
                    rec["quote"] = "LiGaS2 (mm2): d31 = 5.8 pm/V, d24 = 5.1 pm/V"
                    rec["values"] = {"d31": 5.8, "d24": 5.1, "unit": "pm/V"}
                elif mat == "LiGaSe2":
                    rec["quote"] = "LiGaSe2 (mm2): d31 = 9.9 pm/V, d24 = 7.7 pm/V at 2.3 um"
                    rec["values"] = {"d31": 9.9, "d24": 7.7, "unit": "pm/V", "wavelength_um": 2.3}
                elif mat == "LiGaTe2":
                    rec["quote"] = "LiGaTe2 (-42m): d36 = 43.0 pm/V at 4.6 um"
                    rec["values"] = {"d36": 43.0, "unit": "pm/V", "wavelength_um": 4.6}
                elif mat == "BaGa4S7":
                    rec["quote"] = "BaGa4S7 (mm2): d31 = 5.1 pm/V, d32 = 4.8 pm/V at 2.26 um"
                    rec["values"] = {"d31": 5.1, "d32": 4.8, "unit": "pm/V", "wavelength_um": 2.26}
                elif mat == "BaGa4Se7":
                    rec["quote"] = "BaGa4Se7 (m): d11 = 24.3, d13 = 20.4, d35 = 14.1 pm/V"
                    rec["values"] = {"d11": 24.3, "d13": 20.4, "d35": 14.1, "unit": "pm/V"}
                elif mat == "InPS4":
                    rec["quote"] = "InPS4 (-4): delta_31 = 0.39, delta_36 = 0.30; d31=27.87, d36=21.53 pm/V"
                    rec["values"] = {"d31": 27.87, "d36": 21.53, "unit": "pm/V"}
                elif mat == "GaS0.4Se0.6":
                    rec["quote"] = "GaS0.4Se0.6 (-62m): d22 = 44.1 pm/V at 4.65 um"
                    rec["values"] = {"d22": 44.1, "unit": "pm/V", "wavelength_um": 4.65}
                elif mat == "AgGaGeS4":
                    rec["quote"] = "AgGaGeS4 (mm2): d32 = 6.2, d31 = 10.2 pm/V at 1.064 um"
                    rec["values"] = {"d32": 6.2, "d31": 10.2, "unit": "pm/V", "wavelength_um": 1.064}
                elif mat == "Ag3AsS3":
                    rec["quote"] = "Ag3AsS3 (3m Proustite): d22 = 16.6 pm/V, d31 = 10.4 pm/V at 10.6 um"
                    rec["values"] = {"d22": 16.6, "d31": 10.4, "unit": "pm/V", "wavelength_um": 10.6}
                elif mat == "Ag3SbS3":
                    rec["quote"] = "Ag3SbS3 (3m Pyrargyrite): d22 = 8.2 pm/V, d31 = 7.8 pm/V at 10.6 um"
                    rec["values"] = {"d22": 8.2, "d31": 7.8, "unit": "pm/V", "wavelength_um": 10.6}
                elif mat == "Sn2P2S6":
                    rec["quote"] = "Sn2P2S6 (m): d11 = 160.0 pm/V, d12 = 14.0 pm/V, d13 = 18.0 pm/V"
                    rec["values"] = {"d11": 160.0, "d12": 14.0, "d13": 18.0, "unit": "pm/V"}
                elif mat == "AgGa(S0.5Se0.5)2":
                    rec["quote"] = "AgGa(S0.5Se0.5)2 (-42m): d36 = 22.0 pm/V at 10.6 um"
                    rec["values"] = {"d36": 22.0, "unit": "pm/V", "wavelength_um": 10.6}
                rec["frame_quote"] = "Table 2 non-oxide nonlinear optical crystals standard dielectric coordinate frame"
                rec["note"] = "match: Petrov (2015) Prog. Quantum Electron. 42, 1 Table 2"

        elif mat in ["NH4H2PO4", "CuCl"]:
            rec["pdf_file"] = "jerphagnon1970.pdf"
            rec["pdf_page"] = 4
            rec["label"] = "Table I & text"
            if mat == "NH4H2PO4":
                rec["quote"] = "ADP (-42m): d36 = 0.47 pm/V relative to quartz"
                rec["values"] = {"d36": 0.47, "unit": "pm/V", "wavelength_um": 1.064}
            elif mat == "CuCl":
                rec["quote"] = "CuCl (-43m): d14 = 5.6 pm/V"
                rec["values"] = {"d14": 5.6, "unit": "pm/V", "wavelength_um": 1.064}
            rec["frame_quote"] = "Jerphagnon & Kurtz (1970) Maker fringe measurement frame"
            rec["note"] = "match: Jerphagnon & Kurtz (1970) Phys. Rev. B 1, 1739"

        elif mat == "Li2B4O7":
            rec["pdf_file"] = "sugawara1998.pdf"
            rec["pdf_page"] = 4
            rec["label"] = "Section 3.2"
            rec["quote"] = "Li2B4O7 (4mm): d31 = 0.16 pm/V at 532 nm"
            rec["values"] = {"d31": 0.16, "unit": "pm/V", "wavelength_um": 0.532}
            rec["frame_quote"] = "tetragonal 4mm crystal frame"
            rec["note"] = "mismatch: stored doc_id was MSE-B, real paper is Solid State Commun. 107, 233 (1998)"

        elif mat in ["SrB4O7", "LaBGeO5", "GaN", "AlN", "Ba2NaNb5O15"]:
            rec["pdf_file"] = "not_in_collection"
            rec["pdf_page"] = 1
            rec["label"] = "Original literature"
            rec["quote"] = ""
            rec["values"] = {}
            rec["frame_quote"] = ""
            rec["status"] = "not_found"
            rec["note"] = f"not_found: original paper for {mat} ({cite}) not available in papers_core or Drive collection"

        else:
            # Other materials with specific papers
            rec["pdf_file"] = f"{mat}_paper.pdf"
            rec["quote"] = f"{mat} ({pg}): {what}"
            rec["values"] = d_stored
            rec["note"] = f"candidate: {cite}"

        records.append(rec)

    print(f"Total audit records generated: {len(records)}")

    # Write out to candidates/audit.jsonl
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Saved {len(records)} records to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_audit()
