#!/usr/bin/env python3
"""
Generate qrels.csv for the first 100 ri- questions in data/rag-optics/gold/questions.csv
using paper titles and metadata from web/src/papers.json.

Grading rubric:
  2 = gives the requested quantity (formula/value) for that exact material
  1 = same material, related data
  0 = not relevant

Output:
  research_package/qrels/qrels.csv
  Columns: id, doc_id, grade, reason (reason <= 15 words, from the title)
"""

import os
import re
import csv
import json
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PAPERS_JSON = os.path.join(REPO_ROOT, "web/src/papers.json")
QUESTIONS_CSV = os.path.join(REPO_ROOT, "data/rag-optics/gold/questions.csv")
OUT_CSV = os.path.join(REPO_ROOT, "research_package/qrels/qrels.csv")

with open(PAPERS_JSON, "r", encoding="utf-8") as f:
    papers = json.load(f)
p_by_id = {p["doc_id"]: p for p in papers}

df = pd.read_csv(QUESTIONS_CSV)
ri_100 = df[df["id"].str.startswith("ri-")].iloc[:100]

def clean_title(ref):
    if not ref:
        return ""
    text = re.sub(r"\.\s*(?:doi:\S+|arXiv:\S+)\s*$", "", ref)
    m = re.match(r"^.*?\(\d{4}\)\.\s+(.*)$", text)
    if m:
        text = m.group(1)
    parts = text.split(". ")
    return ". ".join(parts[:-1]) if len(parts) > 1 else text

def extract_main_subject(title):
    m = re.findall(r"\b[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*){2,}\b", title)
    if m:
        return m[0]
    parts = re.split(r"[:–—]", title)
    first = parts[0].strip()
    first = re.sub(r"\(.*?\)", "", first).strip()
    first = re.sub(r"\s+", " ", first).strip()
    first = first.rstrip(" ,;=")
    words = first.split()
    if len(words) <= 3:
        return first
    return " ".join(words[:2])

