"""Writes the Colab notebooks (run: python notebooks/build_notebooks.py).

The notebooks are generated so the main notebook and the four identical
worker notebooks stay in sync. Colab gives every notebook *file* its own
session, so parallel workers need separate files.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
BRANCH = "claude/festive-bardeen-nnw123"
VERSION = 13
WORKERS = 4


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip().splitlines(keepends=True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {"cellView": "form"}, "execution_count": None, "outputs": [],
            "source": text.strip().splitlines(keepends=True)}


def notebook(cells: list[dict], gpu: bool = True) -> dict:
    meta = {"colab": {"provenance": []}, "kernelspec": {"name": "python3", "display_name": "Python 3"},
            "language_info": {"name": "python"}}
    if gpu:
        meta |= {"accelerator": "GPU"}
        meta["colab"]["gpuType"] = "T4"
    return {"nbformat": 4, "nbformat_minor": 0, "metadata": meta, "cells": cells}


ENV = """
import os
# Keep Colab's preinstalled JAX/TensorFlow from reserving the GPU memory
# (otherwise the embedding model and Ollama run out of memory).
os.environ.update({'JAX_PLATFORMS': 'cpu', 'XLA_PYTHON_CLIENT_PREALLOCATE': 'false',
                   'TF_FORCE_GPU_ALLOW_GROWTH': 'true', 'USE_TF': '0', 'USE_FLAX': '0',
                   'TF_CPP_MIN_LOG_LEVEL': '3'})
from google.colab import drive
drive.mount('/content/drive')
"""

INSTALL = f"""
BRANCH = "{BRANCH}"  #@param {{type:"string"}}
# Leave the project folder before deleting it (re-running this cell used to fail
# with "Unable to read current working directory").
%cd /content
!rm -rf /content/RAG && git clone -q --depth 1 -b {{BRANCH}} https://github.com/aminsadidi/RAG.git /content/RAG
%cd /content/RAG
!pip install -q -e . 2>&1 | grep -iE "^error" || true
# An editable install is only seen by Python after a restart; adding the source
# folder to the path makes it importable in this session right away.
import sys
if '/content/RAG/src' not in sys.path:
    sys.path.insert(0, '/content/RAG/src')
"""

QDRANT_KEYS = """
# Keys: matrag_data/qdrant.env (Qdrant) and matrag_data/cloudflare.env (the site's PDFs) on Drive,
# as KEY=value lines; the Qdrant ones can also come from Colab Secrets.
import os
KEYS_FILE = f'{WORK}/qdrant.env'
for keys_file in (KEYS_FILE, f'{WORK}/cloudflare.env'):
    if os.path.exists(keys_file):
        for line in open(keys_file, encoding='utf-8'):
            key, sep, value = line.strip().partition('=')
            if sep and not key.startswith('#'):
                os.environ[key.strip()] = value.strip().strip('"')
if not os.environ.get('QDRANT_API_KEY'):
    from google.colab import userdata
    for key in ('QDRANT_URL', 'QDRANT_API_KEY'):
        try:
            os.environ[key] = userdata.get(key)
        except Exception:
            pass
assert os.environ.get('QDRANT_URL') and os.environ.get('QDRANT_API_KEY'), f'Qdrant key not found ({KEYS_FILE})'
"""


MAIN = [
    md(f"""
# سیستم RAG برای استخراج خواص فیزیکی مواد از مقالات

**نسخه‌ی نوت‌بوک: {VERSION}** (اگر عدد کمتری می‌بینید، نوت‌بوک را دوباره از لینک باز کنید)

**قبل از شروع:** منوی *Runtime → Change runtime type* → **T4 GPU**

سلول‌ها را **به ترتیب** اجرا کنید (دکمه‌ی ▶):

| سلول | کار | چند بار؟ |
|---|---|---|
| ۱ تا ۳ | آماده‌سازی | هر بار |
| ۴ | مرتب کردن PDFهای پوشه‌ی `RAG-Optics` در پوشه‌ی هر بلور و گزارش وضعیت | هر بار (سریع؛ فایلی پاک نمی‌شود) |
| ۵ | پردازش مقاله‌ها و ساخت پایگاه داده | بار اول طولانی (چند ساعت)؛ بعد فقط مقاله‌های تازه |
| ۶ و ۷ | مدل زبانی و باز کردن برنامه | هر بار |

**سریع‌تر کردن سلول ۵:** نوت‌بوک‌های «کارگر» (`colab_worker_1` تا `colab_worker_{WORKERS}`) را هم‌زمان در
تب‌های دیگر اجرا کنید؛ هر کدام بخشی از PDFها را تبدیل می‌کند و نتیجه را در همان پوشه‌ی Drive می‌گذارد.
سلول ۵ فقط کارهای باقی‌مانده را انجام می‌دهد. نیازی نیست فایلی برای من بفرستید.

همه‌چیز در **Google Drive** ذخیره می‌شود و با بستن کولب پاک نمی‌شود؛ اگر وسط کار قطع شد، دوباره اجرا کنید
تا از همان‌جا ادامه دهد.
"""),
    code("""
#@title ۱. بررسی کارت گرافیک
!nvidia-smi --query-gpu=name,memory.total --format=csv || echo "⚠️ کارت گرافیک فعال نیست: Runtime → Change runtime type → T4 GPU"
"""),
    code("#@title ۲. اتصال به Google Drive\n" + ENV + """
WORK = '/content/drive/MyDrive/matrag_data'
os.makedirs(f'{WORK}/logs', exist_ok=True)
os.environ['MATRAG_DATA_DIR'] = f'{WORK}/data'
# The vector database runs on Colab's local disk (SQLite is unreliable on Drive);
# the app copies it back to Drive after every change.
os.environ['MATRAG_STORAGE_DIR'] = '/content/storage'
os.environ['MATRAG_STORAGE_BACKUP_DIR'] = f'{WORK}/storage'
# refractiveindex.info database (downloaded in cell 3), shared by all corpora. It lives on
# Colab's local disk: reading its thousands of small files from Drive takes many minutes.
os.environ['MATRAG_REFERENCE_DIR'] = '/content/refractiveindex/database'
!mkdir -p "{WORK}/storage" /content/storage && cp -rT "{WORK}/storage" /content/storage
print('✅ Data folder:', WORK)
"""),
    code("#@title ۳. نصب برنامه از GitHub\n" + INSTALL + """
# refractiveindex.info database (CC0), used to check formulas extracted from optical papers;
# downloaded to the local disk in each session (a few seconds).
if not os.path.isdir('/content/refractiveindex/database'):
    !git clone -q --depth 1 https://github.com/polyanskiy/refractiveindex.info-database.git /content/refractiveindex && echo "refractiveindex.info database downloaded"
!git log --oneline -1
!matrag --help > /dev/null && echo '✅ Installed (red "dependency conflict" warnings from pip can be ignored)' || echo '❌ Installation failed: run this cell again and send the output'
"""),
    code("""
