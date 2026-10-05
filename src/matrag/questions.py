"""Larger evaluation sets for the retrieval benchmark.

Two kinds of questions, both with a known relevant paper (and, where known, page):

``build_curated``  -- written from data already checked by hand, no LLM needed:
    ri      refractiveindex.info: for each material whose data a corpus paper supplied, the
            refractive index asked in three ways (chemical formula, name, abbreviation),
            with a Persian version; any paper the database cites for the material is relevant.
    dij     the papers the nonlinear coefficients of the phase-matching tab were read from
            (data/<corpus>/nonlinear_coefficients.yml).
    paper   the dispersion formulas and thermo-optic formulas read from the collection's papers
            (paper_formulas.yml, thermo_optic.yml), with the page they are on.
    none    questions the collection cannot answer (the site must say "not found").

``generate``  -- questions an LLM writes from passages of the papers (one question per
    passage, the passage's paper and pages relevant); run on a GPU (Colab) with a local
    model. Questions copying the passage or not naming what they ask about are dropped.
"""

import csv
import json
import random
import re
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

FIELDS = ["id", "group", "question", "question_fa", "doc_id", "pages", "expected"]

# Questions the collection has no source for. In-domain-sounding ones (made-up crystals,
# properties far from optics) test the site's "not found" check harder than off-topic ones.
NOT_FOUND = [
    ("What is the boiling point of ethanol at sea level?", "نقطه‌ی جوش اتانول در سطح دریا چقدر است؟"),
    ("Who won the 2018 FIFA World Cup?", "قهرمان جام جهانی فوتبال ۲۰۱۸ کدام تیم بود؟"),
    ("How do I bake sourdough bread?", "نان خمیر ترش را چطور بپزم؟"),
    ("What is the capital of Australia?", "پایتخت استرالیا کجاست؟"),
    ("What is the half-life of carbon-14?", "نیمه‌عمر کربن ۱۴ چقدر است؟"),
    ("How does the stock market react to interest rate changes?", "بازار بورس به تغییر نرخ بهره چه واکنشی نشان می‌دهد؟"),
    ("What is the tensile strength of structural steel?", "استحکام کششی فولاد ساختمانی چقدر است؟"),
    ("What is the recommended daily intake of vitamin C?", "مقدار توصیه‌شده‌ی روزانه‌ی ویتامین C چقدر است؟"),
    ("When was the Eiffel Tower built?", "برج ایفل چه سالی ساخته شد؟"),
    ("What causes earthquakes along fault lines?", "علت زلزله در امتداد گسل‌ها چیست؟"),
    ("What is the melting point of chocolate?", "نقطه‌ی ذوب شکلات چقدر است؟"),
    ("How many moons does Jupiter have?", "مشتری چند قمر دارد؟"),
    ("What is the mechanism of action of penicillin?", "پنی‌سیلین چطور باکتری را از بین می‌برد؟"),
    ("What is the viscosity of honey at room temperature?", "گرانروی عسل در دمای اتاق چقدر است؟"),
    ("How does a jet engine produce thrust?", "موتور جت چطور نیروی پیشران تولید می‌کند؟"),
    ("What is the population of Tehran?", "جمعیت تهران چقدر است؟"),
    ("What is the elastic modulus of human bone?", "مدول کشسانی استخوان انسان چقدر است؟"),
    ("How is cheese made from milk?", "پنیر چطور از شیر درست می‌شود؟"),
    ("What is the Sellmeier equation of the crystal Zr7Q3Bx?", "معادله‌ی سلمایر بلور Zr7Q3Bx چیست؟"),
    ("Refractive index of unobtainium at 1064 nm", "ضریب شکست آنابتینیوم در ۱۰۶۴ نانومتر"),
    ("Nonlinear coefficient d33 of the crystal KXe4Mo9", "ضریب غیرخطی d33 بلور KXe4Mo9"),
    ("Thermal conductivity of chocolate cake", "رسانندگی گرمایی کیک شکلاتی"),
    ("Sellmeier coefficients of Pb7Rh2Q11 measured by prism method", "ضرایب سلمایر Pb7Rh2Q11 با روش منشور"),
    ("What is the electrical resistivity of copper wire used in houses?", "مقاومت ویژه‌ی سیم مسی ساختمان چقدر است؟"),
    ("Best fertilizer for tomato plants", "بهترین کود برای گوجه‌فرنگی"),
    ("What is the speed of sound in seawater?", "سرعت صوت در آب دریا چقدر است؟"),
    ("How do vaccines train the immune system?", "واکسن چطور سیستم ایمنی را آموزش می‌دهد؟"),
    ("What is the density of olive oil?", "چگالی روغن زیتون چقدر است؟"),
    ("Who wrote the Shahnameh?", "شاهنامه را چه کسی سروده است؟"),
    ("What is the gestation period of an elephant?", "دوره‌ی بارداری فیل چقدر است؟"),
    ("Refractive index of the fictional crystal Bz9Qt at 532 nm", "ضریب شکست بلور خیالی Bz9Qt در ۵۳۲ نانومتر"),
    ("Phase-matching angle of the crystal Xe2Kr3O9 for SHG", "زاویه‌ی تطبیق فاز بلور Xe2Kr3O9 برای SHG"),
    ("How fast does a cheetah run?", "یوزپلنگ با چه سرعتی می‌دود؟"),
    ("What is the pH of lemon juice?", "pH آب لیمو چقدر است؟"),
    ("How much does a Boeing 747 weigh?", "وزن هواپیمای بوئینگ ۷۴۷ چقدر است؟"),
    ("What is the compressive strength of concrete?", "مقاومت فشاری بتن چقدر است؟"),
    ("Which planet has the longest day?", "کدام سیاره طولانی‌ترین روز را دارد؟"),
    ("What are the side effects of ibuprofen?", "عوارض ایبوپروفن چیست؟"),
    ("How do bees make honey?", "زنبورها چطور عسل می‌سازند؟"),
    ("What is the freezing point of seawater?", "نقطه‌ی انجماد آب دریا چقدر است؟"),
]


