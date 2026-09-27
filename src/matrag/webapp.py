"""Web interface (Gradio).

Tabs: papers (upload / arXiv / folder / list / remove), question answering,
context pack for chat assistants, property extraction and HITRAN spectra.

Run with ``matrag app`` (local) or from the Colab notebook.
"""

import re
from datetime import datetime
from pathlib import Path

import gradio as gr
import pandas as pd

from matrag.config import get_settings
from matrag.pipeline import Workspace, list_corpora, slugify
from matrag.qa import format_source_label
from matrag.references.hitran import MOLECULES
from matrag.retrieve import RetrievalMode

LANGUAGES = {"فارسی": "Persian", "English": "English"}

EXTRACT_COLUMNS = ["citation", "pages", "material", "property", "value_text", "unit", "uncertainty",
                   "spectral_position", "temperature_K", "pressure", "broadener", "method",
                   "value_in_source", "evidence_verified", "plausible", "evidence"]

GUIDE = """
### راهنمای استفاده

1. **مقاله‌ها:** فایل‌های PDF را بکشید و رها کنید (یا شناسه‌ی arXiv بدهید) و «افزودن و پردازش» را بزنید.
   هر مقاله فقط یک بار پردازش می‌شود. مشخصات مقاله (عنوان، نویسندگان، سال) خودکار از arXiv/Crossref گرفته می‌شود.
2. **پرسش و پاسخ:** سؤال را بنویسید (انگلیسی بهتر جست‌وجو می‌شود؛ زبان جواب را جدا انتخاب کنید).
   گزینه‌ی «مقایسه با حالت بدون RAG» جواب همان مدل را بدون منابع هم نشان می‌دهد.
3. **بسته‌ی منابع:** فایلی می‌سازد که می‌توانید در چت Gemini یا هر هوش مصنوعی دیگری آپلود کنید (بدون مصرف API).
4. **استخراج خواص:** نام خاصیت‌ها را بنویسید؛ جدول مقدارها با منبع و صفحه ساخته می‌شود.
   ستون `value_in_source` نشان می‌دهد عدد واقعاً در متن مقاله هست یا نه؛ ستون `plausible` نشان می‌دهد
   مقدار در بازه‌ی فیزیکی معقول آن خاصیت هست یا نه (بازه‌ها در `data/<corpus>/profile.yml` قابل تغییرند).
5. **طیف:** طیف جذبی HITRAN را رسم می‌کند و با فایل استخراج، طیف دوم با مقدارهای مقاله را کنارش می‌گذارد.

**مجموعه (corpus):** هر موضوع مقاله‌ها و پایگاه داده‌ی جداگانه دارد. برای موضوع جدید، اسم تازه‌ای تایپ کنید.
"""

CSS = """
.rtl, .rtl * { direction: rtl; text-align: right; }
footer { display: none !important; }
"""

_workspaces: dict[str, Workspace] = {}


def _ws(corpus: str) -> Workspace:
    corpus = re.sub(r"[^\w-]+", "_", (corpus or "").strip()) or get_settings().corpus
    if corpus not in _workspaces:
        _workspaces[corpus] = Workspace(corpus=corpus)
    return _workspaces[corpus]


def _results_root() -> Path:
    """results/app/, next to the data folder (on Google Drive in Colab)."""
    return get_settings().data_dir.resolve().parent / "results" / "app"


def _results_path(ws: Workspace, kind: str, name: str, suffix: str) -> Path:
    """results/app/<kind>/<corpus>_<name>_<time><suffix>"""
    folder = _results_root() / kind
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{ws.settings.corpus}_{name}_{datetime.now():%Y%m%d-%H%M%S}{suffix}"


def _auto_dir(text: str) -> str:
    """Wrap text so Persian renders right-to-left and English left-to-right."""
    return f'<div dir="auto">\n\n{text}\n\n</div>'


# --- papers tab ---

