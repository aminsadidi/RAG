"""Gold questions from the site's own data: every crystal whose dispersion formula (paper_formulas.yml),
thermo-optic formula (thermo_optic.yml) or nonlinear coefficients (nonlinear_coefficients.yml) were read from
a paper of the collection gives one question, and those papers are its accepted answers. The answers were
checked when the data was entered (page by page), so these questions need no other judge; papers that also
answer but gave no value to the site are added later by judge_alternatives (SubQ, then a person).

    python scripts/quality/gold_from_data.py          (writes data/rag-optics/gold/data_questions.csv)
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/rag-optics"
OUT = DATA / "gold/data_questions.csv"

QUESTION = {
    "sellmeier": ("What is the Sellmeier equation (dispersion formula) for the refractive indices of {m}?",
                  "معادله‌ی سلمایر (فرمول پاشندگی) ضرایب شکست {m} چیست؟"),
    "dndt": ("What is the temperature dependence of the refractive indices (dn/dT, thermo-optic formula) of {m}?",
             "وابستگی دمایی ضرایب شکست (dn/dT، فرمول ترمواپتیک) {m} چیست؟"),
    "dij": ("What are the measured second-order nonlinear coefficients d_ij of {m}?",
            "ضرایب غیرخطی مرتبه‌ی دوم (d_ij) اندازه‌گیری‌شده‌ی {m} چقدر است؟"),
}


def main():
    papers = {p["doc_id"].lower(): p["doc_id"] for p in json.loads((ROOT / "web/src/papers.json").read_text(encoding="utf-8"))}
    synonyms = json.loads((ROOT / "web/src/shared.json").read_text(encoding="utf-8"))["SYNONYMS"]
    abbr = defaultdict(list)
    for a, m in synonyms.items():
        if a.isupper() or len(a) <= 5:
            abbr[m].append(a)
    answers = defaultdict(set)  # (kind, material) -> doc_ids in the collection

    def add(kind, material, doc_id):
        d = papers.get(str(doc_id or "").replace("/", "_").lower())
        if d:
            answers[(kind, material)].add(d)

    for e in yaml.safe_load((DATA / "paper_formulas.yml").read_text(encoding="utf-8")):
        add("sellmeier", e["material"], e.get("doc_id"))
    for e in yaml.safe_load((DATA / "thermo_optic.yml").read_text(encoding="utf-8")):
        add("dndt", e["material"], e.get("doc_id"))
    for e in yaml.safe_load((DATA / "nonlinear_coefficients.yml").read_text(encoding="utf-8")):
        for s in e.get("sources") or []:
            add("dij", e["material"], s.get("doc_id"))

    rows = []
    for (kind, material), docs in sorted(answers.items()):
        names = [a for a in abbr.get(material, []) if a.lower() != material.lower()][:1]
        m = f"{material} ({names[0]})" if names else material
        q, q_fa = QUESTION[kind]
        rows.append({"id": f"data-{kind}-{re.sub(r'[^A-Za-z0-9.]+', '_', material)}", "group": f"data-{kind}",
                     "question": q.format(m=m), "question_fa": q_fa.format(m=m),
                     "doc_id": ";".join(sorted(docs)), "pages": "", "expected": ""})
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "group", "question", "question_fa", "doc_id", "pages", "expected"])
        w.writeheader()
        w.writerows(rows)
    by = defaultdict(int)
    for r in rows:
        by[r["group"]] += 1
    print(f"{len(rows)} questions written to {OUT.relative_to(ROOT)}: {dict(by)}")


if __name__ == "__main__":
    main()
