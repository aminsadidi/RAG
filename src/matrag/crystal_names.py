"""The names optical crystals go by, in one table for the whole project: the search (query expansion and the
relevance check, here and in web/src/text.js), the site's refractive-index tab and the calculators' crystal pickers
all read it, so a crystal found under one name is found under all of them.

Keys are the formulas the site's data use (web/public/ri); the first name of each list is the usual abbreviation.
Abbreviations of two letters (LN, LT, KN) are matched in capitals only; the others also in lower case.
"""

CRYSTAL_NAMES: dict[str, list[str]] = {
    # borates
    "BaB2O4": ["BBO", "β-BBO", "beta-BBO", "β-BaB2O4", "beta-BaB2O4", "beta barium borate", "barium borate",
               "barium metaborate"],
    "alpha-BaB2O4": ["α-BBO", "alpha-BBO", "a-BBO", "α-BaB2O4", "alpha-BaB2O4", "alpha barium borate"],
    "LiB3O5": ["LBO", "lithium triborate", "lithium borate"],
    "BiB3O6": ["BiBO", "BIBO", "bismuth triborate", "bismuth borate"],
    "CsLiB6O10": ["CLBO", "cesium lithium borate", "caesium lithium borate"],
    "CsB3O5": ["CBO", "cesium triborate", "caesium triborate"],
    "KBe2BO3F2": ["KBBF", "potassium fluoroboratoberyllate", "potassium beryllium fluoroborate"],
    "RbBe2BO3F2": ["RBBF", "rubidium beryllium fluoroborate"],
    "K2Al2B2O7": ["KABO", "potassium aluminum borate", "potassium aluminium borate"],
    "YCa4O(BO3)3": ["YCOB", "yttrium calcium oxyborate", "Ca4YO(BO3)3"],
    "GdCa4O(BO3)3": ["GdCOB", "GDCOB", "gadolinium calcium oxyborate", "Ca4GdO(BO3)3"],
    "TmCa4O(BO3)3": ["TmCOB"],
    "La2CaB10O19": ["LCB", "lanthanum calcium borate"],
    "YAl3(BO3)4": ["YAB", "yttrium aluminum borate", "yttrium aluminium borate"],
    "Li2B4O7": ["LB4", "lithium tetraborate"],
    "LiRbB4O7": ["LRB4", "lithium rubidium tetraborate"],
    "Sr2Be2B2O7": ["SBBO", "strontium beryllium borate"],
    "Na3La9O3(BO3)8": ["NLBO"],
    "NH4B4O6F": ["ABF", "ammonium fluorooxoborate"],
    "KB5O8·4H2O": ["KB5", "potassium pentaborate"],
    # phosphates and arsenates
    "KH2PO4": ["KDP", "potassium dihydrogen phosphate"],
    "KD2PO4": ["DKDP", "KD*P", "deuterated KDP", "potassium dideuterium phosphate", "deuterated potassium dihydrogen phosphate"],
    "NH4H2PO4": ["ADP", "ammonium dihydrogen phosphate"],
    "NH4D2PO4": ["DADP", "deuterated ADP"],
    "RbH2PO4": ["RDP", "rubidium dihydrogen phosphate"],
    "RbD2PO4": ["DRDP", "deuterated RDP"],
    "KH2AsO4": ["KDA", "potassium dihydrogen arsenate"],
    "KD2AsO4": ["DKDA"],
    "NH4H2AsO4": ["ADA", "ammonium dihydrogen arsenate"],
    "NH4D2AsO4": ["DADA"],
    "RbH2AsO4": ["RDA", "rubidium dihydrogen arsenate"],
    "RbD2AsO4": ["DRDA"],
    "CsH2AsO4": ["CDA", "cesium dihydrogen arsenate"],
    "KTiOPO4": ["KTP", "PPKTP", "potassium titanyl phosphate"],
    "RbTiOPO4": ["RTP", "PPRTP", "rubidium titanyl phosphate"],
    "KTiOAsO4": ["KTA", "PPKTA", "potassium titanyl arsenate"],
    "RbTiOAsO4": ["RTA", "PPRTA", "rubidium titanyl arsenate"],
    "CsTiOAsO4": ["CTA", "cesium titanyl arsenate"],
    # niobates, tantalates, iodates
    "LiNbO3": ["LN", "PPLN", "CLN", "lithium niobate"],
    "MgO-LiNbO3": ["MgO:LN", "MgO:PPLN", "PPMgLN", "MgLN", "MgO:LiNbO3", "MgO-LN", "MgO-doped lithium niobate",
                   "magnesium-doped lithium niobate"],
    "LiTaO3": ["LT", "PPLT", "SLT", "PPSLT", "lithium tantalate"],
    "Mg-LiTaO3": ["MgO:SLT", "MgSLT", "MgO:LiTaO3", "Mg:LiTaO3", "MgO-doped lithium tantalate"],
    "KNbO3": ["KN", "potassium niobate"],
    "LiIO3": ["lithium iodate"],
    "HIO3": ["iodic acid", "alpha-HIO3", "α-HIO3"],
    "BaTiO3": ["BTO", "barium titanate"],
    "Ba2NaNb5O15": ["BNN", "BSN", "barium sodium niobate"],
    "SrxBa1-xNb2O6": ["SBN", "strontium barium niobate"],
    "La3Ga5.5Ta0.5O14": ["LGT", "langatate"],
    # mid-infrared chalcopyrites and chalcogenides
    "ZnGeP2": ["ZGP", "zinc germanium phosphide"],
    "AgGaS2": ["AGS", "silver thiogallate", "silver gallium sulfide", "silver gallium sulphide"],
    "AgGaSe2": ["AGSe", "AGSE", "silver gallium selenide"],
    "AgGaGeS4": ["AGGS", "silver gallium germanium sulfide"],
    "CdSiP2": ["CSP", "cadmium silicon phosphide"],
    "CdGeAs2": ["CGA", "cadmium germanium arsenide"],
    "GaSe": ["gallium selenide"],
    "GaS": ["gallium sulfide"],
    "HgGa2S4": ["HGS", "mercury thiogallate"],
    "CdGa2S4": ["cadmium thiogallate"],
    "LiGaS2": ["LGS", "lithium thiogallate"],
    "LiInS2": ["LIS", "lithium thioindate"],
    "LiInSe2": ["LISe", "lithium selenoindate"],
    "LiGaSe2": ["LGSe", "lithium selenogallate"],
    "BaGa4S7": ["BGS"],
    "BaGa4Se7": ["BGSe"],
    "BaGa2GeSe6": ["BGGSe"],
    "Ag3AsS3": ["proustite"],
    "Ag3SbS3": ["pyrargyrite"],
    "HgS": ["cinnabar"],
    "Tl3AsSe3": ["TAS", "thallium arsenic selenide"],
    "CdSe": ["cadmium selenide"],
    "CdS": ["cadmium sulfide"],
    # semiconductors for quasi phase matching
    "GaAs": ["gallium arsenide", "OP-GaAs", "OPGaAs"],
    "GaP": ["gallium phosphide", "OP-GaP", "OPGaP"],
    "ZnSe": ["zinc selenide"],
    "ZnTe": ["zinc telluride"],
    "CdTe": ["cadmium telluride"],
    "GaN": ["gallium nitride"],
    "AlN": ["aluminum nitride", "aluminium nitride"],
    "SiC": ["silicon carbide"],
    "ZnO": ["zinc oxide"],
    "Si": ["silicon"],
    "Ge": ["germanium"],
    "C": ["diamond"],
    # hosts, birefringent and linear crystals
    "SiO2": ["quartz", "α-quartz", "alpha-quartz", "crystal quartz", "crystalline quartz", "fused silica"],
    "Al2O3": ["sapphire", "corundum"],
    "CaCO3": ["calcite"],
    "TiO2": ["rutile"],
    "TeO2": ["paratellurite", "tellurium dioxide"],
    "YVO4": ["YVO", "yttrium vanadate"],
    "Y3Al5O12": ["YAG", "yttrium aluminum garnet", "yttrium aluminium garnet"],
    "YLiF4": ["YLF", "LiYF4", "yttrium lithium fluoride"],
    "MgBaF4": ["BMF", "BaMgF4", "barium magnesium fluoride"],
    "CaF2": ["fluorite", "calcium fluoride"],
    "MgF2": ["magnesium fluoride"],
    "BaF2": ["barium fluoride"],
    "LiF": ["lithium fluoride"],
    "BeAl2O4": ["alexandrite", "chrysoberyl"],
    # organics and others
    "CH4N2O - urea": ["urea"],
    "DAST": [],
    "BeSO4·4H2O": ["BeSO4"],
    "NaCOOH": ["sodium formate"],
    "Ba(COOH)2": ["barium formate"],
    "LiCOOH": ["LFM", "lithium formate"],
}