#@title ۴. پوشه‌ی مقاله‌ها: مرتب‌سازی و وضعیت
#@markdown مسیر پوشه‌ی مقاله‌ها در Drive:
COLLECTION = "/content/drive/MyDrive/RAG-Optics"  #@param {type:"string"}
#@markdown **ORGANIZE**: هر PDF (مثلاً فایل‌های `05_Downloaded_PDFs`) به پوشه‌ی دسته و بلور خودش در
#@markdown `01_Papers_by_Category` منتقل می‌شود. هیچ فایلی پاک نمی‌شود؛ PDFهایی که در فهرست اصلی نیستند به
#@markdown `99_Not_in_master_index` و نسخه‌های تکراری به `98_Duplicate_copies` می‌روند.
#@markdown گزارش کامل: `02_Master_Index/pdf_inventory.csv`
ORGANIZE = True  #@param {type:"boolean"}
os.environ['MATRAG_CORPUS'] = 'rag-optics'
print('1/3 Linking the folder...')
!matrag --corpus rag-optics link "{COLLECTION}" 2>&1 | grep -vE "Warning"
if ORGANIZE:
    print('2/3 Sorting the PDFs (a few minutes the first time)...')
    !matrag --corpus rag-optics organize --move 2>&1 | grep -vE "Warning"
print('3/3 Status:')
!matrag --corpus rag-optics status 2>&1 | grep -vE "Warning"
"""),
    code("""
#@title ۵. پردازش مقاله‌ها و ساخت پایگاه داده
#@markdown بار اول برای حدود ۲۰۰۰ PDF چند ساعت طول می‌کشد (تبدیل PDF کُندترین مرحله است). اگر
#@markdown نوت‌بوک‌های کارگر را هم‌زمان اجرا کرده‌اید، این سلول را **بعد از تمام شدن آن‌ها** اجرا کنید
#@markdown (یا همین حالا؛ فقط ممکن است چند مقاله دو بار تبدیل شود). مقاله‌های بدون PDF با چکیده‌شان وارد
#@markdown می‌شوند. اگر کولب قطع شد، دوباره اجرا کنید: کار از همان‌جا ادامه پیدا می‌کند.
%cd {WORK}
!matrag --corpus rag-optics ingest --prune 2>&1 | grep -vE "Warning|Loading|it/s\\]" | tee -a "{WORK}/logs/ingest.log"
%cd /content/RAG
!matrag --corpus rag-optics status 2>&1 | grep -vE "Warning"
"""),
    code("""
#@title ۶. راه‌اندازی مدل زبانی
#@markdown **ollama**: مدل متن‌باز روی کارت گرافیک کولب (رایگان، بدون سهمیه). بار اول دانلود مدل چند دقیقه طول می‌کشد.
#@markdown **gemini**: کلید API را در بخش Secrets کولب (آیکون 🔑 سمت چپ) با نام `MATRAG_GOOGLE_API_KEY` ذخیره کنید.
LLM_PROVIDER = "ollama"  #@param ["ollama", "gemini"]
#@markdown qwen3:8b کنار برنامه در حافظه‌ی کارت گرافیک T4 جا می‌شود؛ 14b ممکن است جا نشود و خیلی کُند شود.
OLLAMA_MODEL = "qwen3:8b"  #@param ["qwen3:8b", "qwen3:14b", "qwen3:4b-instruct-2507-q4_K_M"]
#@markdown **KEEP_MODEL_ON_DRIVE**: مدل یک بار در Drive ذخیره شود (حدود ۵ گیگ برای 8b) تا دفعه‌های بعد دانلود نشود.
KEEP_MODEL_ON_DRIVE = False  #@param {type:"boolean"}
import os, subprocess, time
os.environ['MATRAG_LLM_PROVIDER'] = LLM_PROVIDER
os.environ['MATRAG_OLLAMA_MODEL'] = OLLAMA_MODEL
os.environ['MATRAG_OLLAMA_THINKING'] = 'false'  # faster answers from Qwen3

try:  # Gemini is optional; with a key both models can be chosen in the app
    from google.colab import userdata
    os.environ['MATRAG_GOOGLE_API_KEY'] = userdata.get('MATRAG_GOOGLE_API_KEY')
    print('✅ Gemini key loaded')
except Exception:
    print('ℹ️ No Gemini key in Colab Secrets (only needed for gemini)')

if LLM_PROVIDER == "ollama":
    os.environ['OLLAMA_MODELS'] = '/content/ollama_models'
    DRIVE_MODELS = f'{WORK}/ollama_models'
    if KEEP_MODEL_ON_DRIVE and os.path.isdir(DRIVE_MODELS):
        print('Copying saved model from Drive...')
        !mkdir -p /content/ollama_models && cp -rT "{DRIVE_MODELS}" /content/ollama_models
    if subprocess.run('which ollama', shell=True, capture_output=True).returncode != 0:
        !apt-get install -y -qq zstd > /dev/null
        !curl -fsSL https://ollama.com/install.sh | sh > /dev/null
    subprocess.Popen('ollama serve > /content/ollama.log 2>&1', shell=True)
    time.sleep(5)
    !ollama pull {OLLAMA_MODEL} 2>&1 | tail -1
    if KEEP_MODEL_ON_DRIVE:
        !mkdir -p "{DRIVE_MODELS}" && cp -rTu /content/ollama_models "{DRIVE_MODELS}" && echo "Model saved to Drive."
print('✅ Language model ready:', LLM_PROVIDER)
"""),
    code("""
#@title ۷. اجرای برنامه 🚀
#@markdown مجموعه‌ی پیش‌فرض (در خود برنامه هم قابل تغییر است). `rag-optics` همان پوشه‌ی مقاله‌های Drive است.
CORPUS = "rag-optics"  #@param ["rag-optics", "optical", "hitran"] {allow-input: true}
#@markdown **PUBLIC_LINK** (پیشنهادی): برنامه با یک لینک موقت https://….gradio.live باز می‌شود — روی لینکی که
#@markdown پایین این سلول چاپ می‌شود بزنید. لینک خصوصی نیست (هر کس آن را داشته باشد باز می‌کند) و با بسته شدن
#@markdown کولب از کار می‌افتد. خاموش: نمایش داخل کولب (ممکن است ظاهر برنامه درست بارگذاری نشود).
PUBLIC_LINK = True  #@param {type:"boolean"}
import os, sys
os.environ['MATRAG_CORPUS'] = CORPUS
if '/content/RAG/src' not in sys.path:  # see cell 3
    sys.path.insert(0, '/content/RAG/src')
# Forget code imported by an earlier run, so the version just installed in cell 3 is used.
for name in [m for m in sys.modules if m == 'matrag' or m.startswith('matrag.')]:
    del sys.modules[name]
from matrag.webapp import launch
PORT = launch(port=7860, share=PUBLIC_LINK, inline=False, prevent_thread_lock=True, quiet=not PUBLIC_LINK)
if not PUBLIC_LINK:
    from google.colab import output
    output.serve_kernel_port_as_window(PORT, anchor_text='👉 باز کردن برنامه در یک تب جدید (پیشنهاد می‌شود)')
    output.serve_kernel_port_as_iframe(PORT, height=950)
"""),
    md("""
---
### (اختیاری) ارزیابی

