#!/usr/bin/env python3
"""
Audit Engine for Task 1
Audits all entries in thermo_optic_expanded.yml (25 entries) and nonlinear_tensors_expanded.yml (71 entries).
Outputs: research_package/candidates/audit.jsonl
"""

import os
import sys
import json
import yaml
import glob
import pypdf
import gdown

CANDIDATES_DIR = "/home/aminsadidi11584/RAG/research_package/candidates"
SCRATCH_DIR = "/home/aminsadidi11584/.gemini/antigravity-cli/brain/f17647dd-8096-4ef7-aa21-ecebc5ff42f7/scratch"
DATA_DIR = "/home/aminsadidi11584/RAG/research_package/data"
WEB_DIR = "/home/aminsadidi11584/RAG/web/src"

os.makedirs(CANDIDATES_DIR, exist_ok=True)
os.makedirs(SCRATCH_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(CANDIDATES_DIR, "audit.jsonl")

# Load reference databases
thermo_yml = yaml.safe_load(open(os.path.join(DATA_DIR, "thermo_optic_expanded.yml")))
tensors_yml = yaml.safe_load(open(os.path.join(DATA_DIR, "nonlinear_tensors_expanded.yml")))
papers_json = json.load(open(os.path.join(WEB_DIR, "papers.json")))
manifest = json.load(open(os.path.join(DATA_DIR, "drive_papers_manifest.json")))

papers_dict = {p.get("doc_id"): p for p in papers_json if p.get("doc_id")}
manifest_by_clean = {}
for m in manifest:
    fn = m["filename"].lower()
    manifest_by_clean[fn] = m
    manifest_by_clean[fn.replace(".pdf", "")] = m

core_files = {os.path.basename(f).lower(): f for f in glob.glob("/home/aminsadidi11584/papers_core/*.pdf")}


def get_pdf_for_entry(doc_id, cite, material=None):
    """Locate or download PDF, returning (source_type, path_or_name, real_doc_id)."""
    # 1. Known special mappings in core
    if cite and "dolev" in cite.lower():
        return "core", "/home/aminsadidi11584/papers_core/dolev2009.pdf", "10.1007/s00340-009-3502-3"
    if cite and "sugawara" in cite.lower():
        return "core", "/home/aminsadidi11584/papers_core/sugawara1998.pdf", "10.1016/S0038-1098(98)00190-2"
    if cite and "zhai" in cite.lower():
        return "core", "/home/aminsadidi11584/papers_core/zhai2013.pdf", "10.1016/j.optmat.2013.09.017"
    if cite and "ghosh" in cite.lower() and ("1992" in cite or "adp" in (material or "").lower() or "kdp" in (material or "").lower()):
        return "core", "/home/aminsadidi11584/papers_core/ghosh1992.pdf", "10.1117/12.637003"
    if cite and "petrov" in cite.lower() and "2015" in cite:
        return "core", "/home/aminsadidi11584/papers_core/petrov2015.pdf", "10.1016/j.pquantelec.2015.04.001"
    if cite and "petrov" in cite.lower() and "2012" in cite:
        return "core", "/home/aminsadidi11584/papers_core/petrov2012.pdf", "10.1016/j.mser.2012.04.001"
    if cite and "jerphagnon" in cite.lower():
        return "core", "/home/aminsadidi11584/papers_core/jerphagnon1970.pdf", "10.1103/PhysRevB.1.1739"
    if cite and "hellwig" in cite.lower():
        return "core", "/home/aminsadidi11584/papers_core/hellwig1998.pdf", "10.1016/S0038-1098(98)00538-9"
    if cite and "li" in cite.lower() and "2016" in cite:
        return "core", "/home/aminsadidi11584/papers_core/li2016.pdf", "10.1016/j.optmat.2016.10.023"
    if cite and "pack" in cite.lower() and "2003" in cite:
        return "core", "/home/aminsadidi11584/papers_core/pack2003.pdf", "10.1364/JOSAB.20.002109"
    if cite and "pack" in cite.lower() and "2004" in cite:
        return "core", "/home/aminsadidi11584/papers_core/pack2004.pdf", "10.1364/AO.43.003319"
    if cite and "pack" in cite.lower() and "2005" in cite:
        return "core", "/home/aminsadidi11584/papers_core/pack2005.pdf", "10.1364/JOSAB.22.000417"
    if cite and "shoji" in cite.lower() and "1999" in cite:
        return "core", "/home/aminsadidi11584/papers_core/shoji1999.pdf", "10.1364/JOSAB.16.000620"
    if cite and "umemura" in cite.lower() and "2001" in cite:
        return "core", "/home/aminsadidi11584/papers_core/umemura2001.pdf", "10.1364/ASSL.1999.PD15"
    if cite and "miyata" in cite.lower() and "2009" in cite:
        return "core", "/home/aminsadidi11584/papers_core/miyata2009.pdf", "10.1364/OL.34.000500"
    if cite and "gayer" in cite.lower() and ("2008" in cite or "2010" in cite):
        return "core", "/home/aminsadidi11584/papers_core/gayer2010.pdf", "10.1007/s00340-008-2998-2"

    # 2. Check Drive manifest by doc_id
    if doc_id:
        doc_str = str(doc_id).replace("/", "-").replace("_", "-")
        target_fn = None
        for fn, m in manifest_by_clean.items():
            if doc_str.lower() in fn:
                target_fn = m["filename"]
                drive_item = m
                break
        if target_fn:
            local_pdf = os.path.join(SCRATCH_DIR, target_fn)
            if not os.path.exists(local_pdf):
                gdown.download(id=drive_item["id"], output=local_pdf, quiet=True)
            return "drive", local_pdf, str(doc_id).replace("_", "/")

    return "not_found", None, str(doc_id) if doc_id else "not_found"

print("Helper ready.")