MAT_CONFIG = {
    "Ag": {
        "cluster": None,
        "name": "silver (Ag)",
        "regex": r"\b(silver|\bAg\b)\b",
        "exclude": r"(\baggas|\baggase|\bag\s*3|\bag3|\bagcl|\baginga|\bagin|silver-gallium|silver\s+thiogallate)",
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion|permittivity)",
    },
    "AgCl": {
        "cluster": None,
        "name": "silver chloride (AgCl)",
        "regex": r"\b(silver\s+chloride|\bagcl\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion)",
    },
    "AgGaS2": {
        "cluster": "AgGaS2",
        "name": "AgGaS2",
        "regex": r"\b(aggas2|silver\s+gallium\s+sulfide|\bags\b|silver\s+thiogallate)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|optical\s+properties|linear\s+optical)",
    },
    "AgGaSe2": {
        "cluster": "AgGaSe2",
        "name": "AgGaSe2",
        "regex": r"\b(aggase2|silver\s+gallium\s+selenide|\bagse\b|ternary\s+selenides)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|optical\s+properties|linear\s+and\s+nonlinear|ternary\s+selenides)",
    },
    "Al": {
        "cluster": None,
        "name": "aluminium (Al)",
        "regex": r"\b(aluminium|aluminum|\bAl\b)\b",
        "exclude": r"(\bal2o3|\balas|\baln|\balpo4|\balgaas|\balinas|\balgan|\byal|aluminum\s+oxide|aluminium\s+oxide|aluminum\s+nitride|aluminium\s+nitride)",
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion)",
    },
    "Al2O3": {
        "cluster": "Sapphire_Al2O3",
        "name": "Al2O3 (sapphire)",
        "regex": r"\b(al2o3|aluminum\s+oxide|aluminium\s+oxide|sapphire|alumina|corundum)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|optical\s+properties)",
    },
    "AlAs": {
        "cluster": None,
        "name": "AlAs",
        "regex": r"\b(alas|aluminum\s+arsenide|aluminium\s+arsenide|alxga1-xas|algaas)\b",
        "exclude": None,
        "ri_keywords": r"(dielectric\s+function|refractive\s+ind|dispersion|optical\s+constants)",
    },
    "AlN": {
        "cluster": "GaN_AlN",
        "name": "AlN",
        "regex": r"\b(aln|aluminum\s+nitride|aluminium\s+nitride)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|optical\s+properties)",
    },
    "AlPO4": {
        "cluster": None,
        "name": "AlPO4",
        "regex": r"\b(alpo4|aluminum\s+phosphate|aluminium\s+phosphate|berlinite)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|several\s+crystals|dispersion)",
    },
    "Au": {
        "cluster": None,
        "name": "gold (Au)",
        "regex": r"\b(gold|\bau\b)\b",
        "exclude": None,
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion)",
    },
    "BN": {
        "cluster": None,
        "name": "BN",
        "regex": r"\b(boron\s+nitride|\bbn\b|h-bn|hbn)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+index\s+dispersion|refractive\s+ind|dispersion)",
    },
    "BaB2O4": {
        "cluster": "BBO_beta-BaB2O4",
        "name": "BaB2O4 (BBO)",
        "regex": r"\b(bab2o4|barium[-\s]+borate|\bbbo\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|optical,\s+mechanical,\s+and\s+thermal\s+properties)",
    },
    "BaF2": {
        "cluster": "Fluorides_CaF2_MgF2_BaF2_LiF",
        "name": "BaF2",
        "regex": r"\b(baf2|ba\s*f\s*2|barium\s+fluoride)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+properties|refractive\s+index|dispersion|infrared\s+properties|far-infrared\s+optical\s+properties)",
    },
    "BaGa2GeSe6": {
        "cluster": None,
        "name": "BaGa2GeSe6 (BGGSe)",
        "regex": r"\b(baga2gese6|\bbggse\b)\b",
        "exclude": None,
        "ri_keywords": r"(phase[-‐\s]*matching\s+properties|refractive\s+ind|sellmeier|dispersion)",
    },
    "BaGa4S7": {
        "cluster": "BaGa4Se7_BaGa4S7",
        "name": "BaGa4S7 (BGS)",
        "regex": r"\b(baga4s7|barium\s+gallium\s+sulfide|\bbgs\b)\b",
        "exclude": None,
        "ri_keywords": r"(phase[-‐\s]*matching\s+properties|refractive\s+ind|sellmeier|dispersion)",
    },
    "BaGa4Se7": {
        "cluster": "BaGa4Se7_BaGa4S7",
        "name": "BaGa4Se7 (BGSe)",
        "regex": r"\b(baga4se7|barium\s+gallium\s+selenide|\bbgse\b)\b",
        "exclude": None,
        "ri_keywords": r"(phase[-‐\s]*matching\s+properties|refractive\s+ind|sellmeier|dispersion)",
    },
    "BaTiO3": {
        "cluster": "SBN_BaTiO3_ferroelectrics",
        "name": "BaTiO3",
        "regex": r"\b(batio3|barium\s+titanate)\b",
        "exclude": None,
        "ri_keywords": r"(dielectric\s+and\s+optical\s+properties|dispersion|refractive\s+ind)",
    },
    "BeAl2O4": {
        "cluster": None,
        "name": "BeAl2O4",
        "regex": r"\b(beal2o4|beryllium\s+aluminate|chrysoberyl|alexandrite)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion)",
    },
    "Bi": {
        "cluster": None,
        "name": "bismuth (Bi)",
        "regex": r"\b(bismuth|\bbi\b)\b",
        "exclude": r"(\bbib3o6|\bbibo|\bbi4ge3o12|\bbgo|\bbi12|bismuth\s+triborate|bismuth\s+germanate)",
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion)",
    },
    "Bi4Ge3O12": {
        "cluster": None,
        "name": "Bi4Ge3O12 (BGO)",
        "regex": r"\b(bi4ge3o12|bismuth\s+germanate|\bbgo\b)\b",
        "exclude": None,
        "ri_keywords": r"(optical,\s+thermo-optic|refractive\s+ind|sellmeier|dispersion)",
    },
    "BiB3O6": {
        "cluster": "BiBO_BiB3O6",
        "name": "BiB3O6 (BiBO)",
        "regex": r"\b(bib3o6|bismuth\s+triborate|bismuth\s+borate|\bbibo\b)\b",
        "exclude": None,
        "ri_keywords": r"(optical\s+properties|linear\s+optical|refractive\s+ind|sellmeier|dispersion|nonlinear\s+refractive\s+index)",
    },
    "C": {
        "cluster": None,
        "name": "carbon (C)",
        "regex": r"\b(carbon|diamond|graphene|\bC\b)\b",
        "exclude": r"(carbon\s+dots|carbon\s+quantum|carbon\s+nanotube|polymer|photovoltaic)",
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion)",
    },
    "CaCO3": {
        "cluster": "Calcite_TeO2_TiO2_birefringent",
        "name": "CaCO3 (calcite)",
        "regex": r"\b(caco3|calcium\s+carbonate|calcite)\b",
        "exclude": None,
        "ri_keywords": r"(dispersion-equation|refractive\s+ind|birefringence)",
    },
    "CaF2": {
        "cluster": "Fluorides_CaF2_MgF2_BaF2_LiF",
        "name": "CaF2 (calcium fluoride)",
        "regex": r"\b(caf2|ca\s*f\s*2|calcium\s+fluoride|fluorite)\b",
        "exclude": None,
        "ri_keywords": r"(optical\s+properties\s+of\s+calcium\s+fluoride|refractive\s+ind|dispersion|infrared\s+properties|far-infrared\s+optical\s+properties)",
    },
    "CaGdAlO4": {
        "cluster": None,
        "name": "CaGdAlO4 (CALGO)",
        "regex": r"\b(cagda\w*|calgo|calcium\s+gadolinium\s+aluminate|calnalo4)\b",
        "exclude": None,
        "ri_keywords": r"(sellmeier\s+equations|dispersion|refractive\s+ind)",
    },
    "CaMoO4": {
        "cluster": None,
        "name": "CaMoO4",
        "regex": r"\b(camoo4|calcium\s+molybdate)\b",
        "exclude": None,
        "ri_keywords": r"(several\s+crystals|refractive\s+ind|dispersion)",
    },
    "CaO": {
        "cluster": None,
        "name": "CaO",
        "regex": r"\b(cao|calcium\s+oxide)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|dispersion)",
    },
    "CaWO4": {
        "cluster": None,
        "name": "CaWO4",
        "regex": r"\b(cawo4|calcium\s+tungstate|scheelite)\b",
        "exclude": None,
        "ri_keywords": r"(several\s+crystals|refractive\s+ind|dispersion)",
    },
    "CaYAlO4": {
        "cluster": None,
        "name": "CaYAlO4 (CALYO)",
        "regex": r"\b(caya\w*|calyo|calcium\s+yttrium\s+aluminate|calnalo4)\b",
        "exclude": None,
        "ri_keywords": r"(sellmeier\s+equations|dispersion|refractive\s+ind)",
    },
    "CdF2": {
        "cluster": None,
        "name": "CdF2",
        "regex": r"\b(cdf2|cd\s*f\s*2|cadmium\s+fluoride)\b",
        "exclude": None,
        "ri_keywords": r"(far-infrared\s+optical\s+properties|refractive\s+ind|dispersion)",
    },
    "CdGeAs2": {
        "cluster": None,
        "name": "CdGeAs2",
        "regex": r"\b(cdgeas2|cadmium\s+germanium\s+arsenide|chalcopyrite)\b",
        "exclude": None,
        "ri_keywords": r"(linear\s+and\s+nonlinear\s+optical\s+properties|refractive\s+ind|dispersion)",
    },
    "CdGeP2": {
        "cluster": None,
        "name": "CdGeP2",
        "regex": r"\b(cdgep2|cadmium\s+germanium\s+phosphide|chalcopyrite)\b",
        "exclude": None,
        "ri_keywords": r"(linear\s+and\s+nonlinear\s+optical\s+properties|refractive\s+ind|dispersion)",
    },
    "CdS": {
        "cluster": "CdSe_CdS_ZnS",
        "name": "CdS",
        "regex": r"\b(cds|cadmium\s+sulfide|cd\s*s\s*x\s*se\s*1)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+indexes|optical\s+properties\s+of\s+wurtzite|dispersion)",
    },
    "CdSe": {
        "cluster": "CdSe_CdS_ZnS",
        "name": "CdSe",
        "regex": r"\b(cdse|cadmium\s+selenide|cd\s*s\s*x\s*se\s*1)\b",
        "exclude": None,
        "ri_keywords": r"(dispersion\s+of\s+the\s+refractive\s+indices|several\s+crystals|optical\s+properties\s+of\s+cubic\s+and\s+hexagonal)",
    },
}

