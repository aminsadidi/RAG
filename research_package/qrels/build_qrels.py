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
ri_questions = df[df["id"].str.startswith("ri-")]

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

# Start with existing MAT_CONFIG
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



NEW_MAT_CONFIG = {
    # Alkali halides
    "CsBr": {
        "cluster": None,
        "name": "CsBr (cesium bromide)",
        "regex": r"\b(cesium\s+bromide|caesium\s+bromide|\bCsBr\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "CsCl": {
        "cluster": None,
        "name": "CsCl (cesium chloride)",
        "regex": r"\b(cesium\s+chloride|caesium\s+chloride|\bCsCl\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "CsF": {
        "cluster": None,
        "name": "CsF (cesium fluoride)",
        "regex": r"\b(cesium\s+fluoride|caesium\s+fluoride|\bCsF\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "CsI": {
        "cluster": None,
        "name": "CsI (cesium iodide)",
        "regex": r"\b(cesium\s+iodide|caesium\s+iodide|\bCsI\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "CsLiB6O10": {
        "cluster": "CLBO_CsLiB6O10",
        "name": "CsLiB6O10 (CLBO)",
        "regex": r"\b(cslib6o10|cesium\s+lithium\s+borate|\bclbo\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+properties)",
    },
    "Cu": {
        "cluster": None,
        "name": "copper (Cu)",
        "regex": r"\b(copper|\bCu\b)\b",
        "exclude": r"(\bcugas2|\bcuo|\bcu2o|\bcual|\bcuga|\bcuzn|copper-gallium)",
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion)",
    },
    "CuGaS2": {
        "cluster": None,
        "name": "CuGaS2",
        "regex": r"\b(cugas2|copper\s+gallium\s+sulfide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|chalcopyrite)",
    },
    "Dy2O3": {
        "cluster": None,
        "name": "Dy2O3 (dysprosium oxide)",
        "regex": r"\b(dy2o3|dysprosium\s+oxide|dysprosium\s+sesquioxide)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|dispersion|rare\s+earth\s+oxides)",
    },
    "Er2O3": {
        "cluster": None,
        "name": "Er2O3 (erbium oxide)",
        "regex": r"\b(er2o3|erbium\s+oxide|erbium\s+sesquioxide)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|dispersion|rare\s+earth\s+oxides)",
    },
    "Ga2O3": {
        "cluster": None,
        "name": "Ga2O3 (gallium oxide)",
        "regex": r"\b(ga2o3|gallium\s+oxide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants)",
    },
    "GaAs": {
        "cluster": "GaAs_OP-GaAs_AlGaAs",
        "name": "GaAs (gallium arsenide)",
        "regex": r"\b(gaas|gallium\s+arsenide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|optical\s+functions|dielectric)",
    },
    "GaN": {
        "cluster": "GaN_AlN",
        "name": "GaN (gallium nitride)",
        "regex": r"\b(gan|gallium\s+nitride)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|dielectric)",
    },
    "GaP": {
        "cluster": "GaP_OP-GaP",
        "name": "GaP (gallium phosphide)",
        "regex": r"\b(gap|gallium\s+phosphide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|optical\s+functions|several\s+crystals|dielectric)",
    },
    "GaS": {
        "cluster": "GaSe_GaS",
        "name": "GaS (gallium sulfide)",
        "regex": r"\b(gas|gallium\s+sulfide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants)",
    },
    "GaSb": {
        "cluster": None,
        "name": "GaSb (gallium antimonide)",
        "regex": r"\b(gasb|gallium\s+antimonide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|optical\s+functions|dielectric)",
    },
    "GaSe": {
        "cluster": "GaSe_GaS",
        "name": "GaSe (gallium selenide)",
        "regex": r"\b(gase|gallium\s+selenide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants)",
    },
    "Gd3Ga5O12": {
        "cluster": None,
        "name": "Gd3Ga5O12 (GGG)",
        "regex": r"\b(gd3ga5o12|gadolinium\s+gallium\s+garnet|\bggg\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants)",
    },
    "Gd3Sc2Al3O12": {
        "cluster": None,
        "name": "Gd3Sc2Al3O12 (GSAG)",
        "regex": r"\b(gd3sc2al3o12|\bgsag\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "Gd3Sc2Ga3O12": {
        "cluster": None,
        "name": "Gd3Sc2Ga3O12 (GSGG)",
        "regex": r"\b(gd3sc2ga3o12|\bgsgg\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "Ge": {
        "cluster": "Si_Ge",
        "name": "germanium (Ge)",
        "regex": r"\b(germanium|\bge\b)\b",
        "exclude": r"(\bgeo2|\bbi4ge3o12|\bbgo|\bzngep2|\bcdgeas2|\bcdgep2|\bbaga2gese6|germanium\s+dioxide)",
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|optical\s+functions|dielectric)",
    },
    "GeO2": {
        "cluster": None,
        "name": "GeO2 (germanium dioxide)",
        "regex": r"\b(geo2|germanium\s+dioxide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "HgGa2S4": {
        "cluster": "AgGaGeS4_HgGa2S4_others",
        "name": "HgGa2S4",
        "regex": r"\b(hgga2s4|mercury\s+gallium\s+sulfide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+properties)",
    },
    "InAs": {
        "cluster": None,
        "name": "InAs (indium arsenide)",
        "regex": r"\b(inas|indium\s+arsenide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|dielectric)",
    },
    "InP": {
        "cluster": None,
        "name": "InP (indium phosphide)",
        "regex": r"\b(inp|indium\s+phosphide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|dielectric)",
    },
    "InSb": {
        "cluster": None,
        "name": "InSb (indium antimonide)",
        "regex": r"\b(insb|indium\s+antimonide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|dielectric)",
    },
    "KBr": {
        "cluster": None,
        "name": "potassium bromide (KBr)",
        "regex": r"\b(potassium\s+bromide|\bKBr\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "KCl": {
        "cluster": None,
        "name": "potassium chloride (KCl)",
        "regex": r"\b(potassium\s+chloride|\bKCl\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "KF": {
        "cluster": None,
        "name": "potassium fluoride (KF)",
        "regex": r"\b(potassium\s+fluoride|\bKF\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "KH2PO4": {
        "cluster": "KDP_DKDP_KH2PO4",
        "name": "KH2PO4 (KDP)",
        "regex": r"\b(kh2po4|potassium\s+dihydrogen\s+phosphate|\bkdp\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "KI": {
        "cluster": None,
        "name": "potassium iodide (KI)",
        "regex": r"\b(potassium\s+iodide|\bKI\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "KNbO3": {
        "cluster": "KNbO3",
        "name": "potassium niobate (KNbO3)",
        "regex": r"\b(knbo3|potassium\s+niobate)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "KTaO3": {
        "cluster": None,
        "name": "potassium tantalate (KTaO3)",
        "regex": r"\b(ktao3|potassium\s+tantalate)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "KTiOPO4": {
        "cluster": "KTP_KTiOPO4",
        "name": "KTiOPO4 (KTP)",
        "regex": r"\b(ktiopo4|potassium\s+titanyl\s+phosphate|\bktp\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "La3Lu2Ga3O12": {
        "cluster": None,
        "name": "La3Lu2Ga3O12 (LLGG)",
        "regex": r"\b(la3lu2ga3o12|\bllgg\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "LaF3": {
        "cluster": None,
        "name": "lanthanum fluoride (LaF3)",
        "regex": r"\b(lanthanum\s+fluoride|\bLaF3\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "LiB3O5": {
        "cluster": "LBO_LiB3O5",
        "name": "LiB3O5 (LBO)",
        "regex": r"\b(lib3o5|lithium\s+triborate|\blbo\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "LiBr": {
        "cluster": None,
        "name": "lithium bromide (LiBr)",
        "regex": r"\b(lithium\s+bromide|\bLiBr\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "LiCl": {
        "cluster": None,
        "name": "lithium chloride (LiCl)",
        "regex": r"\b(lithium\s+chloride|\bLiCl\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "LiF": {
        "cluster": "Fluorides_CaF2_MgF2_BaF2_LiF",
        "name": "lithium fluoride (LiF)",
        "regex": r"\b(lithium\s+fluoride|\bLiF\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "LiI": {
        "cluster": None,
        "name": "lithium iodide (LiI)",
        "regex": r"\b(lithium\s+iodide|\bLiI\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "LiIO3": {
        "cluster": "LiIO3_alpha-HIO3",
        "name": "lithium iodate (LiIO3)",
        "regex": r"\b(liio3|lithium\s+iodate)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "LiNbO3": {
        "cluster": "LiNbO3_LN_PPLN",
        "name": "lithium niobate (LiNbO3)",
        "regex": r"\b(linbo3|lithium\s+niobate|\bln\b|ppln)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "LiTaO3": {
        "cluster": "LiTaO3_LT_PPLT",
        "name": "lithium tantalate (LiTaO3)",
        "regex": r"\b(litao3|lithium\s+tantalate|\blt\b|pplt)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|several\s+crystals)",
    },
    "Lu2O3": {
        "cluster": None,
        "name": "Lu2O3 (lutetium oxide)",
        "regex": r"\b(lu2o3|lutetium\s+oxide|lutetium\s+sesquioxide)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|dispersion|rare\s+earth\s+oxides)",
    },
    "Mg": {
        "cluster": None,
        "name": "magnesium (Mg)",
        "regex": r"\b(magnesium|\bMg\b)\b",
        "exclude": r"(\bmgf2|\bmgo|\bmgal2o4|\bmgh2|magnesium\s+fluoride|magnesium\s+oxide|magnesium\s+aluminate|magnesium\s+hydride)",
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion)",
    },
    "MgAl2O4": {
        "cluster": None,
        "name": "MgAl2O4 (spinel)",
        "regex": r"\b(mgal2o4|magnesium\s+aluminate|spinel)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "MgF2": {
        "cluster": "Fluorides_CaF2_MgF2_BaF2_LiF",
        "name": "magnesium fluoride (MgF2)",
        "regex": r"\b(mgf2|magnesium\s+fluoride)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkaline\s+earth\s+halides)",
    },
    "MgH2": {
        "cluster": None,
        "name": "magnesium hydride (MgH2)",
        "regex": r"\b(mgh2|magnesium\s+hydride)\b",
        "exclude": None,
        "ri_keywords": r"(optical\s+properties|metal\s+hydrides|refractive\s+ind|dispersion)",
    },
    "MgO": {
        "cluster": None,
        "name": "magnesium oxide (MgO)",
        "regex": r"\b(mgo|magnesium\s+oxide|magnesium\s+monoxide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "MoS2": {
        "cluster": None,
        "name": "MoS2 (molybdenum disulfide)",
        "regex": r"\b(mos2|molybdenum\s+disulfide)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|dispersion|optical\s+constants|thickness[-‐\s]*dependent)",
    },
    "MoSe2": {
        "cluster": None,
        "name": "MoSe2 (molybdenum diselenide)",
        "regex": r"\b(mose2|molybdenum\s+diselenide)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|dispersion|optical\s+constants|thickness[-‐\s]*dependent)",
    },
    "NH4H2PO4": {
        "cluster": "ADP_NH4H2PO4",
        "name": "NH4H2PO4 (ADP)",
        "regex": r"\b(nh4h2po4|ammonium\s+dihydrogen\s+phosphate|\badp\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "NaBr": {
        "cluster": None,
        "name": "sodium bromide (NaBr)",
        "regex": r"\b(sodium\s+bromide|\bNaBr\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "NaCl": {
        "cluster": None,
        "name": "sodium chloride (NaCl)",
        "regex": r"\b(sodium\s+chloride|\bNaCl\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "NaF": {
        "cluster": None,
        "name": "sodium fluoride (NaF)",
        "regex": r"\b(sodium\s+fluoride|\bNaF\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "NaI": {
        "cluster": None,
        "name": "sodium iodide (NaI)",
        "regex": r"\b(sodium\s+iodide|\bNaI\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "PbF2": {
        "cluster": None,
        "name": "lead difluoride (PbF2)",
        "regex": r"\b(lead\s+fluoride|lead\s+difluoride|\bpbf2\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "Pd": {
        "cluster": None,
        "name": "palladium (Pd)",
        "regex": r"\b(palladium|\bPd\b)\b",
        "exclude": None,
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion)",
    },
    "RbBr": {
        "cluster": None,
        "name": "rubidium bromide (RbBr)",
        "regex": r"\b(rubidium\s+bromide|\bRbBr\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "RbCl": {
        "cluster": None,
        "name": "rubidium chloride (RbCl)",
        "regex": r"\b(rubidium\s+chloride|\bRbCl\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "RbF": {
        "cluster": None,
        "name": "rubidium fluoride (RbF)",
        "regex": r"\b(rubidium\s+fluoride|\bRbF\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "RbI": {
        "cluster": None,
        "name": "rubidium iodide (RbI)",
        "regex": r"\b(rubidium\s+iodide|\bRbI\b)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkali\s+halides)",
    },
    "RbTiOPO4": {
        "cluster": "RTP_RbTiOPO4",
        "name": "RbTiOPO4 (RTP)",
        "regex": r"\b(rbtiopo4|rubidium\s+titanyl\s+phosphate|\brtp\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "Sc2O3": {
        "cluster": None,
        "name": "Sc2O3 (scandium oxide)",
        "regex": r"\b(sc2o3|scandium\s+oxide|scandium\s+sesquioxide)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|dispersion|rare\s+earth\s+oxides)",
    },
    "Se": {
        "cluster": None,
        "name": "selenium (Se)",
        "regex": r"\b(selenium|\bSe\b)\b",
        "exclude": r"(\bcdse|\bznse|\baggase|\bbaga4se|\bgase|\bmose2|\bwse2|\btl3asse3|cadmium\s+selenide|zinc\s+selenide)",
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion)",
    },
    "Si": {
        "cluster": "Si_Ge",
        "name": "silicon (Si)",
        "regex": r"\b(silicon|\bsi\b)\b",
        "exclude": r"(\bsio2|\bsi3n4|\bsic|\bsin\b|\bcdsip2|\bznsias2|silica|silicon\s+dioxide|silicon\s+nitride|silicon\s+carbide)",
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|dielectric)",
    },
    "Si3N4": {
        "cluster": None,
        "name": "silicon nitride (Si3N4)",
        "regex": r"\b(si3n4|silicon\s+nitride|\bsin\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|mid-infrared)",
    },
    "SiC": {
        "cluster": None,
        "name": "silicon carbide (SiC)",
        "regex": r"\b(sic|silicon\s+carbide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants)",
    },
    "SiO2": {
        "cluster": "Quartz_SiO2",
        "name": "silicon dioxide (SiO2)",
        "regex": r"\b(sio2|silicon\s+dioxide|quartz|fused\s+silica)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants|mid-infrared)",
    },
    "SrF2": {
        "cluster": None,
        "name": "strontium fluoride (SrF2)",
        "regex": r"\b(srf2|strontium\s+fluoride)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|sellmeier|dispersion|alkaline\s+earth\s+halides|infrared\s+properties)",
    },
    "SrMoO4": {
        "cluster": None,
        "name": "strontium molybdate (SrMoO4)",
        "regex": r"\b(srmoo4|strontium\s+molybdate)\b",
        "exclude": None,
        "ri_keywords": r"(several\s+crystals|refracti|sellmeier|dispersion)",
    },
    "SrO": {
        "cluster": None,
        "name": "strontium oxide (SrO)",
        "regex": r"\b(sro|strontium\s+oxide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "SrTiO3": {
        "cluster": None,
        "name": "strontium titanate (SrTiO3)",
        "regex": r"\b(srtio3|strontium\s+titanate|\bsto\b)\b",
        "exclude": None,
        "ri_keywords": r"(several\s+crystals|refracti|sellmeier|dispersion)",
    },
    "Ta2O5": {
        "cluster": None,
        "name": "tantalum pentoxide (Ta2O5)",
        "regex": r"\b(ta2o5|tantalum\s+oxide|tantalum\s+pentoxide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "Te": {
        "cluster": None,
        "name": "tellurium (Te)",
        "regex": r"\b(tellurium|\bTe\b)\b",
        "exclude": r"(\bcdte|\bznte|\bteo2|\bligate2|cadmium\s+telluride|zinc\s+telluride)",
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion)",
    },
    "TeO2": {
        "cluster": "Calcite_TeO2_TiO2_birefringent",
        "name": "tellurium dioxide (TeO2)",
        "regex": r"\b(teo2|tellurium\s+dioxide|paratellurite)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "Ti": {
        "cluster": None,
        "name": "titanium (Ti)",
        "regex": r"\b(titanium|\bTi\b)\b",
        "exclude": r"(\btio2|\btih2|\bsrtio3|\bbatio3|\bktiopo4|\brbtiopo4|titanium\s+dioxide|titanate)",
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion)",
    },
    "TiH2": {
        "cluster": None,
        "name": "titanium hydride (TiH2)",
        "regex": r"\b(tih2|titanium\s+hydride)\b",
        "exclude": None,
        "ri_keywords": r"(optical\s+properties|metal\s+hydrides|refractive\s+ind|dispersion)",
    },
    "TiO2": {
        "cluster": "Calcite_TeO2_TiO2_birefringent",
        "name": "titanium dioxide (TiO2)",
        "regex": r"\b(tio2|titanium\s+dioxide|rutile)\b",
        "exclude": None,
        "ri_keywords": r"(several\s+crystals|refracti|sellmeier|dispersion|mid-infrared)",
    },
    "V": {
        "cluster": None,
        "name": "vanadium (V)",
        "regex": r"\b(vanadium|\bV\b)\b",
        "exclude": r"(\byvo4|\bgdvo4|vanadate)",
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion)",
    },
    "WS2": {
        "cluster": None,
        "name": "WS2 (tungsten disulfide)",
        "regex": r"\b(ws2|tungsten\s+disulfide)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|dispersion|optical\s+constants|thickness[-‐\s]*dependent)",
    },
    "WSe2": {
        "cluster": None,
        "name": "WSe2 (tungsten diselenide)",
        "regex": r"\b(wse2|tungsten\s+diselenide)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|dispersion|optical\s+constants|thickness[-‐\s]*dependent)",
    },
    "Y2O3": {
        "cluster": None,
        "name": "Y2O3 (yttrium oxide)",
        "regex": r"\b(y2o3|yttrium\s+oxide|yttrium\s+sesquioxide)\b",
        "exclude": r"(\by3al5o12|\byag|\byvo4|\byalo3|\bylif4)",
        "ri_keywords": r"(refractive\s+ind|dispersion|rare\s+earth\s+oxides)",
    },
    "Y3Al5O12": {
        "cluster": "YAG_YVO4_GdVO4_hosts",
        "name": "Y3Al5O12 (YAG)",
        "regex": r"\b(y3al5o12|yttrium\s+aluminium\s+garnet|yttrium\s+aluminum\s+garnet|\byag\b)\b",
        "exclude": None,
        "ri_keywords": r"(several\s+crystals|refracti|sellmeier|dispersion)",
    },
    "Y3Ga5O12": {
        "cluster": None,
        "name": "Y3Ga5O12 (YGG)",
        "regex": r"\b(y3ga5o12|yttrium\s+gallium\s+garnet|\bygg\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "YAlO3": {
        "cluster": None,
        "name": "YAlO3 (YAP)",
        "regex": r"\b(yalo3|yttrium\s+aluminate|\byap\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "YLiF4": {
        "cluster": None,
        "name": "YLiF4 (YLF)",
        "regex": r"\b(ylif4|yttrium\s+lithium\s+fluoride|\bylf\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "YVO4": {
        "cluster": "YAG_YVO4_GdVO4_hosts",
        "name": "YVO4 (yttrium orthovanadate)",
        "regex": r"\b(yvo4|yttrium\s+orthovanadate|yttrium\s+vanadate)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "Yb2O3": {
        "cluster": None,
        "name": "Yb2O3 (ytterbium oxide)",
        "regex": r"\b(yb2o3|ytterbium\s+oxide|ytterbium\s+sesquioxide)\b",
        "exclude": None,
        "ri_keywords": r"(refractive\s+ind|dispersion|rare\s+earth\s+oxides)",
    },
    "ZnGeP2": {
        "cluster": "ZGP_ZnGeP2",
        "name": "ZnGeP2 (ZGP)",
        "regex": r"\b(zngep2|zinc\s+germanium\s+phosphide|\bzgp\b)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "ZnO": {
        "cluster": None,
        "name": "ZnO (zinc oxide)",
        "regex": r"\b(zno|zinc\s+oxide|zinc\s+monoxide)\b",
        "exclude": None,
        "ri_keywords": r"(several\s+crystals|refracti|sellmeier|dispersion)",
    },
    "ZnS": {
        "cluster": "CdSe_CdS_ZnS",
        "name": "ZnS (zinc sulfide)",
        "regex": r"\b(zns|zinc\s+sulfide)\b",
        "exclude": None,
        "ri_keywords": r"(several\s+crystals|refracti|sellmeier|dispersion)",
    },
    "ZnSe": {
        "cluster": "ZnSe_ZnTe",
        "name": "ZnSe (zinc selenide)",
        "regex": r"\b(znse|zinc\s+selenide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "ZnSiAs2": {
        "cluster": None,
        "name": "ZnSiAs2",
        "regex": r"\b(znsias2|zinc\s+silicon\s+arsenide)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "ZnTe": {
        "cluster": "ZnSe_ZnTe",
        "name": "ZnTe (zinc telluride)",
        "regex": r"\b(znte|zinc\s+telluride)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "ZnWO4": {
        "cluster": None,
        "name": "ZnWO4 (zinc tungstate)",
        "regex": r"\b(znwo4|zinc\s+tungstate)\b",
        "exclude": None,
        "ri_keywords": r"(several\s+crystals|refracti|sellmeier|dispersion)",
    },
    "Zr": {
        "cluster": None,
        "name": "zirconium (Zr)",
        "regex": r"\b(zirconium|\bZr\b)\b",
        "exclude": r"(\bzro2|zirconium\s+dioxide|zirconia)",
        "ri_keywords": r"(optical\s+constants|refractive\s+ind|dispersion)",
    },
    "ZrO2": {
        "cluster": None,
        "name": "ZrO2 (zirconium dioxide)",
        "regex": r"\b(zro2|zirconium\s+dioxide|zirconia)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
    "CdTe": {
        "cluster": None,
        "name": "CdTe (cadmium telluride)",
        "regex": r"\b(cdte|cadmium\s+telluride)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion|optical\s+constants)",
    },
    "CeF3": {
        "cluster": None,
        "name": "CeF3 (cerium fluoride)",
        "regex": r"\b(cef3|cerium\s+fluoride|cerium\s+trifluoride)\b",
        "exclude": None,
        "ri_keywords": r"(refracti|sellmeier|dispersion)",
    },
}