این سلول‌ها جدول‌های نتایج مقاله را می‌سازند. فایل‌ها در `matrag_data/results/eval` ذخیره می‌شوند.
سؤال‌های مرجع در `matrag_data/data/<corpus>/gold/questions.csv` قرار دارند.
"""),
    code("""
#@title ۸. ارزیابی بازیابی (بدون مصرف مدل زبانی)
#@markdown برای `rag-optics` سؤال‌ها خودکار از refractiveindex.info ساخته می‌شوند: «فرمول پاشندگی ماده‌ی X»
#@markdown باید یکی از مقاله‌هایی را پیدا کند که پایگاه برای آن ماده به آن ارجاع داده است.
CORPUS = globals().get('CORPUS', 'rag-optics')  # set by cell 7; rag-optics if it was skipped
%cd {WORK}
if CORPUS == 'rag-optics':
    !matrag --corpus rag-optics evaluate build-gold 2>&1 | grep -vE "Warning|Loading"
else:
    !mkdir -p "{WORK}/data/{CORPUS}/gold" && cp -n /content/RAG/data/{CORPUS}/gold/*.csv "{WORK}/data/{CORPUS}/gold/" 2>/dev/null; true
!matrag --corpus {CORPUS} evaluate retrieval 2>&1 | grep -vE "Warning|Loading" | tee -a "{WORK}/logs/eval.log"
%cd /content/RAG
"""),
    code("""
#@title ۹. ارزیابی پاسخ‌ها: RAG در برابر مدل بدون منبع (برای hitran و optical)
#@markdown سؤال‌های خودکارِ `rag-optics` جواب مرجع ندارند و این‌جا رد می‌شوند؛ ارزیابی اصلی آن سلول ۱۰ است.
LIMIT = 16  #@param {type:"integer"}
CORPUS = globals().get('CORPUS', 'rag-optics')  # set by cell 7
%cd {WORK}
!matrag --corpus {CORPUS} evaluate answers --limit {LIMIT} 2>&1 | grep -vE "Warning|Loading" | tee -a "{WORK}/logs/eval.log"
%cd /content/RAG
"""),
    code("""
#@title ۱۰. ارزیابی اصلی: استخراج فرمول ← مقایسه با refractiveindex.info
#@markdown برای هر مقاله‌ای که refractiveindex.info فرمولش را از آن برداشته: فرمول پاشندگی از متن مقاله استخراج و
#@markdown ضریب شکست حاصل با پایگاه مقایسه می‌شود (بیشینه‌ی |Δn|). به مدل زبانی (سلول ۶) نیاز دارد و برای هر مقاله
#@markdown چند دقیقه طول می‌کشد؛ هر بار **LIMIT** مقاله‌ی تازه پردازش می‌شود و اجرای بعدی از همان‌جا ادامه می‌دهد.
LIMIT = 20  #@param {type:"integer"}
%cd {WORK}
!matrag --corpus rag-optics evaluate formulas --limit {LIMIT} 2>&1 | grep -vE "Warning|Loading|it/s\\]" | tee -a "{WORK}/logs/eval.log"
%cd /content/RAG
"""),
    md("""
---
### انتقال به سایت

سایت (Cloudflare) از روی یک کپی از پایگاه داده در Qdrant Cloud جست‌وجو می‌کند. بعد از سلول ۵ (و هر بار که
مقاله‌ی تازه اضافه شد) این سلول را اجرا کنید. به کارت گرافیک و مدل زبانی نیاز ندارد.
"""),
    code("""
#@title ۱۱. بارگذاری پایگاه داده در سایت (Qdrant Cloud)
#@markdown کلید Qdrant خودکار از فایل `matrag_data/qdrant.env` در Drive خوانده می‌شود (یا از Secrets کولب).
#@markdown بردارها دوباره ساخته نمی‌شوند؛ همان بردارهای پایگاه (و ارزیابی‌ها) فرستاده می‌شوند. اگر قطع شد دوباره
#@markdown اجرا کنید: بخش‌های فرستاده‌شده رد می‌شوند. **RECREATE** مجموعه را پاک و از نو می‌سازد.
RECREATE = False  #@param {type:"boolean"}
#@markdown **EVALUATE**: بعد از بارگذاری، ارزیابی سلول ۸ روی جست‌وجوی سایت هم اجرا شود (برای مقایسه).
EVALUATE = True  #@param {type:"boolean"}
""" + QDRANT_KEYS + """
%cd {WORK}
!matrag --corpus rag-optics export-qdrant {'--recreate' if RECREATE else ''} 2>&1 | grep -vE "Warning|Loading"
if EVALUATE and os.path.exists(f'{WORK}/data/rag-optics/gold/questions.csv'):
    !matrag --corpus rag-optics evaluate retrieval --backend qdrant 2>&1 | grep -vE "Warning|Loading" | tee -a "{WORK}/logs/eval.log"
%cd /content/RAG
"""),
]


def site() -> dict:
    """One click, CPU only: upload the database made by colab_demo to the website's Qdrant collection."""
    return notebook([
        md(f"""
# بارگذاری پایگاه داده در سایت (نسخه‌ی {VERSION})

فقط یک سلول: روی ▶️ بزنید و اجازه‌ی دسترسی به Google Drive را بدهید. کارت گرافیک لازم نیست.
۱) PDF مقاله‌ها برای نمایش صفحه روی سایت (پشت رمز) بارگذاری می‌شوند؛ ۲) پایگاه داده‌ای که نوت‌بوک اصلی
(سلول ۵) در `matrag_data` ساخته، با همان بردارها در Qdrant بارگذاری می‌شود؛ ۳) جست‌وجوی سایت با همان سؤال‌های
ارزیابی سنجیده می‌شود. حدود یک ساعت. اگر قطع شد دوباره اجرا کنید؛ از همان‌جا ادامه می‌دهد.
"""),
        code("#@title ▶️ بارگذاری در سایت\n" + ENV + """
WORK = '/content/drive/MyDrive/matrag_data'
os.environ['MATRAG_DATA_DIR'] = f'{WORK}/data'
os.environ['MATRAG_STORAGE_DIR'] = '/content/storage'
os.environ['MATRAG_CORPUS'] = 'rag-optics'
print('Copying the database from Drive...')
!mkdir -p /content/storage && cp -rT "{WORK}/storage" /content/storage
""" + INSTALL + QDRANT_KEYS + """
%cd {WORK}
if os.environ.get('CLOUDFLARE_API_TOKEN'):
    # 1. The PDFs, for the page view: copied from Drive, then deployed to the site's private PDF Worker
    print('Copying the PDFs from Drive (10-20 minutes)...')
    !matrag --corpus rag-optics export-pdfs /content/RAG/web-pdfs/pdfs 2>&1 | grep -vE "Warning|Loading"
    if not os.path.exists('/content/node/bin/node'):  # wrangler needs Node.js 20 or newer
        !curl -fsSL https://nodejs.org/dist/v22.12.0/node-v22.12.0-linux-x64.tar.xz | tar -xJ -C /content && mv /content/node-v22.12.0-linux-x64 /content/node
    os.environ['PATH'] = '/content/node/bin:' + os.environ['PATH']
    print('Uploading the PDFs to the site...')
    !cd /content/RAG/web-pdfs && npx --yes wrangler@4 deploy 2>&1 | grep -vE "telemetry|^$" | tail -4
else:
    print('ℹ️ No matrag_data/cloudflare.env: PDFs not uploaded (the page view needs them)')
# 2. The chunks and their vectors, for the search
!matrag --corpus rag-optics export-qdrant 2>&1 | grep -vE "Warning|Loading"
if os.path.exists(f'{WORK}/data/rag-optics/gold/questions.csv'):
    !matrag --corpus rag-optics evaluate retrieval --backend qdrant 2>&1 | grep -vE "Warning|Loading" | tee -a "{WORK}/logs/eval.log"
%cd /content/RAG
print('✅ Done: https://matrag.ethanjamescarter1995.workers.dev')
"""),
    ], gpu=False)


def gpu_update() -> dict:
    """GPU run: OCR / equation decoding for the listed papers, wrong PDFs dropped, then the site updated."""
    return notebook([
        md(f"""
# به‌روزرسانی با GPU: OCR، معادله‌ها و سایت (نسخه‌ی {VERSION})

**سلول ۱** (حدود ۱ تا ۲ ساعت؛ Runtime → Change runtime type → T4 GPU):
- متن OCR‌شده‌ی ۴۵ مقاله‌ی اسکن‌شده (همان که روی سایت است) وارد پایگاه کولب می‌شود؛ ۹ مقاله‌ای که PDFشان هیچ متنی ندارد OCR می‌شوند؛
- برای ۴۶ مقاله‌ی ارزیابی فرمول، معادله‌ها با مدل CodeFormula از تصویر صفحه به LaTeX خوانده می‌شوند (GPU)؛
- ۶ مقاله که PDFشان مقاله‌ی دیگری است فقط با چکیده نمایه می‌شوند؛
- پایگاه در Drive ذخیره، PDFها و بخش‌ها در سایت به‌روز و جست‌وجوی سایت دوباره ارزیابی می‌شود.

فهرست مقاله‌ها در `data/rag-optics/*.txt` مخزن است. اگر قطع شد دوباره اجرا کنید؛ از همان‌جا ادامه می‌دهد.

**سلول ۲** (اختیاری، حدود ۱ تا ۲ ساعت): ارزیابی دوباره‌ی استخراج فرمول با مدل qwen3:8b روی همین متن‌های تازه.
"""),
        code("#@title ▶️ ۱. OCR، معادله‌ها، پایگاه و سایت\n" + ENV + """
WORK = '/content/drive/MyDrive/matrag_data'
os.environ['MATRAG_DATA_DIR'] = f'{WORK}/data'
os.environ['MATRAG_STORAGE_DIR'] = '/content/storage'
os.environ['MATRAG_STORAGE_BACKUP_DIR'] = f'{WORK}/storage'
os.environ['MATRAG_CORPUS'] = 'rag-optics'
os.environ['MATRAG_CONVERT_TIMEOUT_S'] = '3600'  # equation decoding is slow on long papers
!nvidia-smi --query-gpu=name --format=csv,noheader || echo "⚠️ No GPU: Runtime → Change runtime type → T4 GPU"
print('Copying the database from Drive...')
!mkdir -p /content/storage && cp -rT "{WORK}/storage" /content/storage
""" + INSTALL + """
!pip install -q "rapidocr>=3" onnxruntime 2>&1 | grep -iE "^error" || true
!cp /content/RAG/data/rag-optics/ocr_papers.txt /content/RAG/data/rag-optics/formula_papers.txt /content/RAG/data/rag-optics/pdf_mismatch.txt "{WORK}/data/rag-optics/"
""" + QDRANT_KEYS + """
# The OCR conversions made for the site (same text on both sides), kept in Qdrant.
import base64, pathlib
from matrag import qdrant_store
root = pathlib.Path(open(f'{WORK}/data/rag-optics/corpus_root.txt').read().strip())
qc, offset, got = qdrant_store.client(), None, 0
while True:
    points, offset = qc.scroll('matrag_files', limit=16, offset=offset, with_payload=True)
    for p in points:
        dst = root / '_RAG_processed' / p.payload['path']
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(base64.b64decode(p.payload['data'])); got += 1
    if offset is None:
        break
print(f'{got} OCR conversions copied')
%cd {WORK}
!matrag --corpus rag-optics ingest 2>&1 | grep -vE "Warning|Loading|it/s\\]" | tee -a "{WORK}/logs/ingest.log"
if os.environ.get('CLOUDFLARE_API_TOKEN'):
    !matrag --corpus rag-optics export-pdfs /content/RAG/web-pdfs/pdfs 2>&1 | grep -vE "Warning|Loading"
    if not os.path.exists('/content/node/bin/node'):
        !curl -fsSL https://nodejs.org/dist/v22.12.0/node-v22.12.0-linux-x64.tar.xz | tar -xJ -C /content && mv /content/node-v22.12.0-linux-x64 /content/node
    os.environ['PATH'] = '/content/node/bin:' + os.environ['PATH']
    !cd /content/RAG/web-pdfs && npx --yes wrangler@4 deploy 2>&1 | grep -vE "telemetry|^$" | tail -4
!matrag --corpus rag-optics export-qdrant 2>&1 | grep -vE "Warning|Loading"
if os.path.exists(f'{WORK}/data/rag-optics/gold/questions.csv'):
    !matrag --corpus rag-optics evaluate retrieval --backend qdrant 2>&1 | grep -vE "Warning|Loading" | tee -a "{WORK}/logs/eval.log"
%cd /content/RAG
print('✅ Done: https://matrag.ethanjamescarter1995.workers.dev')
"""),
        code("""
#@title ۲. (اختیاری) ارزیابی دوباره‌ی استخراج فرمول با qwen3:8b
#@markdown نتیجه جدا از ارزیابی قبلی در `results/eval/rag-optics_formula_benchmark_ocr_formulas.jsonl` ذخیره می‌شود.
LIMIT = 80  #@param {type:"integer"}
import subprocess, time
if not os.path.isdir('/content/refractiveindex'):
    !git clone -q --depth 1 https://github.com/polyanskiy/refractiveindex.info-database.git /content/refractiveindex
os.environ['MATRAG_REFERENCE_DIR'] = '/content/refractiveindex/database'
os.environ.update({'MATRAG_LLM_PROVIDER': 'ollama', 'MATRAG_OLLAMA_MODEL': 'qwen3:8b', 'MATRAG_OLLAMA_THINKING': 'false',
                   'OLLAMA_MODELS': '/content/ollama_models'})
if subprocess.run('which ollama', shell=True, capture_output=True).returncode != 0:
    !apt-get install -y -qq zstd > /dev/null
    !curl -fsSL https://ollama.com/install.sh | sh > /dev/null
subprocess.Popen('ollama serve > /content/ollama.log 2>&1', shell=True)
time.sleep(5)
!ollama pull qwen3:8b 2>&1 | tail -1
%cd {WORK}
!matrag --corpus rag-optics evaluate formulas --run ocr_formulas --limit {LIMIT} 2>&1 | grep -vE "Warning|Loading|it/s\\]" | tee -a "{WORK}/logs/eval.log"
%cd /content/RAG
"""),
    ], gpu=True)


NEW_PAPERS = """
# File in the downloads folder -> DOI, category, material; rows only for papers the master index lacks.
PAPERS = {
    'pack2003.pdf': ('10.1364/josab.20.002109', '03_Niobates_Tantalates_Iodates', 'KNbO3', {
        'title': 'Measurement of the χ^(2) tensor of the potassium niobate crystal',
        'authors': 'Michael V. Pack; Darrell J. Armstrong; Arlee V. Smith', 'year': 2003,
        'journal': 'Journal of the Optical Society of America B'}),
    'pack2004.pdf': ('10.1364/ao.43.003319', '02_Phosphates_Arsenates_KDP', 'RTP_RbTiOPO4', None),
    'pack2005.pdf': ('10.1364/josab.22.000417', '01_Borates', 'YCOB_GdCOB_ReCOB', {
        'title': 'Measurement of the χ^(2) tensors of GdCa4O(BO3)3 and YCa4O(BO3)3 crystals',
        'authors': 'Michael V. Pack; Darrell J. Armstrong; Arlee V. Smith; Gerard Aka; Bernard Ferrand; Denis Pelenc',
        'year': 2005, 'journal': 'Journal of the Optical Society of America B'}),
    'hellwig1998.pdf': ('10.1016/s0038-1098(98)00538-9', '01_Borates', 'BiBO_BiB3O6', None),
    'jerphagnon1970.pdf': ('10.1103/physrevb.1.1739', '02_Phosphates_Arsenates_KDP', 'ADP_NH4H2PO4', None),
    'li2016.pdf': ('10.1016/j.optmat.2016.10.023', '01_Borates', 'LCB_La2CaB10O19', None),
    # 2026-10-07: sources of the NLO data (docs/nlo_sources.md) and SPDC theory
    'ljunggren2005.pdf': ('10.1103/physreva.72.062301', '08_Theory_Dispersion_Models', 'Phase_matching_theory_birefringence', {'title': 'Optimal focusing for maximal collection of entangled narrow-band photon pairs into single-mode fibers', 'authors': 'Daniel Ljunggren; Maria Tengner', 'year': 2005, 'journal': 'Physical Review A'}),
    'tzankov2005.pdf': ('10.1364/ao.44.006971', '08_Theory_Dispersion_Models', 'Nonlinear_coefficients_Miller_rule', {'title': 'Effective second-order nonlinearity in acentric optical crystals with low symmetry', 'authors': 'Pancho Tzankov; Valentin Petrov', 'year': 2005, 'journal': 'Applied Optics'}),
    'kato1994.pdf': ('10.1109/3.362711', '01_Borates', 'LBO_LiB3O5', {'title': 'Temperature-tuned 90° phase-matching properties of LiB3O5', 'authors': 'K. Kato', 'year': 1994, 'journal': 'IEEE Journal of Quantum Electronics'}),
    'fedrizzi2007.pdf': ('10.1364/oe.15.015377', '02_Phosphates_Arsenates_KDP', 'KTP_KTiOPO4', {'title': 'A wavelength-tunable fiber-coupled source of narrowband entangled photons', 'authors': 'Alessandro Fedrizzi; Thomas Herbst; Andreas Poppe; Thomas Jennewein; Anton Zeilinger', 'year': 2007, 'journal': 'Optics Express'}),
    'gayer2010.pdf': ('10.1007/s00340-010-4203-7', '03_Niobates_Tantalates_Iodates', 'LiNbO3_LN_PPLN', {'title': 'Erratum to: Temperature and wavelength dependent refractive index equations for MgO-doped congruent and stoichiometric LiNbO3', 'authors': 'O. Gayer; Z. Sacks; E. Galun; A. Arie', 'year': 2010, 'journal': 'Applied Physics B'}),
    'dolev2009.pdf': ('10.1007/s00340-009-3502-3', '03_Niobates_Tantalates_Iodates', 'LiTaO3_LT_PPLT', {'title': 'Linear and nonlinear optical properties of MgO:LiTaO3', 'authors': 'I. Dolev; A. Ganany-Padowicz; O. Gayer; A. Arie; J. Mangin; G. Gadret', 'year': 2009, 'journal': 'Applied Physics B'}),
    'petrov2015.pdf': ('10.1016/j.pquantelec.2015.04.001', '08_Theory_Dispersion_Models', 'Reviews_NLO_crystals_databases', {'title': 'Frequency down-conversion of solid-state laser sources to the mid-infrared spectral range using non-oxide nonlinear crystals', 'authors': 'Valentin Petrov', 'year': 2015, 'journal': 'Progress in Quantum Electronics'}),
    'petrov2012.pdf': ('10.1016/j.optmat.2011.03.042', '08_Theory_Dispersion_Models', 'Reviews_NLO_crystals_databases', {'title': 'Parametric down-conversion devices: The coverage of the mid-infrared spectral range by solid-state laser sources', 'authors': 'Valentin Petrov', 'year': 2012, 'journal': 'Optical Materials'}),
    'grice1997.pdf': ('10.1103/physreva.56.1627', '08_Theory_Dispersion_Models', 'Phase_matching_theory_birefringence', {'title': 'Spectral information and distinguishability in type-II down-conversion with a broadband pump', 'authors': 'W. P. Grice; I. A. Walmsley', 'year': 1997, 'journal': 'Physical Review A'}),
    'zhai2013.pdf': ('10.1016/j.optmat.2013.09.017', '01_Borates', 'KBBF_KBe2BO3F2', {'title': 'Measurement of thermal refractive index coefficients of nonlinear optical crystal RbBe2BO3F2', 'authors': 'Naixia Zhai; Lirong Wang; Lijuan Liu; Xiaoyang Wang; Yong Zhu; Chuangtian Chen', 'year': 2013, 'journal': 'Optical Materials'}),
    'kato2018.pdf': ('10.1088/1555-6611/aac9df', '01_Borates', 'LBO_LiB3O5', {'title': 'New thermo-optic dispersion formula for LiB3O5', 'authors': 'K Kato; S G Grechin; N Umemura', 'year': 2018, 'journal': 'Laser Physics'}),
    'komatsu1997.pdf': ('10.1063/1.119210', '01_Borates', 'SBBO_KABO_other_borates', {'title': 'Growth and ultraviolet application of Li2B4O7 crystals: Generation of the fourth and fifth harmonics of Nd:Y3Al5O12 lasers', 'authors': 'R. Komatsu; T. Sugawara; K. Sassa; N. Sarukura; Z. Liu; S. Izumida; Y. Segawa; S. Uda; T. Fukuda; K. Yamanouchi', 'year': 1997, 'journal': 'Applied Physics Letters'}),
    'bennink2010.pdf': ('10.1103/physreva.81.053805', '08_Theory_Dispersion_Models', 'Phase_matching_theory_birefringence', {'title': 'Optimal collinear Gaussian beams for spontaneous parametric down-conversion', 'authors': 'Ryan S. Bennink', 'year': 2010, 'journal': 'Physical Review A'}),
    'hong1985.pdf': ('10.1103/physreva.31.2409', '08_Theory_Dispersion_Models', 'Phase_matching_theory_birefringence', {'title': 'Theory of parametric frequency down conversion of light', 'authors': 'C. K. Hong; L. Mandel', 'year': 1985, 'journal': 'Physical Review A'}),
    'sugawara1998.pdf': ('10.1016/s0038-1098(98)00190-2', '01_Borates', 'SBBO_KABO_other_borates', {'title': 'Linear and nonlinear optical properties of lithium tetraborate', 'authors': 'Tamotsu Sugawara; Ryuichi Komatsu; Satoshi Uda', 'year': 1998, 'journal': 'Solid State Communications'}),
    'ghosh1992.pdf': ('10.1117/12.637003', '02_Phosphates_Arsenates_KDP', 'KDP_DKDP_KH2PO4', {'title': 'Dispersion of thermo-optic coefficients and temperature-dependent nonlinear optical devices of some nonlinear crystals', 'authors': 'Gorachand Ghosh', 'year': 1992, 'journal': 'SPIE Proceedings'}),
    'evans2010.pdf': ('10.1103/physrevlett.105.253601', '02_Phosphates_Arsenates_KDP', 'KTP_KTiOPO4', {'title': 'Bright Source of Spectrally Uncorrelated Polarization-Entangled Photons with Nearly Single-Mode Emission', 'authors': 'P. G. Evans; R. S. Bennink; W. P. Grice; T. S. Humble; J. Schaake', 'year': 2010, 'journal': 'Physical Review Letters'}),
    'umemura2001.pdf': ('10.1364/assl.1999.pd15', '01_Borates', 'CLBO_CsLiB6O10', {'title': 'New data on the phase-matching properties of CsLiB6O10', 'authors': 'N. Umemura; K. Yoshida; T. Kamimura; Y. Mori; T. Sasaki; K. Kato', 'year': 2001, 'journal': 'Advanced Solid State Lasers'}),
    'mosley2008.pdf': ('10.1103/physrevlett.100.133601', '02_Phosphates_Arsenates_KDP', 'KDP_DKDP_KH2PO4', {'title': 'Heralded Generation of Ultrafast Single Photons in Pure Quantum States', 'authors': 'Peter J. Mosley; Jeff S. Lundeen; Brian J. Smith; Piotr Wasylczyk; Alfred B. U’Ren; Christine Silberhorn; Ian A. Walmsley', 'year': 2008, 'journal': 'Physical Review Letters'}),
    'petrov1998.pdf': ('10.1063/1.368904', '01_Borates', 'SBBO_KABO_other_borates', {'title': 'Vacuum ultraviolet application of Li2B4O7 crystals: Generation of 100 fs pulses down to 170 nm', 'authors': 'V. Petrov; F. Rotermund; F. Noack; R. Komatsu; T. Sugawara; S. Uda', 'year': 1998, 'journal': 'Journal of Applied Physics'}),
    'ghotbi2004.pdf': ('10.1364/opex.12.006002', '01_Borates', 'BiBO_BiB3O6', None),
    'law2000.pdf': ('10.1103/physrevlett.84.5304', '08_Theory_Dispersion_Models', 'Phase_matching_theory_birefringence', {'title': 'Continuous Frequency Entanglement: Effective Finite Hilbert Space and Entropy Control', 'authors': 'C. K. Law; I. A. Walmsley; J. H. Eberly', 'year': 2000, 'journal': 'Physical Review Letters'}),
    'miyata2009.pdf': ('10.1364/ol.34.000500', '01_Borates', 'BiBO_BiB3O6', {'title': 'Phase-matched pure χ^(3) third-harmonic generation in noncentrosymmetric BiB3O6', 'authors': 'Kentaro Miyata; Nobuhiro Umemura; Kiyoshi Kato', 'year': 2009, 'journal': 'Optics Letters'}),
    'shoji1999.pdf': ('10.1364/josab.16.000620', '01_Borates', 'BBO_beta-BaB2O4', {'title': 'Absolute measurement of second-order nonlinear-optical coefficients of β-BaB2O4 for visible to ultraviolet second-harmonic wavelengths', 'authors': 'Ichiro Shoji; Hirotaka Nakamura; Keisuke Ohdaira; Takashi Kondo; Ryoichi Ito; Tsutomu Okamoto; Koichi Tatsuki; Shigeo Kubota', 'year': 1999, 'journal': 'Journal of the Optical Society of America B'}),
    'hong1987.pdf': ('10.1103/physrevlett.59.2044', '08_Theory_Dispersion_Models', 'Phase_matching_theory_birefringence', {'title': 'Measurement of subpicosecond time intervals between two photons by interference', 'authors': 'C. K. Hong; Z. Y. Ou; L. Mandel', 'year': 1987, 'journal': 'Physical Review Letters'}),

}
import csv, json, pathlib, shutil
from matrag.catalog import PAPERS_DIR, doi_key, index_file, load_catalog, plan
root = pathlib.Path(open(f'{WORK}/data/rag-optics/corpus_root.txt').read().strip())
downloads = pathlib.Path(DOWNLOADS)
known = {e.key for e in load_catalog(root)}
print('1/4 Looking for the papers in the collection...')
have = {i.doc_id: i.pdf for i in plan(root).items if i.pdf is not None}  # a PDF under any file name
rows, placed = [], 0
for name, (doi, category, material, meta) in PAPERS.items():
    pdf = downloads / name
    target = root / PAPERS_DIR / category / material / (doi_key(doi) + '.pdf')
    if target.exists() or doi_key(doi) in have:
        print('already in the collection:', name, '->', (target if target.exists() else have[doi_key(doi)]).relative_to(root))
    elif not pdf.exists():
        print('⚠️ not found, skipped:', pdf)
        continue
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf, target)  # a copy: the downloads folder stays as it is
        placed += 1
        print('added:', name, '->', target.relative_to(root))
    if doi_key(doi) not in known and meta:
        rows.append({'category': category, 'material': material, 'doi': doi, 'doi_link': 'https://doi.org/' + doi,
                     'status': 'downloaded', **meta})
if rows:
    path = index_file(root)
    shutil.copy2(path, str(path) + '.before_new_papers')  # backup of the master index
    if path.suffix == '.csv':
        with path.open(encoding='utf-8-sig', newline='') as f:
            fields = csv.DictReader(f).fieldnames
        with path.open('a', encoding='utf-8', newline='') as f:
            csv.DictWriter(f, fieldnames=fields, extrasaction='ignore').writerows(rows)
    else:
        with path.open('a', encoding='utf-8') as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + '\\n' for r in rows)
    print(len(rows), 'rows added to', path.name)
print(f'✅ {placed} PDFs copied')
"""


def new_papers() -> dict:
    """CPU run: the papers downloaded by hand put in their category folders, indexed, and sent to the site."""
    return notebook([
        md(f"""
# افزودن مقاله‌های تازه به مجموعه و سایت (نسخه‌ی {VERSION})

PDFها باید در پوشه‌ی `proDownloads` در Drive باشند، با همان نام‌هایی که دانلود شده‌اند (مثل `petrov2015.pdf`،
`kato2018.pdf`، `pack2004.pdf`؛ فهرست کامل در کد). مقاله‌هایی که از قبل اضافه شده‌اند دوباره اضافه نمی‌شوند. فقط یک سلول دارد: روی ▶️ بزنید و اجازه‌ی دسترسی به
Google Drive را بدهید. کارت گرافیک لازم نیست. حدود ۳۰ تا ۶۰ دقیقه طول می‌کشد.

۱) هر PDF با نام DOI در پوشه‌ی دسته و بلور خودش در `RAG-Optics` **کپی** می‌شود (چیزی پاک یا جابه‌جا نمی‌شود)؛
مقاله‌هایی که در فهرست اصلی نیستند به آن اضافه می‌شوند (یک نسخه‌ی پشتیبان از فهرست کنار آن ذخیره می‌شود).
۲) مقاله‌ها پردازش و وارد پایگاه می‌شوند. ۳) PDFها و پایگاه روی سایت به‌روز می‌شوند.
اگر قطع شد دوباره اجرا کنید؛ کارهای انجام‌شده تکرار نمی‌شوند.
"""),
        code("#@title ▶️ افزودن مقاله‌ها\n"
             "DOWNLOADS = '/content/drive/MyDrive/proDownloads'  #@param {type:\"string\"}\n" + ENV + """
WORK = '/content/drive/MyDrive/matrag_data'
os.environ['MATRAG_DATA_DIR'] = f'{WORK}/data'
os.environ['MATRAG_STORAGE_DIR'] = '/content/storage'
os.environ['MATRAG_STORAGE_BACKUP_DIR'] = f'{WORK}/storage'
os.environ['MATRAG_CORPUS'] = 'rag-optics'
print('Copying the database from Drive...')
!mkdir -p /content/storage && cp -rT "{WORK}/storage" /content/storage
""" + INSTALL + NEW_PAPERS + QDRANT_KEYS + """
%cd {WORK}
# 2. Only the new papers are converted and embedded (the rest is already in the database)
print('2/4 Indexing the new papers (the rest are skipped as unchanged)...')
!matrag --corpus rag-optics ingest 2>&1 | grep -vE "Warning|Loading|it/s\\]" | tee -a "{WORK}/logs/ingest.log"
# 3. The site: PDFs for the page view, then the chunks for the search
if os.environ.get('CLOUDFLARE_API_TOKEN'):
    print('3/4 Copying all PDFs from Drive for the site: 10-20 minutes with no output, it is not stuck...')
    !matrag --corpus rag-optics export-pdfs /content/RAG/web-pdfs/pdfs 2>&1 | grep -vE "Warning|Loading"
    if not os.path.exists('/content/node/bin/node'):
        !curl -fsSL https://nodejs.org/dist/v22.12.0/node-v22.12.0-linux-x64.tar.xz | tar -xJ -C /content && mv /content/node-v22.12.0-linux-x64 /content/node
    os.environ['PATH'] = '/content/node/bin:' + os.environ['PATH']
    print('   Uploading the PDFs to the site (a few minutes)...')
    !cd /content/RAG/web-pdfs && npx --yes wrangler@4 deploy 2>&1 | grep -vE "telemetry|^$" | tail -4
else:
    print('ℹ️ No matrag_data/cloudflare.env: PDFs not uploaded (the page view needs them)')
print('4/4 Sending the new chunks to the site search (Qdrant)...')
!matrag --corpus rag-optics export-qdrant 2>&1 | grep -vE "Warning|Loading"
%cd /content/RAG
!matrag --corpus rag-optics status 2>&1 | grep -vE "Warning"
print('✅ Done: https://matrag.ethanjamescarter1995.workers.dev')
"""),
    ], gpu=False)


OLLAMA = """
import subprocess, time
os.environ.update({'MATRAG_LLM_PROVIDER': 'ollama', 'MATRAG_OLLAMA_MODEL': OLLAMA_MODEL,
                   'MATRAG_OLLAMA_THINKING': 'false', 'OLLAMA_MODELS': '/content/ollama_models',
                   # 4 requests at once on the T4 (the code sends 4 passages at a time); short context and replies
                   'OLLAMA_NUM_PARALLEL': '4', 'MATRAG_OLLAMA_CONTEXT_WINDOW': '4096', 'MATRAG_OLLAMA_NUM_PREDICT': '400'})
if subprocess.run('which ollama', shell=True, capture_output=True).returncode != 0:
    !apt-get install -y -qq zstd > /dev/null
    !curl -fsSL https://ollama.com/install.sh | sh > /dev/null
subprocess.Popen('ollama serve > /content/ollama.log 2>&1', shell=True)
time.sleep(5)
!ollama pull {OLLAMA_MODEL} 2>&1 | tail -1
"""


def big_eval() -> dict:
    """GPU: many more evaluation questions (curated + written by a local LLM), then retrieval evaluated
    on the Colab database and on the site's search."""
    return notebook([
        md(f"""
# ارزیابی بزرگ: هزاران سؤال (نسخه‌ی {VERSION})

**قبل از شروع:** *Runtime → Change runtime type* → **T4 GPU**. دو سلول دارد؛ هر دو را به ترتیب اجرا کنید.

**سلول ۱** (حدود ۱ تا ۱٫۵ ساعت برای ۱۰۰۰ سؤال؛ ۴ بخش هم‌زمان به مدل داده می‌شود): سؤال‌ها ساخته می‌شوند.
هر سؤال همان لحظه در Drive ذخیره می‌شود (`matrag_data/data/rag-optics/gold/generated.csv`).
- حدود ۵۰۰ سؤال از داده‌های بررسی‌شده: هر ماده‌ی refractiveindex.info به سه شکل (فرمول، نام، نام کوتاه) با نسخه‌ی فارسی،
  مقاله‌های ضرایب غیرخطی و فرمول‌هایی که از مقاله‌ها خوانده شد، و ۴۰ سؤال که جوابشان در مجموعه نیست؛
- و **N** سؤال که مدل زبانی qwen3 روی کارت گرافیک، از روی بخش‌هایی از خود مقاله‌ها (جدول یا متن با عدد) می‌نویسد؛ جواب هر
  سؤال همان مقاله و صفحه است. سؤال‌هایی که از متن کپی شده‌اند یا نام ماده را ندارند خودکار کنار گذاشته می‌شوند.
اگر کولب قطع شد، دوباره اجرا کنید: سؤال‌های ساخته‌شده می‌مانند و از همان‌جا ادامه می‌دهد (شمارنده از تعداد ذخیره‌شده شروع می‌کند).
**مدل سریع‌تر:** `qwen3:4b-instruct` حدود دو برابر سریع‌تر است و سؤال‌هایش کمی ساده‌تر.

**سلول ۲** (حدود ۱ ساعت): هر سه روش جست‌وجو (برداری، کلیدواژه، ترکیبی) روی پایگاه کولب و روی جست‌وجوی سایت، با همه‌ی سؤال‌ها
و نسخه‌ی فارسی‌شان سنجیده می‌شود. نتیجه در `matrag_data/results/eval` در Drive ذخیره می‌شود؛ بعد به من بگویید تا در
زبانه‌ی «ارزیابی» سایت بگذارم.
"""),
        code("#@title ▶️ ۱. ساخت سؤال‌ها\n"
             "N = 1000  #@param {type:\"integer\"}\n"
             "OLLAMA_MODEL = \"qwen3:8b\"  #@param [\"qwen3:8b\", \"qwen3:4b-instruct-2507-q4_K_M\"]\n" + ENV + """
WORK = '/content/drive/MyDrive/matrag_data'
os.environ['MATRAG_DATA_DIR'] = f'{WORK}/data'
os.environ['MATRAG_STORAGE_DIR'] = '/content/storage'
os.environ['MATRAG_CORPUS'] = 'rag-optics'
os.environ['MATRAG_REFERENCE_DIR'] = '/content/refractiveindex/database'
!nvidia-smi --query-gpu=name --format=csv,noheader || echo "⚠️ No GPU: Runtime → Change runtime type → T4 GPU"
print('Copying the database from Drive...')
!mkdir -p /content/storage && cp -rT "{WORK}/storage" /content/storage
""" + INSTALL + """
if not os.path.isdir('/content/refractiveindex/database'):
    !git clone -q --depth 1 https://github.com/polyanskiy/refractiveindex.info-database.git /content/refractiveindex
""" + OLLAMA + """
%cd {WORK}
GOLD = f'{WORK}/data/rag-optics/gold'
!mkdir -p "{GOLD}" && [ -f "{GOLD}/questions.csv" ] && [ ! -f "{GOLD}/questions_86.csv" ] && cp "{GOLD}/questions.csv" "{GOLD}/questions_86.csv"; true
!matrag --corpus rag-optics evaluate build-gold --overwrite 2>&1 | grep -vE "Warning|Loading"
!ls "{GOLD}"/generated.csv > /dev/null 2>&1 && echo "Continuing: $(($(wc -l < "{GOLD}/generated.csv") - 1)) questions already saved"
!matrag --corpus rag-optics evaluate generate-questions --n {N} --workers 4 2>&1 | grep -vE "Warning|Loading|it/s\\]"
%cd /content/RAG
print('✅ Questions ready. Run cell 2.')
"""),
        code("""
#@title ▶️ ۲. ارزیابی با همه‌ی سؤال‌ها (کولب و سایت)
#@markdown **PERSIAN**: نسخه‌ی فارسی سؤال‌ها هم با ترجمه‌ی qwen3 سنجیده شود (حدود ۴۰ دقیقه بیشتر).
PERSIAN = True  #@param {type:"boolean"}
""" + QDRANT_KEYS + """
%cd {WORK}
G = '--gold questions.csv --gold generated.csv'
print('1/3 Colab database (ChromaDB + BM25)...')
!matrag --corpus rag-optics evaluate retrieval {G} 2>&1 | grep -vE "Warning|Loading" | tee -a "{WORK}/logs/eval.log"
print('2/3 The site search (Qdrant)...')
!matrag --corpus rag-optics evaluate retrieval --backend qdrant {G} 2>&1 | grep -vE "Warning|Loading" | tee -a "{WORK}/logs/eval.log"
if PERSIAN:
    print('3/3 Persian questions, translated...')
    !matrag --corpus rag-optics evaluate retrieval --persian {G} 2>&1 | grep -vE "Warning|Loading" | tee -a "{WORK}/logs/eval.log"
!ls -la results/eval | grep -E "retrieval" 
%cd /content/RAG
print('✅ Done: the results are in matrag_data/results/eval on Drive')
"""),
    ], gpu=True)


def worker(n: int) -> dict:
    return notebook([
        md(f"""
# کارگر {n} از {WORKERS}: تبدیل PDFها (نسخه‌ی {VERSION})

این نوت‌بوک فقط PDFها را به متن ساختاریافته تبدیل می‌کند (کُندترین مرحله) و نتیجه را در
`RAG-Optics/_RAG_processed` در Drive می‌گذارد. هر کارگر سهم جداگانه‌ای از PDFها را دارد، پس
کارگرهای ۱ تا {WORKERS} را **هم‌زمان در تب‌های جدا** باز و اجرا کنید. مدل زبانی و پایگاه داده لازم نیست.

- کارت گرافیک اختیاری است (*Runtime → Change runtime type → T4 GPU* سریع‌تر است؛ اگر کولب
  کارت گرافیک نداد، روی CPU هم کار می‌کند، فقط کُندتر).
- تب را باز نگه دارید. اگر قطع شد، دوباره اجرا کنید: مقاله‌های تمام‌شده دوباره تبدیل نمی‌شوند.
- اگر کولب اجازه‌ی باز کردن این همه جلسه را نداد، هر تعداد که شد کافی است: سلول ۵ نوت‌بوک اصلی
  باقی‌مانده را انجام می‌دهد.
- بعد از تمام شدن همه، در نوت‌بوک اصلی سلول‌های ۱ تا ۵ را اجرا کنید.
"""),
        code(f"""
#@title ▶️ اجرای کارگر {n}
WORKER = {n}  #@param {{type:"integer"}}
WORKERS = {WORKERS}  #@param {{type:"integer"}}
COLLECTION = "/content/drive/MyDrive/RAG-Optics"  #@param {{type:"string"}}
""" + ENV + INSTALL + """
os.environ['MATRAG_DATA_DIR'] = '/content/worker_data'  # only the link to the collection lives here
os.environ['MATRAG_CORPUS'] = 'rag-optics'
!matrag link "{COLLECTION}" > /dev/null
!matrag convert --shard {WORKER - 1} --shards {WORKERS} 2>&1 | grep -vE "Warning|it/s\\]"
print(f'✅ Worker {WORKER} finished.')
"""),
    ], gpu=False)


if __name__ == "__main__":
    (HERE / "colab_demo.ipynb").write_text(json.dumps(notebook(MAIN), ensure_ascii=False, indent=1) + "\n", "utf-8")
    for n in range(1, WORKERS + 1):
        (HERE / f"colab_worker_{n}.ipynb").write_text(json.dumps(worker(n), ensure_ascii=False, indent=1) + "\n",
                                                      "utf-8")
    (HERE / "colab_gpu_update.ipynb").write_text(json.dumps(gpu_update(), ensure_ascii=False, indent=1) + "\n", "utf-8")
    (HERE / "colab_site.ipynb").write_text(json.dumps(site(), ensure_ascii=False, indent=1) + "\n", "utf-8")
    (HERE / "colab_big_eval.ipynb").write_text(json.dumps(big_eval(), ensure_ascii=False, indent=1) + "\n", "utf-8")
    (HERE / "colab_new_papers.ipynb").write_text(json.dumps(new_papers(), ensure_ascii=False, indent=1) + "\n",
                                                 "utf-8")
    print("written")