def papers_table(corpus: str) -> pd.DataFrame:
    rows = [
        {"doc_id": p.doc_id, "citation": p.short_citation(), "title": p.title or "", "year": p.year,
         "journal": p.journal or "", "doi": p.doi or "", "chunks": n}
        for p, n in _ws(corpus).papers()
    ]
    return pd.DataFrame(rows, columns=["doc_id", "citation", "title", "year", "journal", "doi", "chunks"])


def paper_choices(corpus: str) -> list[tuple[str, str]]:
    return [(f"{p.short_citation()} — {(p.title or p.doc_id)[:70]}", p.doc_id) for p, _ in _ws(corpus).papers()]


def _refresh_paper_lists(corpus: str):
    """New values for: papers table, remove dropdown, and the three paper filters."""
    choices = paper_choices(corpus)
    filters = [gr.update(choices=choices, value=[]) for _ in range(3)]
    return (papers_table(corpus), gr.update(choices=choices, value=None), *filters)


def ingest_uploads(corpus: str, files: list[str] | None, arxiv_ids: str, progress=gr.Progress()):
    ws = _ws(corpus)
    paths = ws.add_files([Path(f) for f in files or []])
    for arxiv_id in [a for a in re.split(r"[\s,]+", arxiv_ids or "") if a]:
        try:
            paths.append(ws.download_arxiv(arxiv_id))
        except Exception as e:
            gr.Warning(f"arXiv {arxiv_id}: {e}")
    if not paths:
        raise gr.Error("هیچ فایلی انتخاب نشده است.")

    def report(i, n, name):
        progress(i / max(n, 1), desc=f"{i}/{n}: {name}")

    results = ws.ingest(paths, on_progress=report)
    lines = []
    for r in results:
        if r.error:
            lines.append(f"- ❌ `{r.file}`: {r.error}")
        elif r.skipped:
            lines.append(f"- ⏭️ `{r.file}` ({r.citation}): از قبل در پایگاه داده بود")
        else:
            lines.append(f"- ✅ `{r.file}` → **{r.citation}**، {r.chunks} قطعه")
    return ("\n".join(lines), *_refresh_paper_lists(corpus))


def ingest_folder(corpus: str, progress=gr.Progress()):
    """Index every paper in the corpus folder that is not indexed yet (e.g. PDFs copied into Drive)."""
    ws = _ws(corpus)

    def report(i, n, name):
        progress(i / max(n, 1), desc=f"{i}/{n}: {name}")

    results = ws.ingest(on_progress=report)
    new = [r for r in results if not r.skipped]
    if not results:
        lines = [f"پوشه‌ی `{ws.settings.raw_pdf_dir}` خالی است."]
    else:
        lines = [f"- ❌ `{r.file}`: {r.error}" if r.error else f"- ✅ `{r.file}` → **{r.citation}**، {r.chunks} قطعه"
                 for r in new] or ["همه‌ی مقاله‌های پوشه از قبل پردازش شده بودند."]
    return ("\n".join(lines), *_refresh_paper_lists(corpus))


def remove_paper(corpus: str, doc_id: str | None):
    if not doc_id:
        raise gr.Error("مقاله‌ای برای حذف انتخاب نشده است.")
    _ws(corpus).remove_paper(doc_id)
    return (f"🗑️ `{doc_id}` حذف شد.", *_refresh_paper_lists(corpus))


# --- question answering tab ---

def ask(corpus, question, provider, language, mode, top_k, doc_ids, compare, progress=gr.Progress()):
    if not (question or "").strip():
        raise gr.Error("سؤال خالی است.")
    ws = _ws(corpus)
    lang = LANGUAGES.get(language)
    progress(0.1, desc="بازیابی منابع و تولید جواب...")
    try:
        answer = ws.ask(question, provider, RetrievalMode(mode), int(top_k), doc_ids or None, lang)
    except ValueError as e:
        raise gr.Error(str(e))
    sources = pd.DataFrame([
        {"#": i, "source": format_source_label(n), "score": round(n.score or 0, 3),
         "excerpt": " ".join(n.get_content().split())[:400]}
        for i, n in enumerate(answer.sources, start=1)
    ], columns=["#", "source", "score", "excerpt"])
    baseline = ""
    if compare:
        progress(0.6, desc="جواب بدون RAG...")
        baseline = _auto_dir(ws.ask_without_rag(question, provider, lang).text)
    header = f"*{ws.llm_name(provider)} · {mode} · top {int(top_k)}*\n\n"
    return _auto_dir(header + answer.text), baseline, sources