def _split_name(material: str, name: str) -> tuple[str, str, str]:
    """(formula, English name, abbreviation) from a refractiveindex.info book name such as
    'LiB3O5 (Lithium triborate, LBO)'."""
    m = re.match(r"^\s*([^()]+?)\s*\((.*)\)\s*$", name or "")
    if not m:
        return material, "", ""
    parts = [p.strip() for p in m.group(2).split(",") if p.strip()]
    is_abbr = lambda p: len(p) <= 8 and " " not in p and sum(c.isupper() for c in p) >= 2  # noqa: E731
    english = parts[0] if parts and not is_abbr(parts[0]) else ""
    abbr = next((p for p in parts if is_abbr(p) and p != m.group(1).strip()), "")
    return m.group(1).strip(), english, abbr


def _ri_questions(database_dir: Path, doc_ids: set[str], names: dict[str, str]) -> list[dict]:
    from matrag.catalog import doi_key
    from matrag.references.refractiveindex import iter_entries

    by_material: dict[str, set[str]] = defaultdict(set)
    for e in iter_entries(database_dir):
        if e.doi and doi_key(e.doi) in doc_ids and e.page != "about":
            by_material[e.material].add(doi_key(e.doi))
    rows = []
    for material, docs in sorted(by_material.items()):
        formula, english, abbr = _split_name(material, names.get(material, ""))
        short = abbr or formula
        variants = [
            (f"What is the dispersion formula (Sellmeier coefficients) for the refractive index of {formula}?",
             f"فرمول پاشندگی (ضرایب سلمایر) ضریب شکست {formula} چیست؟"),
            (f"Refractive index of {english or formula} as a function of wavelength",
             f"ضریب شکست {short} بر حسب طول موج"),
            (f"{short} refractive index measurement", f"اندازه‌گیری ضریب شکست {short}"),
        ]
        seen = set()
        for k, (en, fa) in enumerate(variants, start=1):
            if en in seen:
                continue
            seen.add(en)
            rows.append({"id": f"ri-{material}-{k}", "group": "ri", "question": en, "question_fa": fa,
                         "doc_id": ";".join(sorted(docs)), "pages": "", "expected": ""})
    return rows


def _yaml(path: Path) -> list[dict]:
    import yaml

    return (yaml.safe_load(path.read_text(encoding="utf-8")) or []) if path.exists() else []


def _short(names: dict[str, str], material: str) -> tuple[str, str]:
    """(the formula with its abbreviation if any, e.g. 'LiB3O5 (LBO)'; the shortest name)."""
    formula, english, abbr = _split_name(material, names.get(material, ""))
    return (f"{formula} ({abbr})" if abbr else formula), abbr or formula