MAT_CONFIG.update(NEW_MAT_CONFIG)

def make_title_reason(p, mat, q_row):
    cfg = MAT_CONFIG[mat]
    t = clean_title(p.get("reference") or "")
    doc_id = p.get("doc_id")
    
    # Landmark multi-crystal survey papers
    if "10.1364_josa.65.000742" in doc_id:
        if mat in ["Ag", "Al", "Au", "Bi", "C", "Al2O3", "Cu", "Mg"]:
            return 2, f"Title gives optical constants for {mat} from far infrared to x-ray."
        return 0, f"Title covers optical constants of other elements, not {cfg['name']}."

    if "10.1063_1.1703106" in doc_id:
        if mat in ["AlPO4", "CaMoO4", "CaWO4", "CdSe", "GaP", "LiTaO3", "SrMoO4", "SrTiO3", "TiO2", "Y3Al5O12", "ZnO", "ZnS", "ZnWO4"]:
            return 2, f"Title measures refractive indices of several crystals including {mat}."
        return 0, f"Title measures several crystals, not applicable to {cfg['name']}."

    if "10.1063_1.555616" in doc_id:
        if mat in ["BaF2", "CaF2", "MgF2", "SrF2"]:
            return 2, f"Title gives refractive index of alkaline earth halides ({mat})."
        return 0, f"Title covers alkaline earth halides, not {cfg['name']}."

    if "10.1063_1.555536" in doc_id:
        alkali_halides = ["CsBr", "CsCl", "CsF", "CsI", "KBr", "KCl", "KF", "KI", "LiBr", "LiCl", "LiF", "LiI", "NaBr", "NaCl", "NaF", "NaI", "RbBr", "RbCl", "RbF", "RbI"]
        if mat in alkali_halides:
            return 2, f"Title gives refractive index of alkali halides ({mat})."
        return 0, f"Title covers alkali halides, not {cfg['name']}."

    if "10.1103_physrevb.27.985" in doc_id:
        if mat in ["Si", "Ge", "GaP", "GaAs", "GaSb", "InP", "InAs", "InSb"]:
            return 2, f"Title measures dielectric functions and optical parameters of {mat}."
        return 0, f"Title measures semiconductor optical parameters, not {cfg['name']}."

    if "10.1063_1.343580" in doc_id:
        if mat in ["GaP", "GaAs", "GaSb", "InP", "InAs", "InSb", "AlAs"]:
            return 2, f"Title reports optical dispersion relations for III-V semiconductor {mat}."
        return 0, f"Title reports dispersion for other III-V semiconductors, not {cfg['name']}."

    if "10.1088_1464_4258_3_3_303" in doc_id:
        if mat in ["Dy2O3", "Er2O3", "Lu2O3", "Sc2O3", "Y2O3", "Yb2O3"]:
            return 2, f"Title gives refractive index and dispersion of rare earth oxide {mat}."
        return 0, f"Title covers other rare earth oxides, not {cfg['name']}."

    if "10.1002_adom.201900239" in doc_id:
        if mat in ["MoS2", "MoSe2", "WS2", "WSe2"]:
            return 2, f"Title measures thickness-dependent refractive index of {mat}."
        return 0, f"Title measures other 2D transition metal dichalcogenides, not {cfg['name']}."

    if "10.1021_acsphotonics.8b01243" in doc_id:
        if mat in ["MgH2", "TiH2"]:
            return 2, f"Title reports optical properties of metal hydride {mat}."
        return 0, f"Title covers other metal hydrides, not {cfg['name']}."

    if "10.1063_1.1713411" in doc_id:
        if mat in ["ZnSe", "ZnTe", "CdTe"]:
            return 2, f"Title reports refractive index and dispersion for {mat}."
        return 0, f"Title reports refractive index for other II-VI semiconductors, not {cfg['name']}."

    if "10.1016_0925_3467_92_90022_f" in doc_id:
        if mat in ["GaAs", "GaP", "Ge"]:
            return 2, f"Title determines optical functions and dispersion for {mat}."
        return 0, f"Title determines optical functions of other semiconductors, not {cfg['name']}."

    if "10.1103_physrev.157.709" in doc_id:
        if mat in ["CaF2", "SrF2", "BaF2", "CdF2"]:
            return 2, f"Title reports far-infrared optical properties and dispersion of {mat}."
        return 0, f"Title covers other fluorides, not {cfg['name']}."

    if "10.1103_physrev.127.1950" in doc_id:
        if mat in ["CaF2", "SrF2", "BaF2"]:
            return 2, f"Title reports infrared properties and dispersion of {mat}."
        return 0, f"Title covers other fluorides, not {cfg['name']}."

    if "10.1364_ao.51.006789" in doc_id:
        if mat in ["Al2O3", "TiO2", "SiO2", "AlN", "Si3N4"]:
            return 2, f"Title reports mid-infrared optical properties and dispersion of {mat}."
        return 0, f"Title covers other thin films, not {cfg['name']}."

    if "10.1103_physrevb.39.3337" in doc_id:
        return 0, f"Title discusses nonlinear index of crystals, without {mat} dispersion formula."

    if "10.1063_1.89561" in doc_id:
        return 0, f"Title discusses nonlinear index of fluoride crystals, without {mat} dispersion."

    if "10.1364_oe.579736" in doc_id:
        return 0, f"Title discusses nonlinear refractive index measurements, not {mat} dispersion."

    # Boyd 1972 ternary papers
    if "10.1109_jqe.1972.1076900" in doc_id and mat == "AgGaSe2":
        return 2, "Title reports linear optical properties and refractive indices of AgGaSe2."
    if "10.1109_jqe.1972.1076982" in doc_id and mat in ["CdGeAs2", "CdGeP2"]:
        return 2, f"Title reports linear optical properties of chalcopyrite semiconductor {mat}."

    # Check if title discusses target material
    has_target = bool(re.search(cfg["regex"], t, re.I))
    if cfg.get("exclude") and re.search(cfg["exclude"], t, re.I):
        has_target = False

    if not has_target:
        subj = extract_main_subject(t)
        if subj:
            return 0, f"Title discusses {subj}, not {cfg['name']}."
        return 0, f"Title discusses other material, not {cfg['name']}."

    # Check for requested quantity (refractive index / Sellmeier / dispersion formula)
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

    # Same material, related data
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
    print(f"Processing all {len(ri_questions)} ri- questions...")
    for idx, q_row in ri_questions.iterrows():
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
    df_out = pd.DataFrame(records)
    print("\n--- Summary Statistics ---")
    print(f"Total rows: {len(df_out)}")
    print(f"Questions covered: {df_out['id'].nunique()}")
    print(f"Unique papers: {df_out['doc_id'].nunique()}")
    print("Grade distribution:")
    print(df_out['grade'].value_counts(normalize=True).mul(100).round(1).astype(str) + "% (" + df_out['grade'].value_counts().astype(str) + ")")
    max_words = df_out['reason'].apply(lambda s: len(s.split())).max()
    min_words = df_out['reason'].apply(lambda s: len(s.split())).min()
    print(f"Reason word counts: min={min_words}, max={max_words}")