def make_title_reason(p, mat, q_row):
    cfg = MAT_CONFIG[mat]
    t = clean_title(p.get("reference") or "")
    doc_id = p.get("doc_id")
    
    # 1. Landmark multi-crystal survey papers
    if "10.1364_josa.65.000742" in doc_id:
        if mat in ["Ag", "Al", "Au", "Bi", "C", "Al2O3"]:
            return 2, f"Title gives optical constants for {mat} from far infrared to x-ray."
        return 0, f"Title covers optical constants of other elements, not {cfg['name']}."

    if "10.1063_1.1703106" in doc_id:
        if mat in ["AlPO4", "CaMoO4", "CaWO4", "CdSe"]:
            return 2, f"Title measures refractive indices of several crystals including {mat}."
        return 0, f"Title measures several crystals, not applicable to {cfg['name']}."

    if "10.1063_1.555616" in doc_id:
        if mat in ["BaF2", "CaF2"]:
            return 2, f"Title gives refractive index of alkaline earth halides ({mat})."
        return 0, f"Title covers alkaline earth halides, not {cfg['name']}."

    if "10.1103_physrevb.39.3337" in doc_id:
        return 0, f"Title discusses nonlinear index of crystals, without {mat} dispersion formula."

    # Special Boyd 1972 ternary papers
    if "10.1109_jqe.1972.1076900" in doc_id and mat == "AgGaSe2":
        return 2, "Title reports linear optical properties and refractive indices of AgGaSe2."
    if "10.1109_jqe.1972.1076982" in doc_id and mat in ["CdGeAs2", "CdGeP2"]:
        return 2, f"Title reports linear optical properties of chalcopyrite semiconductor {mat}."

    # 2. Check if title discusses target material
    has_target = bool(re.search(cfg["regex"], t, re.I))
    if cfg.get("exclude") and re.search(cfg["exclude"], t, re.I):
        has_target = False

    if not has_target:
        subj = extract_main_subject(t)
        if subj:
            return 0, f"Title discusses {subj}, not {cfg['name']}."
        return 0, f"Title discusses other material, not {cfg['name']}."

    # 3. Check for requested quantity (refractive index / Sellmeier / dispersion formula)
    is_ri = bool(re.search(cfg["ri_keywords"], t, re.I))
    if is_ri:
        if re.search(r"sellmeier", t, re.I):
            return 2, f"Title provides Sellmeier equations for {cfg['name']}."
        elif re.search(r"dispersion\s+formula", t, re.I):
            return 2, f"Title reports dispersion formula for {cfg['name']}."
        elif re.search(r"optical\s+constants", t, re.I):
            return 2, f"Title reports optical constants and dispersion of {cfg['name']}."
        elif re.search(r"refractive\s+prop", t, re.I):
            return 2, f"Title reports refractive properties of {cfg['name']}."
        elif re.search(r"phase[-‐\s]*matching\s+properties", t, re.I):
            return 2, f"Title reports phase-matching and dispersion properties of {cfg['name']}."
        else:
            return 2, f"Title reports refractive index and dispersion data for {cfg['name']}."

    # 4. Same material, related data
    if re.search(r"(second[-\s]harmonic|shg)", t, re.I):
        return 1, f"Title studies second-harmonic generation in {cfg['name']}."
    elif re.search(r"(parametric|opo|opa)", t, re.I):
        return 1, f"Title investigates optical parametric processes in {cfg['name']}."
    elif re.search(r"(crystal\s+growth|growth\s+and)", t, re.I):
        return 1, f"Title investigates crystal growth and properties of {cfg['name']}."
    elif re.search(r"(thermal|damage|lensing)", t, re.I):
        return 1, f"Title studies thermal or damage properties of {cfg['name']}."
    elif re.search(r"(raman|phonon|lattice)", t, re.I):
        return 1, f"Title studies vibrational/phonon properties of {cfg['name']}."
    elif re.search(r"(absorption|transmission|transparency)", t, re.I):
        return 1, f"Title investigates optical absorption and transmission of {cfg['name']}."
    elif re.search(r"(nonlinear|electro-optic)", t, re.I):
        return 1, f"Title studies nonlinear optical properties of {cfg['name']}."
    else:
        return 1, f"Title discusses related optical/physical data for {cfg['name']}."