# --- context pack tab ---

def make_pack(corpus, question, language, mode, top_k, doc_ids):
    if not (question or "").strip():
        raise gr.Error("سؤال خالی است.")
    ws = _ws(corpus)
    try:
        text = ws.pack(question, LANGUAGES.get(language), RetrievalMode(mode), int(top_k), doc_ids or None)
    except ValueError as e:
        raise gr.Error(str(e))
    path = _results_path(ws, "packs", slugify(question, 40), ".md")
    path.write_text(text, encoding="utf-8")
    return text, str(path)


# --- extraction tab ---

def run_extract(corpus, properties, provider, exhaustive, mode, top_k, doc_ids, progress=gr.Progress()):
    props = [p.strip() for p in re.split(r"[,\n]", properties or "") if p.strip()]
    if not props:
        raise gr.Error("حداقل یک خاصیت بنویسید.")
    ws = _ws(corpus)
    progress(0.05, desc="در حال استخراج... (هر قطعه یک درخواست به مدل)")
    try:
        records = ws.extract(props, provider, exhaustive, RetrievalMode(mode), int(top_k), doc_ids or None)
    except ValueError as e:
        raise gr.Error(str(e))
    library = ws.library
    rows = [r.model_dump() | {"citation": library.get(r.doc_id).short_citation()} for r in records]
    df = pd.DataFrame(rows, columns=EXTRACT_COLUMNS + ["doc_id", "node_id", "llm"])
    path = _results_path(ws, "extracted", "values", ".csv")
    df.to_csv(path, index=False)
    ok = int(df["value_in_source"].sum()) if len(df) else 0
    implausible = int((df["plausible"] == False).sum()) if len(df) else 0  # noqa: E712 (None = unknown)
    summary = (f"**{len(df)}** مقدار استخراج شد؛ **{ok}** مقدار عیناً در متن منبع پیدا شد؛ "
               f"**{implausible}** مقدار خارج از بازه‌ی فیزیکی معقول بود. مدل: `{ws.llm_name(provider)}`")
    shown = df[EXTRACT_COLUMNS].copy()
    shown["evidence"] = shown["evidence"].str.slice(0, 120)  # full text is in the CSV
    return summary, shown, str(path)


# --- spectrum tab ---

# Two categorical slots of the validated default palette (blue, orange); the paper
# curve is also dashed so the series never rely on color alone.
_SERIES = {"hitran": "#2a78d6", "paper": "#eb6834"}