def _formula_like(name: str) -> bool:
    """A chemical formula (GaP, BiBO, LiNbO3): element symbols with a digit or a lower-case letter, matched in its
    own case only, so 'gap' or 'gas' in a sentence is not GaP or GaS."""
    import re

    from matrag.qdrant_store import _ELEMENTS

    parts = re.findall(r"[A-Z][a-z]?", name)
    return bool(parts) and all(p in _ELEMENTS for p in parts) and bool(re.search(r"[\da-z]", name)) \
        and re.fullmatch(r"(?:[A-Z][a-z]?|\d+(?:\.\d+)?|[()·:\-x])+", name) is not None


def alias_patterns() -> list[tuple[str, str, bool]]:
    """(name, formula, case-insensitive) for every name of every crystal, the longest first (so 'cesium lithium
    borate' is read before 'lithium borate', 'alpha-BBO' before 'BBO'). One-letter names (C) are never read."""
    out = []
    for formula, names in CRYSTAL_NAMES.items():
        for name in [formula, *names]:
            if len(name) < 2:
                continue
            fold = len(name) >= 3 and not _formula_like(name)
            out.append((name, formula, fold))
    return sorted(set(out), key=lambda t: -len(t[0]))


def find_crystals(text: str) -> tuple[list[str], str]:
    """The crystals a text names (their formulas, in order of first mention) and the text with those names blanked
    out. Same rules as web/src/text.js findCrystals."""
    import re

    found = []
    # names in their own case first (HgS is cinnabar, not HGS = HgGa2S4 read in any case), then in any case
    for name, formula, fold in [(n, f, False) for n, f, _ in alias_patterns()] + [t for t in alias_patterns() if t[2]]:
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", re.I if fold else 0)
        if pattern.search(text):
            text = pattern.sub(" , ", text)
            if formula not in found:
                found.append(formula)
    return found, text
