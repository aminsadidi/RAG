"""Crystal tags for the handbooks (Dmitriev et al. 1999, Nikogosyan 2005): one section per crystal, whose title
("3.2.1 KB5O8 · 4H2O, Potassium Pentaborate Tetrahydrate (KB5)") is the heading of only the first passages; the
tables further on carry their own headings ("Experimental values of refractive indices"). Every passage of a
section gets the crystal of the section in `crystals` (added to what enrich.py found), so the focused search
(web/src/index.js) finds the handbook's data on that crystal. Only ids and crystal names are written.

    python scripts/quality/tag_handbooks.py [--dry]      (QDRANT_URL, QDRANT_API_KEY)
"""
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import datamap  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HANDBOOKS = ["10.1007_978_3_540_46793_9", "10.1007_b138685"]
SECTION = re.compile(r"^(\d+\.\d+(?:\.\d+)?)\s+(.+?),\s+(.+)$")
NUMBERED = re.compile(r"^\d+\.\d+(?:\.\d+)?\s+[A-Z]")
SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def known():
    """normalized name -> site material, for the materials of the site's data and their synonyms."""
    names = {x["material"] for x in json.loads((ROOT / "web/public/ri/aniso.json").read_text())}
    names |= set(json.loads((ROOT / "web/public/ri/dij.json").read_text()))
    syn = json.loads((ROOT / "web/src/shared.json").read_text())["SYNONYMS"]
    out = {norm(m): m for m in names}
    out.update({norm(a): m for a, m in syn.items() if len(a) >= 2})
    return out


def norm(s):
    return re.sub(r"[\s·•.\-]", "", s.translate(SUB)).replace("*", "").lower()


def section_crystal(heading, names):
    """The site material of a section title, by its formula or by the abbreviation in parentheses."""
    m = SECTION.match(heading.strip().translate(SUB))
    if not m:
        return None
    formula, rest = m.group(2), m.group(3)
    cands = [formula, formula.split(":")[-1]] + re.findall(r"\(([^()]+)\)", rest)
    for c in cands:
        if norm(c) in names:
            return names[norm(c)]
    return None


def main():
    names = known()
    writes = collections.defaultdict(list)
    for doc in HANDBOOKS:
        pts = sorted(datamap.points([doc], ("node_id", "headings", "crystals")), key=lambda p: int(p["payload"]["node_id"].split("::")[1]))
        current = None
        for p in pts:
            h = str(p["payload"].get("headings") or "")
            if NUMBERED.match(h.strip()):  # a new section or chapter: its crystal, or none (a section on a
                current = section_crystal(h, names)  # crystal the site has no data for, "3.6 New Developments")
            if current and current not in (p["payload"].get("crystals") or []):
                writes[tuple(sorted(set(p["payload"].get("crystals") or []) | {current}))].append(p["id"])
    n = sum(len(v) for v in writes.values())
    by = collections.Counter(c for k, v in writes.items() for c in k for _ in v)
    print(f"{n} passages to tag, {len(by)} crystals: {dict(by.most_common(12))}")
    if "--dry" in sys.argv:
        return
    for crystals, ids in writes.items():
        datamap.qdrant("/collections/rag-optics/points/payload?wait=false", {"payload": {"crystals": list(crystals)}, "points": ids})
    print("done")


if __name__ == "__main__":
    main()