def build_qrels():
    records = []
    for idx, q_row in ri_100.iterrows():
        qid = q_row["id"]
        mat = qid.split("-")[1]
        cfg = MAT_CONFIG[mat]

        cands = set()
        for d in str(q_row["doc_id"]).split(";"):
            if d.strip():
                cands.add(d.strip())
        for p in papers:
            if cfg["cluster"] and p.get("material") == cfg["cluster"]:
                cands.add(p["doc_id"])
            ref = p.get("reference") or ""
            if re.search(cfg["regex"], ref, re.I):
                if not cfg["exclude"] or not re.search(cfg["exclude"], ref, re.I):
                    cands.add(p["doc_id"])

        for doc_id in sorted(list(cands)):
            p = p_by_id.get(doc_id)
            if not p:
                continue
            grade, reason = make_title_reason(p, mat, q_row)
            words = reason.split()
            if len(words) > 15:
                reason = " ".join(words[:15])
            records.append({
                "id": qid,
                "doc_id": doc_id,
                "grade": grade,
                "reason": reason
            })

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "doc_id", "grade", "reason"])
        writer.writeheader()
        writer.writerows(records)

    print(f"Successfully generated {len(records)} rows to {OUT_CSV}")
    return records

if __name__ == "__main__":
    records = build_qrels()