def _curated_paper_questions(corpus_dir: Path, doc_ids: set[str], names: dict[str, str]) -> list[dict]:
    rows = []
    for r in _yaml(corpus_dir / "nonlinear_coefficients.yml"):
        docs = sorted({s["doc_id"] for s in r["sources"] if s.get("doc_id") in doc_ids})
        if not docs:
            continue
        formula, short = _short(names, r["material"])
        rows.append({"id": f"dij-{r['material']}", "group": "dij",
                     "question": f"What are the second-order nonlinear optical coefficients d_ij of {formula}?",
                     "question_fa": f"ضرایب نوری غیرخطی مرتبه‌ی دوم (d) بلور {short} چقدر است؟",
                     "doc_id": ";".join(docs), "pages": "", "expected": ""})
    for p in _yaml(corpus_dir / "paper_formulas.yml"):
        if p["doc_id"] not in doc_ids:
            continue
        formula, short = _short(names, p["material"])
        rows.append({"id": f"paper-{p['material']}-{p['entries'][0]['page']}", "group": "paper",
                     "question": f"Sellmeier equations of {formula}: coefficients for the principal refractive indices",
                     "question_fa": f"معادله‌ی سلمایر و ضرایب آن برای ضریب شکست‌های اصلی {short}",
                     "doc_id": p["doc_id"], "pages": str(p["pdf_page"]), "expected": ""})
    for t in _yaml(corpus_dir / "thermo_optic.yml"):
        if t["doc_id"] not in doc_ids:
            continue
        formula, short = _short(names, t["material"])
        rows.append({"id": f"thermo-{t['material']}-{t['source']}", "group": "paper",
                     "question": f"Thermo-optic coefficients dn/dT of {formula} as a function of wavelength",
                     "question_fa": f"ضریب ترمواپتیک dn/dT بلور {short} بر حسب طول موج",
                     "doc_id": t["doc_id"], "pages": str(t["pdf_page"]), "expected": ""})
    return rows


def _merge(rows: list[dict]) -> list[dict]:
    """One question per text: the same question from several papers counts any of them (and their pages)."""
    merged: dict[str, dict] = {}
    for r in rows:
        if r["question"] in merged:
            m = merged[r["question"]]
            m["doc_id"] = ";".join(sorted(set(m["doc_id"].split(";")) | set(r["doc_id"].split(";"))))
            pages = set(filter(None, m["pages"].split(";"))) | set(filter(None, r["pages"].split(";")))
            m["pages"] = ";".join(sorted(pages, key=int))
        else:
            merged[r["question"]] = dict(r)
    return list(merged.values())


def build_curated(database_dir: Path, corpus_dir: Path, doc_ids: set[str], names: dict[str, str]) -> list[dict]:
    """All hand-checkable questions (see the module docstring); ``doc_ids``: full-text papers of the corpus,
    ``names``: refractiveindex.info book names by material."""
    rows = _ri_questions(database_dir, doc_ids, names) + _merge(_curated_paper_questions(corpus_dir, doc_ids, names))
    rows += [{"id": f"none-{i:02d}", "group": "none", "question": en, "question_fa": fa, "doc_id": "",
              "pages": "", "expected": "NOT_FOUND"} for i, (en, fa) in enumerate(NOT_FOUND, start=1)]
    return rows


def write_questions(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in FIELDS} for r in rows)


# --- questions written by an LLM from passages ---

PROMPT = """You write test questions for a search engine over optics research papers.
Read the passage below (from the paper "{title}"). Write ONE question that a physics student could
ask and that this passage answers with a specific fact (a number, a coefficient, a measured value, a method
or a material property). Rules:
- Name the material or system explicitly; never write "this paper", "the passage", "the table", "the authors".
- Do not copy phrases from the passage: ask in your own words, as a student would.
- The question must make sense without having seen the passage.
Also give the same question in natural Persian, and the short answer from the passage.
Reply with JSON only: {{"question": "...", "question_fa": "...", "answer": "..."}}

Passage:
{text}"""

_BAD = re.compile(r"\b(this|the) (paper|passage|table|study|work|article|figure|text)\b|\bauthors?\b", re.I)


def _ngrams(text: str, n: int = 6) -> set[tuple[str, ...]]:
    words = re.findall(r"[a-z0-9.]+", text.lower())
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def acceptable(question: str, passage: str) -> bool:
    """A usable generated question: long enough, self-contained, and not lifted from the passage."""
    if not (25 <= len(question) <= 300) or _BAD.search(question) or not question.rstrip().endswith("?"):
        return False
    return not (_ngrams(question) & _ngrams(passage))  # no 6 words in a row from the passage


