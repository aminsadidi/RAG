"""Writes the Colab notebooks (run: python notebooks/build_notebooks.py).

The notebooks are generated so the main notebook and the four identical
worker notebooks stay in sync. Colab gives every notebook *file* its own
session, so parallel workers need separate files.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
BRANCH = "claude/festive-bardeen-nnw123"
VERSION = 10
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
# refractiveindex.info database (downloaded in cell 3), shared by all corpora.
os.environ['MATRAG_REFERENCE_DIR'] = f'{WORK}/data/optical/reference/database'
!mkdir -p "{WORK}/storage" /content/storage && cp -rT "{WORK}/storage" /content/storage
print('✅ Data folder:', WORK)
"""),
    code("#@title ۳. نصب برنامه از GitHub\n" + INSTALL + """
# refractiveindex.info database (CC0), used to check formulas extracted from optical papers;
# downloaded once into Drive.
REF_DB = f"{WORK}/data/optical/reference"
if not os.path.isdir(f"{REF_DB}/database"):
    !git clone -q --depth 1 https://github.com/polyanskiy/refractiveindex.info-database.git "{REF_DB}" && echo "refractiveindex.info database saved to Drive"
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
!matrag link "{COLLECTION}" > /dev/null
if ORGANIZE:
    !matrag organize --move 2>&1 | grep -vE "Warning" | tail -4
print()
!matrag status 2>&1 | grep -vE "Warning"
"""),
    code("""
#@title ۵. پردازش مقاله‌ها و ساخت پایگاه داده
#@markdown بار اول برای حدود ۲۰۰۰ PDF چند ساعت طول می‌کشد (تبدیل PDF کُندترین مرحله است). اگر
#@markdown نوت‌بوک‌های کارگر را هم‌زمان اجرا کرده‌اید، این سلول را **بعد از تمام شدن آن‌ها** اجرا کنید
#@markdown (یا همین حالا؛ فقط ممکن است چند مقاله دو بار تبدیل شود). مقاله‌های بدون PDF با چکیده‌شان وارد
#@markdown می‌شوند. اگر کولب قطع شد، دوباره اجرا کنید: کار از همان‌جا ادامه پیدا می‌کند.
%cd {WORK}
!matrag ingest --prune 2>&1 | grep -vE "Warning|Loading|it/s\\]" | tee -a "{WORK}/logs/ingest.log"
%cd /content/RAG
!matrag status 2>&1 | grep -vE "Warning"
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
!mkdir -p "{WORK}/data/{CORPUS}/gold" && cp -n /content/RAG/data/{CORPUS}/gold/*.csv "{WORK}/data/{CORPUS}/gold/" 2>/dev/null; true
%cd {WORK}
!matrag evaluate retrieval 2>&1 | grep -vE "Warning|Loading" | tee -a "{WORK}/logs/eval.log"
%cd /content/RAG
"""),
    code("""
#@title ۹. ارزیابی پاسخ‌ها: RAG در برابر مدل بدون منبع
LIMIT = 16  #@param {type:"integer"}
%cd {WORK}
!matrag evaluate answers --limit {LIMIT} 2>&1 | grep -vE "Warning|Loading" | tee -a "{WORK}/logs/eval.log"
%cd /content/RAG
"""),
]


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
    print("written")