def spectrum_figure(nu, sigma_hitran, sigma_paper, title: str):
    """Cross-sections on top; when the paper curve exists, their difference below on its own axis."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    rows = 2 if sigma_paper is not None else 1
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        row_heights=[0.7, 0.3] if rows == 2 else [1.0])
    fig.add_trace(go.Scatter(x=nu, y=sigma_hitran, name="HITRAN", mode="lines",
                             line=dict(color=_SERIES["hitran"], width=2)), row=1, col=1)
    if sigma_paper is not None:
        fig.add_trace(go.Scatter(x=nu, y=sigma_paper, name="HITRAN + مقادیر مقاله", mode="lines",
                                 line=dict(color=_SERIES["paper"], width=2, dash="dash")), row=1, col=1)
        fig.add_trace(go.Scatter(x=nu, y=sigma_paper - sigma_hitran, name="اختلاف (مقاله − HITRAN)",
                                 mode="lines", line=dict(color=_SERIES["paper"], width=2)), row=2, col=1)
        fig.update_yaxes(title_text="Δσ", row=2, col=1)
    grid = dict(gridcolor="#e8e7e3", zeroline=False)
    fig.update_xaxes(**grid, tickformat=".2f")
    fig.update_xaxes(title_text="wavenumber (cm⁻¹)", row=rows, col=1)
    fig.update_yaxes(**grid, exponentformat="power")
    fig.update_yaxes(title_text="σ (cm²/molecule)", row=1, col=1)
    fig.update_layout(
        title=title, hovermode="x unified", height=620 if rows == 2 else 480,
        margin=dict(l=70, r=20, t=60, b=60), plot_bgcolor="#fcfcfb", paper_bgcolor="#fcfcfb",
        font=dict(color="#0b0b0b"),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"),
    )
    return fig


def run_spectrum(molecule, isotopologue, nu_min, nu_max, temperature, pressure, records_file):
    from matrag.evaluate import load_records
    from matrag.references import hitran

    if not nu_max > nu_min:
        raise gr.Error("انتهای بازه باید از ابتدای آن بزرگ‌تر باشد.")
    if nu_max - nu_min > 200:
        raise gr.Error("بازه‌ی عدد موج حداکثر 200 cm⁻¹ باشد (برای سرعت).")
    iso = int(isotopologue)
    try:
        lines = hitran.fetch_lines(molecule, iso, float(nu_min), float(nu_max))
    except Exception as e:
        raise gr.Error(f"دریافت داده از HITRAN ناموفق بود: {e}")
    if not lines:
        raise gr.Error("در این بازه خطی در HITRAN نیست.")
    overrides = []
    if records_file:
        overrides = hitran.overrides_from_records(load_records(Path(records_file)), lines)
    nu, sig_h, sig_p = hitran.absorption_spectra(molecule, iso, float(nu_min), float(nu_max),
                                                  float(temperature), float(pressure), overrides)
    title = f"{molecule} (isotopologue {iso}) · T = {temperature:g} K · p = {pressure:g} atm · {len(lines)} lines"
    table = pd.DataFrame(overrides, columns=["line", "parameter", "hitran", "paper", "source"])
    note = (f"**{len(overrides)}** پارامتر از مقاله جایگزین مقدار HITRAN شد. "
            "فرض بر این است که واحدها همان واحدهای HITRAN هستند (cm⁻¹/atm، cm⁻¹/(molecule·cm⁻²))؛ ستون unit جدول استخراج را چک کنید."
            if overrides else "فقط طیف HITRAN رسم شد (فایل استخراج داده نشده یا خطی از آن با HITRAN تطبیق نیافت).")
    return spectrum_figure(nu, sig_h, sig_p, title), note, table


# --- layout ---

def build_app() -> gr.Blocks:
    settings = get_settings()
    corpora = sorted(set(list_corpora(settings)) | {settings.corpus})
    initial_choices = paper_choices(settings.corpus)

    with gr.Blocks(title="RAG مواد") as demo:
        gr.Markdown("# سیستم بازیابی و استخراج خواص فیزیکی مواد از مقالات (RAG)", elem_classes="rtl")
        with gr.Row():
            corpus = gr.Dropdown(corpora, value=settings.corpus, allow_custom_value=True,
                                 label="مجموعه‌ی مقالات (corpus)", scale=2)
            provider = gr.Dropdown(["ollama", "gemini"], value=settings.llm_provider,
                                   label="مدل زبانی", scale=1)

        with gr.Tab("📚 مقاله‌ها"):
            with gr.Row():
                files = gr.File(file_count="multiple", file_types=[".pdf"], type="filepath",
                                label="فایل‌های PDF", scale=2)
                with gr.Column(scale=1):
                    arxiv_ids = gr.Textbox(label="یا شناسه‌های arXiv (با فاصله یا کاما)",
                                           placeholder="1906.01475, 2111.01212")
                    add_btn = gr.Button("افزودن و پردازش", variant="primary")
                    folder_btn = gr.Button("پردازش همه‌ی مقاله‌های پوشه")
                    gr.Markdown("برای افزودن تعداد زیاد مقاله، PDFها را مستقیم در پوشه‌ی "
                                "`data/<corpus>/pdfs` (در کولب: `matrag_data/data/<corpus>/pdfs` در Drive) "
                                "بگذارید و این دکمه را بزنید.", elem_classes="rtl")
            ingest_log = gr.Markdown(elem_classes="rtl")
            table = gr.Dataframe(papers_table(settings.corpus), label="مقاله‌های پایگاه داده",
                                 interactive=False, wrap=True)
            with gr.Row():
                to_remove = gr.Dropdown(initial_choices, label="حذف مقاله", scale=3)
                remove_btn = gr.Button("حذف", variant="stop", scale=1)

        with gr.Tab("❓ پرسش و پاسخ"):
            question = gr.Textbox(label="سؤال", lines=2,
                                  value="How much larger are water-vapor-broadened half-widths of CO2 lines "
                                        "compared to air-broadened ones?")
            with gr.Row():
                language = gr.Dropdown(list(LANGUAGES), value="فارسی", label="زبان جواب")
                mode = gr.Dropdown([m.value for m in RetrievalMode], value="hybrid", label="روش بازیابی")
                top_k = gr.Slider(1, 20, value=6, step=1, label="تعداد منابع")
                compare = gr.Checkbox(value=True, label="مقایسه با حالت بدون RAG")
            ask_docs = gr.Dropdown(initial_choices, multiselect=True, label="فقط در این مقاله‌ها (اختیاری)")
            ask_btn = gr.Button("بپرس", variant="primary")
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### ✅ با RAG (بر اساس مقاله‌ها)", elem_classes="rtl")
                    answer = gr.Markdown()
                with gr.Column():
                    gr.Markdown("#### ⚪ بدون RAG (فقط حافظه‌ی مدل)", elem_classes="rtl")
                    baseline = gr.Markdown()
            sources = gr.Dataframe(label="منابع بازیابی‌شده", interactive=False, wrap=True)

        with gr.Tab("📄 بسته‌ی منابع برای چت"):
            gr.Markdown("فایلی می‌سازد شامل دستورالعمل، منابع شماره‌دار و سؤال؛ آن را در چت Gemini یا هر "
                        "هوش مصنوعی دیگری آپلود کنید و بنویسید «به سؤال داخل فایل جواب بده».", elem_classes="rtl")
            pack_question = gr.Textbox(label="سؤال", lines=2)
            with gr.Row():
                pack_language = gr.Dropdown(list(LANGUAGES), value="فارسی", label="زبان جواب")
                pack_mode = gr.Dropdown([m.value for m in RetrievalMode], value="hybrid", label="روش بازیابی")
                pack_top_k = gr.Slider(1, 20, value=6, step=1, label="تعداد منابع")
            pack_docs = gr.Dropdown(initial_choices, multiselect=True, label="فقط در این مقاله‌ها (اختیاری)")
            pack_btn = gr.Button("ساخت فایل", variant="primary")
            pack_file = gr.File(label="دانلود فایل")
            pack_text = gr.Textbox(label="پیش‌نمایش", lines=16, buttons=["copy"])

        with gr.Tab("📊 استخراج خواص"):
            properties = gr.Textbox(label="خاصیت‌ها (با کاما جدا کنید)", lines=2,
                                    value=", ".join(_ws(settings.corpus).default_properties()))
            with gr.Row():
                exhaustive = gr.Checkbox(value=False, label="همه‌ی قطعه‌ها (کامل‌تر ولی خیلی کندتر)")
                ex_mode = gr.Dropdown([m.value for m in RetrievalMode], value="hybrid", label="روش بازیابی")
                ex_top_k = gr.Slider(1, 20, value=4, step=1, label="قطعه برای هر خاصیت")
            ex_docs = gr.Dropdown(initial_choices, multiselect=True, label="فقط در این مقاله‌ها (اختیاری)")
            ex_btn = gr.Button("استخراج", variant="primary")
            ex_summary = gr.Markdown(elem_classes="rtl")
            ex_table = gr.Dataframe(interactive=False, wrap=True, max_height=600)
            ex_file = gr.File(label="دانلود CSV")

        with gr.Tab("📈 طیف (HITRAN)"):
            gr.Markdown("طیف جذبی (پروفایل Voigt) از خطوط HITRAN با کتابخانه‌ی HAPI محاسبه می‌شود. اگر فایل CSV "
                        "استخراج خواص را بدهید، طیف دوم با جایگزینی مقدارهای مقاله رسم می‌شود تا اثر فیزیکی "
                        "اختلاف مقاله و HITRAN دیده شود. خطوط با شاخه و J (مثلاً R(50)) تطبیق داده می‌شوند.",
                        elem_classes="rtl")
            with gr.Row():
                sp_molecule = gr.Dropdown(list(MOLECULES), value="CO2", label="مولکول")
                sp_iso = gr.Number(1, precision=0, label="ایزوتوپولوگ (1 = فراوان‌ترین)")
                sp_min = gr.Number(5007.0, label="ابتدای بازه (cm⁻¹)")
                sp_max = gr.Number(5008.5, label="انتهای بازه (cm⁻¹)")
                sp_t = gr.Number(296, label="دما (K)")
                sp_p = gr.Number(0.04, label="فشار (atm)")
            sp_file = gr.File(label="فایل CSV استخراج خواص (اختیاری؛ بعد از استخراج خودکار پر می‌شود)",
                              file_types=[".csv"], type="filepath")
            sp_btn = gr.Button("رسم طیف", variant="primary")
            sp_plot = gr.Plot()
            sp_note = gr.Markdown(elem_classes="rtl")
            sp_table = gr.Dataframe(label="پارامترهای جایگزین‌شده", interactive=False)

        with gr.Tab("ℹ️ راهنما"):
            gr.Markdown(GUIDE, elem_classes="rtl")

        paper_outputs = [table, to_remove, ask_docs, pack_docs, ex_docs]
        add_btn.click(ingest_uploads, [corpus, files, arxiv_ids], [ingest_log, *paper_outputs])
        folder_btn.click(ingest_folder, [corpus], [ingest_log, *paper_outputs])
        remove_btn.click(remove_paper, [corpus, to_remove], [ingest_log, *paper_outputs])
        ask_btn.click(ask, [corpus, question, provider, language, mode, top_k, ask_docs, compare],
                      [answer, baseline, sources])
        pack_btn.click(make_pack, [corpus, pack_question, pack_language, pack_mode, pack_top_k, pack_docs],
                       [pack_text, pack_file])
        ex_btn.click(run_extract, [corpus, properties, provider, exhaustive, ex_mode, ex_top_k, ex_docs],
                     [ex_summary, ex_table, ex_file]).then(lambda f: f, ex_file, sp_file)
        sp_btn.click(run_spectrum, [sp_molecule, sp_iso, sp_min, sp_max, sp_t, sp_p, sp_file],
                     [sp_plot, sp_note, sp_table])

        def switch_corpus(name):
            return (*_refresh_paper_lists(name), ", ".join(_ws(name).default_properties()))

        corpus.change(switch_corpus, corpus, [*paper_outputs, properties])
    return demo


def launch(port: int = 7860, share: bool = False, **kwargs) -> None:
    # Re-running the launch (e.g. the Colab cell) first stops the previous app,
    # which would otherwise still hold the port.
    gr.close_all()
    results = _results_root()
    results.mkdir(parents=True, exist_ok=True)
    # Gradio only serves files from the working and temp folders unless told otherwise;
    # in Colab the results live on Google Drive.
    build_app().queue().launch(server_port=port, share=share, theme=gr.themes.Soft(), css=CSS,
                               allowed_paths=[str(results)], **kwargs)