def _parse(reply: str) -> dict | None:
    reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.S)
    m = re.search(r"\{.*\}", reply, re.S)
    try:
        data = json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) and data.get("question") else None


def candidate_passages(nodes, seed: int = 0) -> list:
    """Full-text passages worth a question (tables, or text with numbers), in a seeded random order,
    at most two per paper so that the set spreads over the whole collection."""
    rng = random.Random(seed)
    per_doc: dict[str, list] = defaultdict(list)
    for n in nodes:
        md = n.metadata
        text = n.get_content()
        if md.get("source_type") != "full_text_pdf" or len(text) < 300 or "References" in str(md.get("headings", "")):
            continue
        if md.get("content_type") == "table" or len(re.findall(r"\d+\.\d+", text)) >= 3:
            per_doc[md["doc_id"]].append(n)
    picked = []
    for doc in sorted(per_doc):
        picked += rng.sample(per_doc[doc], min(2, len(per_doc[doc])))
    rng.shuffle(picked)
    return picked


def _ask(llm, node) -> dict | None:
    """The LLM's question for one passage, or None if it is unusable."""
    md, text = node.metadata, node.get_content()
    title = str(md.get("reference", "")).split(". ")[1] if ". " in str(md.get("reference", "")) else ""
    try:
        data = _parse(llm.complete(PROMPT.format(title=title, text=text[:2500])).text)
    except Exception:  # a failed call must not stop the run
        return None
    if not data or not acceptable(data["question"], text) or not str(data.get("answer", "")).strip():
        return None
    return {"id": "gen-" + node.node_id.replace(":", "_"),
            "group": "generated-table" if md.get("content_type") == "table" else "generated-text",
            "question": data["question"].strip(), "question_fa": str(data.get("question_fa", "")).strip(),
            "doc_id": md["doc_id"], "pages": ";".join(p.strip() for p in str(md.get("pages", "")).split(",") if p.strip()),
            "expected": ""}


def _append(path: Path, line_or_row, header: bool = False) -> None:
    """Append and close at once: on a Google Drive mount a file is only uploaded when it is closed, so a
    file kept open is lost when Colab disconnects."""
    with path.open("a", encoding="utf-8", newline="") as f:
        if isinstance(line_or_row, dict):
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if header:
                w.writeheader()
            w.writerow(line_or_row)
        else:
            f.write(line_or_row + "\n")


def generate(nodes, llm, out: Path, n: int, seed: int = 0,
             on_progress: Callable[[int, int, str], None] | None = None, workers: int = 4) -> int:
    """Append up to ``n`` accepted questions to ``out`` (CSV, FIELDS); passages already used (accepted or
    rejected, listed in ``<out>.tried``) are skipped, so an interrupted run continues. ``workers`` passages
    are sent to the LLM at once (Ollama serves them in parallel with OLLAMA_NUM_PARALLEL).
    Returns the number of questions in the file."""
    from concurrent.futures import ThreadPoolExecutor

    done: dict[str, dict] = {}
    if out.exists():
        with out.open(encoding="utf-8", newline="") as f:
            done = {r["id"]: r for r in csv.DictReader(f)}
    tried = out.with_suffix(".tried")
    skipped = set(tried.read_text(encoding="utf-8").split()) if tried.exists() else set()
    out.parent.mkdir(parents=True, exist_ok=True)
    seen = set(done) | skipped
    todo = [nd for nd in candidate_passages(nodes, seed)
            if "gen-" + nd.node_id.replace(":", "_") not in seen]
    with ThreadPoolExecutor(max(1, workers)) as pool:
        for start in range(0, len(todo), max(1, workers)):
            if len(done) >= n:
                break
            batch = todo[start:start + max(1, workers)]
            for node, row in zip(batch, pool.map(lambda nd: _ask(llm, nd), batch)):
                qid = "gen-" + node.node_id.replace(":", "_")
                if row and len(done) < n:
                    _append(out, row, header=not out.exists() or out.stat().st_size == 0)
                    done[qid] = row
                    if on_progress:
                        on_progress(len(done) - 1, n, node.metadata.get("citation", node.metadata["doc_id"]))
                _append(tried, qid)
    return len(done)
