"""Data the collection holds but the site does not use yet, for the crystals and quantities that matter most.

For each (crystal, kind of data) gap, the passages the data map tags with that crystal and kind (`crystals`, `has`)
are taken from papers the data files do not cite for it yet; a language model behind an OpenAI-compatible API reads
each passage and returns what it states (values or formula, conditions, where in the paper) as JSON, or nothing.
Every answer is a candidate only: it is checked against the paper before anything goes into the data files.
The answers stay in the output folder (local); nothing here writes to the data files.

    python scripts/quality/gap_extract.py OUT_DIR [--model M] [--per-gap 8] [--workers 4]
        (QDRANT_URL, QDRANT_API_KEY; VISION_API_KEY, VISION_BASE_URL)
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import datamap  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/rag-optics"
# the crystals of most experiments (SHG/THG of Nd and Ti:sapphire lasers, SPDC sources, OPOs, mid-IR) and what they lack
GAPS = {
    "dndt": ["BaB2O4", "BaGa4S7", "KH2PO4", "KD2PO4", "MgO-LiNbO3", "LiTaO3", "Mg-LiTaO3", "RbTiOPO4", "CdSiP2",
             "YCa4O(BO3)3", "BiB3O6", "KTiOAsO4", "CsLiB6O10"],
    "thermal": ["KTiOPO4", "KTiOAsO4", "RbTiOPO4", "LiNbO3", "MgO-LiNbO3", "LiTaO3", "Mg-LiTaO3", "BaB2O4", "LiB3O5"],
    "damage": ["RbTiOPO4", "MgO-LiNbO3", "LiTaO3", "Mg-LiTaO3", "KH2PO4", "KD2PO4", "YCa4O(BO3)3", "CdSiP2", "GaAs",
               "GaP", "AgGaS2", "LiNbO3"],
    "sellmeier": ["KH2PO4", "BiB3O6", "Mg-LiTaO3", "LiTaO3", "CdSiP2", "MgO-LiNbO3", "RbTiOPO4"],
    "dij": ["BaGa4S7", "KTiOAsO4", "RbTiOPO4", "Mg-LiTaO3"],
}
ASK = {
    "dndt": "the temperature dependence of its refractive indices (dn/dT values, or a temperature-dependent Sellmeier or thermo-optic formula)",
    "thermal": "its thermal expansion coefficients (and, if given, thermal conductivity), per crystal axis",
    "damage": "a laser-induced damage threshold (with wavelength, pulse duration and repetition rate)",
    "sellmeier": "a Sellmeier (dispersion) equation for its refractive indices, or a table of measured refractive indices",
    "dij": "measured second-order nonlinear coefficients d_ij (pm/V) and how they were measured",
}
PROMPT = """You read one passage of a scientific paper on nonlinear optical crystals. Question: does this passage itself
state {ask} for the crystal {crystal}, as measured or derived in this paper (not only cited from another paper)?

Answer with JSON only:
{{"found": true or false,
  "cited_from_other_work": true or false,
  "quantity": "...", "axes_or_polarizations": "...",
  "values": "the numbers or the formula with every coefficient exactly as printed, with units",
  "conditions": "wavelength range, temperature range, pulse, sample (doping, growth)",
  "where": "equation / table / figure number as printed",
  "quote": "the shortest exact quote from the passage that holds the numbers"}}
If the passage only mentions the quantity without its numbers, found is false. Never invent or correct numbers.

Passage (from {cite}, page {page}):
{text}"""


def cited() -> dict[str, set[str]]:
    """material -> doc_ids the data files already take something from."""
    out: dict[str, set[str]] = {}
    add = lambda m, d: d and out.setdefault(m, set()).add(d)  # noqa: E731
    for b in yaml.safe_load((DATA / "thermo_optic.yml").read_text()):
        add(b["material"], b.get("doc_id"))
    for b in yaml.safe_load((DATA / "nonlinear_coefficients.yml").read_text()):
        for s in b.get("sources", []):
            add(b["material"], s.get("doc_id"))
    for b in yaml.safe_load((DATA / "paper_formulas.yml").read_text()):
        add(b["material"], b.get("doc_id"))
    for p in yaml.safe_load((DATA / "crystal_properties.yml").read_text()) or []:
        m = p.get("material")
        for v in p.values():
            if isinstance(v, dict):
                add(m, v.get("doc_id"))
            elif isinstance(v, list):
                for s in v:
                    if isinstance(s, dict):
                        add(m, s.get("doc_id"))
    return out


def candidates(per_gap: int) -> list[dict]:
    known, out = cited(), []
    for kind, crystals in GAPS.items():
        for m in crystals:
            r = datamap.qdrant("/collections/rag-optics/points/scroll", {
                "limit": 400, "with_payload": ["doc_id", "node_id", "text", "pages", "citation", "junk"],
                "filter": {"must": [{"key": "crystals", "match": {"value": m}}, {"key": "has", "match": {"value": kind}}]}})
            seen, picked = set(), []
            for p in sorted(r["points"], key=lambda p: float(p["payload"].get("junk") or 0)):
                pl = p["payload"]
                if pl["doc_id"] in known.get(m, set()) or pl["doc_id"] in seen:
                    continue
                seen.add(pl["doc_id"])
                picked.append({"kind": kind, "crystal": m, **{k: pl.get(k) for k in ("doc_id", "node_id", "text", "pages", "citation")}})
                if len(picked) >= per_gap:
                    break
            out += picked
    return out


def ask(prompt: str, model: str) -> str:
    body = {"model": model, "temperature": 0, "messages": [{"role": "user", "content": prompt}]}
    url = os.environ.get("VISION_BASE_URL", "https://oxionai.com/v1").rstrip("/") + "/chat/completions"
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
                "Authorization": "Bearer " + os.environ["VISION_API_KEY"], "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == 7:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 7:
                raise
        time.sleep(min(300, 15 * 2 ** attempt))
    raise RuntimeError("unreachable")


def parse(answer: str) -> dict:
    s = answer[answer.find("{"): answer.rfind("}") + 1]
    try:
        return json.loads(s)
    except ValueError:
        return {"found": None, "raw": answer[:2000]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--per-gap", type=int, default=8)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cands = candidates(a.per_gap)
    (out / "candidates.json").write_text(json.dumps(cands, ensure_ascii=False))
    print(f"{len(cands)} passages for {len({(c['kind'], c['crystal']) for c in cands})} gaps", flush=True)

    def one(c):
        f = out / f"{c['kind']}__{c['node_id'].replace('/', '_')}__{c['crystal']}.json"
        if not f.exists():
            ans = ask(PROMPT.format(ask=ASK[c["kind"]], crystal=c["crystal"], cite=c.get("citation") or c["doc_id"],
                                    page=c.get("pages"), text=(c["text"] or "")[:6000]), a.model)
            f.write_text(json.dumps({**{k: c[k] for k in ("kind", "crystal", "doc_id", "node_id", "pages")},
                                     "answer": parse(ans)}, ensure_ascii=False))
        return json.loads(f.read_text())

    with ThreadPoolExecutor(a.workers) as ex:
        rows = list(ex.map(one, cands))
    found = [r for r in rows if r["answer"].get("found") and not r["answer"].get("cited_from_other_work")]
    (out / "found.json").write_text(json.dumps(found, ensure_ascii=False, indent=1))
    print(f"{len(found)} passages state new data (not cited from elsewhere):")
    for r in found:
        print(f"  {r['kind']:9} {r['crystal']:14} {r['node_id']}  {str(r['answer'].get('values'))[:90]}")


if __name__ == "__main__":
    main()
