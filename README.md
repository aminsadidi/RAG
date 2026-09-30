# سیستم بازیابی هوشمند اطلاعات و استخراج خواص فیزیکی مواد از مقالات علمی (RAG)

سیستمی که مقالات علمی (PDF) را می‌خواند، در یک پایگاه داده‌ی برداری نگه می‌دارد، به سؤال‌ها **با ارجاع دقیق به
مقاله و صفحه** جواب می‌دهد و مقدارهای خواص فیزیکی (مثل ضریب پهن‌شدگی خطوط طیفی یا ضریب شکست) را به‌صورت
جدول استخراج می‌کند. درستی نتایج با پایگاه‌های مرجع **HITRAN** و **refractiveindex.info** سنجیده می‌شود.

برنامه‌ی کامل پروژه: [`ROADMAP.md`](ROADMAP.md)

---

## اجرا در Google Colab (پیشنهادی)

1. نوت‌بوک را باز کنید:
   [colab_demo.ipynb در کولب](https://colab.research.google.com/github/aminsadidi/RAG/blob/claude/festive-bardeen-nnw123/notebooks/colab_demo.ipynb)
2. منوی **Runtime → Change runtime type → T4 GPU**
3. سلول‌ها را به ترتیب اجرا کنید. بعد از سلول ۷ برنامه باز می‌شود.

همه‌ی داده‌ها در Google Drive، پوشه‌ی `matrag_data`، ذخیره می‌شوند و با بسته شدن کولب از بین نمی‌روند.

### مجموعه‌ی بزرگ مقاله‌ها در Drive (پوشه‌ی `RAG-Optics`)

برنامه مقاله‌ها را مستقیم از پوشه‌ی `RAG-Optics` در Drive می‌خواند (مجموعه‌ی `rag-optics`):

| پوشه | محتوا |
|---|---|
| `01_Papers_by_Category/<دسته>/<بلور>/` | PDFها (هر جای دیگری از پوشه هم باشند پیدا می‌شوند) |
| `02_Master_Index/` | فهرست اصلی همه‌ی مقاله‌ها با DOI، دسته، بلور و چکیده؛ و گزارش `pdf_inventory.csv` |
| `04_Dispersion_Formulas_Data/` | داده‌ی مرجع refractiveindex.info؛ **عمداً وارد جست‌وجو نمی‌شود** (کلید ارزیابی است) |
| `_RAG_processed/` | خروجی برنامه (PDFهای تبدیل‌شده)؛ دست نزنید |

- هر PDF با **DOI در نام فایل** (مثل `10.1364-josab.6.000616.pdf`؛ `/` به `-` یا `_`) یا با مسیر ثبت‌شده در فهرست،
  به مقاله‌ی خودش وصل می‌شود؛ دسته، بلور و مشخصات از فهرست می‌آید (بدون جست‌وجوی Crossref).
- مقاله‌های **بدون PDF** با چکیده‌شان وارد می‌شوند و در جواب‌ها با برچسب «abstract only» مشخص‌اند.
- سلول ۴ PDFها را در پوشه‌ی بلور خودشان مرتب می‌کند (`matrag organize --move`؛ هیچ فایلی پاک نمی‌شود).
- تبدیل PDF کُندترین مرحله است: نوت‌بوک‌های `colab_worker_1` تا `colab_worker_4` را هم‌زمان اجرا کنید تا
  هر کدام بخشی از PDFها را تبدیل کند ([کارگر ۱](https://colab.research.google.com/github/aminsadidi/RAG/blob/claude/festive-bardeen-nnw123/notebooks/colab_worker_1.ipynb)،
  [۲](https://colab.research.google.com/github/aminsadidi/RAG/blob/claude/festive-bardeen-nnw123/notebooks/colab_worker_2.ipynb)،
  [۳](https://colab.research.google.com/github/aminsadidi/RAG/blob/claude/festive-bardeen-nnw123/notebooks/colab_worker_3.ipynb)،
  [۴](https://colab.research.google.com/github/aminsadidi/RAG/blob/claude/festive-bardeen-nnw123/notebooks/colab_worker_4.ipynb))؛
  سپس سلول ۵ نوت‌بوک اصلی باقی‌مانده را انجام می‌دهد و پایگاه داده را می‌سازد.

```
matrag --corpus rag-optics link /content/drive/MyDrive/RAG-Optics
matrag --corpus rag-optics organize --move        # مرتب‌سازی PDFها + گزارش
matrag --corpus rag-optics convert --shard 0 --shards 4   # کارگر ۱ از ۴ (فقط تبدیل)
matrag --corpus rag-optics ingest --prune         # ساخت پایگاه داده
matrag --corpus rag-optics status                 # چند مقاله: متن کامل / فقط چکیده / تبدیل‌شده / در پایگاه
```

نوت‌بوک‌ها از `notebooks/build_notebooks.py` ساخته می‌شوند؛ برای تغییر، همان فایل را ویرایش و اجرا کنید.

## کار با برنامه

| زبانه | کار |
|---|---|
| 📚 مقاله‌ها | آپلود PDF (کشیدن و رها کردن) یا دادن شناسه‌ی arXiv؛ مشخصات مقاله (عنوان، نویسندگان، سال، DOI) خودکار پیدا می‌شود |
| ❓ پرسش و پاسخ | سؤال به فارسی یا انگلیسی؛ جواب با ارجاع (مثلاً «Tan et al. (2019), p. 5») و در کنارش جواب همان مدل **بدون** منابع، برای مقایسه؛ نمایش **صفحه‌ی اصلی مقاله با بخش استفاده‌شده‌ی رنگی** |
| 📄 بسته‌ی منابع | فایلی برای آپلود در چت Gemini یا هر هوش مصنوعی دیگر، بدون مصرف API |
| 📊 استخراج خواص | جدول مقدارها با منبع، صفحه، واحد و شرایط اندازه‌گیری، به‌علاوه‌ی سه بررسی خودکار (پایین)؛ نمایش هر مقدار روی صفحه‌ی مقاله |
| 🧮 فرمول ← جدول | استخراج فرمول‌های پاشندگی (سلمایر، کوشی، …) از جدول‌ها و متن مقاله، ساخت جدول ضریب شکست در هر طول موج و مقایسه با refractiveindex.info |
| 📈 طیف (HITRAN) | طیف جذبی (Voigt) از HITRAN با HAPI، و طیف دوم با جایگزینی مقدارهای استخراج‌شده از مقاله، همراه با نمودار اختلاف |

**مجموعه (corpus):** هر موضوع مقاله‌ها و پایگاه داده‌ی خودش را دارد (`hitran` و `optical`). برای موضوع جدید، کافی
است اسم تازه‌ای در کادر «مجموعه‌ی مقالات» تایپ کنید.

### سه بررسی خودکار روی هر مقدار استخراج‌شده

| ستون | معنی |
|---|---|
| `value_in_source` | عدد، همان‌طور که نوشته شده، واقعاً در متن مقاله هست؟ (در برابر عددسازی مدل) |
| `evidence_verified` | جمله‌ای که مدل به‌عنوان شاهد آورده، عیناً در مقاله هست؟ |
| `plausible` | مقدار در بازه‌ی فیزیکی معقول آن خاصیت هست؟ (خطای واحد یا برداشت اشتباه، مثل «تعداد خط‌ها») |

بازه‌های فیزیکی در `src/matrag/profiles/<corpus>.yml` تعریف شده‌اند و با گذاشتن فایلی به همین شکل در
`data/<corpus>/profile.yml` قابل تغییرند.

---

## ارزیابی (برای بخش نتایج مقاله)

سؤال‌های مرجع با صفحه‌ی جواب و مقدار درست در `data/<corpus>/gold/questions.csv` هستند
(قالب فایل در ابتدای [`src/matrag/evaluate.py`](src/matrag/evaluate.py) توضیح داده شده).

```
matrag --corpus hitran evaluate retrieval     # Recall@k و MRR برای سه روش بازیابی (بدون مدل زبانی)
matrag --corpus hitran evaluate answers       # دقت جواب: RAG در برابر مدل بدون منبع، و آزمون «پیدا نشد»
matrag --corpus hitran evaluate extraction results.csv   # دقت، بازخوانی و F1 در برابر gold/values.csv
matrag reference hitran results.csv --molecule CO2 --nu-min 5007.7 --nu-max 5007.9   # مقایسه با HITRAN
matrag reference optical-candidates           # فهرست مقاله‌های منبع refractiveindex.info و وضعیت دسترسی آزاد
```

نتیجه‌ها در `results/eval/` ذخیره می‌شوند. در کولب، سلول‌های ۸ تا ۱۰ همین کار را انجام می‌دهند.

**ارزیابی خودکار با refractiveindex.info** (بدون برچسب‌گذاری دستی؛ برای مجموعه‌ی `rag-optics`):

```
matrag --corpus rag-optics evaluate build-gold    # سؤال «فرمول پاشندگی ماده‌ی X» برای هر ماده‌ای که فرمولش از مقاله‌ای در مجموعه آمده
matrag --corpus rag-optics evaluate retrieval     # آیا یکی از همان مقاله‌ها بازیابی می‌شود؟
matrag --corpus rag-optics evaluate formulas --limit 20   # استخراج فرمول و مقایسه‌ی n(λ) با پایگاه: سهم مقاله‌ها با |Δn| ≤ 1e-4، 1e-3، 1e-2
```

ارزیابی فرمول‌ها ادامه‌پذیر است: هر اجرا مقاله‌های تازه را پردازش می‌کند و نتیجه‌ی هر مقاله بلافاصله در
`results/eval/rag-optics_formula_benchmark.jsonl` ذخیره می‌شود.

### نتایج اولیه روی مقاله‌های آزمایشی (۳ مقاله در هر حوزه)

بازیابی: آیا صفحه‌ی درستِ مقاله‌ی درست در k قطعه‌ی اول هست؟ (`results/eval/*_retrieval.csv`)

| حوزه | روش | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---|---|---|---|---|
| HITRAN (۱۵ سؤال) | برداری | 0.60 | 0.73 | 0.87 | 0.72 |
| | BM25 | 0.60 | 0.80 | 0.87 | 0.72 |
| | ترکیبی | **0.73** | 0.80 | 0.87 | **0.79** |
| اپتیک (۱۳ سؤال) | برداری | 0.69 | 1.00 | 1.00 | 0.85 |
| | BM25 | **0.92** | 1.00 | 1.00 | **0.96** |
| | ترکیبی | 0.69 | 1.00 | 1.00 | 0.83 |

پاسخ به سؤال (HITRAN، ۱۵ سؤال جواب‌دار + ۱ سؤال بی‌جواب؛ مدل محلی Qwen3-4B؛ `results/eval/hitran_answers*.csv`):

| سیستم | دقت (جواب شامل مقدار درست) | «پیدا نشد» برای سؤال جواب‌دار | امتناع درست در سؤال بی‌جواب |
|---|---|---|---|
| RAG + Qwen3-4B | **0.93** (۱۴ از ۱۵) | 0.00 | 1.0 |
| Qwen3-4B بدون منبع | 0.00 | 1.00 | 1.0 |

تنها خطای RAG (سؤال h07): منبع درست بازیابی شده بود، اما مدل به‌جای مقدار دقیق 5007.787078 cm⁻¹ عدد تقریبی
«∼5000 cm⁻¹» را از مقدمه‌ی مقاله آورد، که نمونه‌ای از خطای «دقت عددی» برای تحلیل خطاست.

سؤال فارسی (همان ۱۵ سؤال HITRAN به فارسی، ترجمه با Qwen3-4B، سپس جست‌وجو؛ `results/eval/hitran_retrieval_fa*.csv`):

| روش | MRR سؤال انگلیسی | MRR سؤال فارسی ← ترجمه |
|---|---|---|
| برداری | 0.72 | **0.72** |
| BM25 | 0.72 | 0.63 |
| ترکیبی | 0.79 | 0.72 |

جست‌وجوی برداری (معنایی) از ترجمه اثر نمی‌پذیرد، ولی BM25 به واژه‌های دقیق وابسته است و افت می‌کند. خطای
شاخص ترجمه: «چند خط» در دو سؤال به «several lines» (به‌جای how many) ترجمه شد، که ابهام واژه‌ی «چند» در فارسی است.

این اعداد روی مجموعه‌ی کوچک آزمایشی‌اند و فقط نشان می‌دهند ابزار ارزیابی کار می‌کند؛ نتیجه‌ی نهایی باید روی
مقاله‌های اصلی و سؤال‌های بیشتر گرفته شود.

## خط لوله و ابزارها

```
PDF ─► Docling (متن، جدول، ساختار) ─► ترمیم حروف یونانی و نمادها ─► قطعه‌بندی ساختارمحور (HybridChunker)
    ─► Embedding (bge-base-en-v1.5) ─► ChromaDB
پرسش ─► بازیابی ترکیبی: برداری + BM25 با Reciprocal Rank Fusion ─► مدل زبانی (Qwen3 از Ollama یا Gemini)
    ─► جواب با ارجاع | استخراج ساخت‌یافته (Pydantic) ─► سه بررسی خودکار ─► مقایسه با HITRAN / refractiveindex.info
```

| بخش | ابزار |
|---|---|
| تبدیل PDF | [Docling](https://github.com/docling-project/docling) |
| چارچوب RAG | [LlamaIndex](https://github.com/run-llama/llama_index) |
| پایگاه برداری | [ChromaDB](https://github.com/chroma-core/chroma) |
| Embedding | [BAAI/bge-base-en-v1.5](https://huggingface.co/BAAI/bge-base-en-v1.5) |
| بازیابی کلیدواژه‌ای | BM25 ([bm25s](https://github.com/xhluca/bm25s)) |
| مدل زبانی | [Ollama](https://ollama.com) (Qwen3) یا Google Gemini |
| مشخصات مقاله | arXiv و [Crossref API](https://api.crossref.org) |
| مرجع طیف‌سنجی | [HITRAN](https://hitran.org) از طریق [HAPI](https://hitran.org/hapi/) |
| مرجع اپتیکی | [refractiveindex.info-database](https://github.com/polyanskiy/refractiveindex.info-database) |
| رابط کاربری | [Gradio](https://gradio.app) |

### فرمول به‌جای نمودار (خواص اپتیکی)

بسیاری از مقاله‌های اپتیکی ضریب شکست را فقط به شکل نمودار نشان می‌دهند، اما ضرایب فرمول برازش‌شده (مثلاً سلمایر)
را در جدول یا متن می‌آورند. سیستم این ضرایب را استخراج می‌کند و با آن‌ها n(λ) را در هر طول موجی حساب می‌کند
([`dispersion.py`](src/matrag/dispersion.py)، [`formulas.py`](src/matrag/formulas.py)):

- شکل عمومی: n² = A + Σ Bᵢ·λ^pᵢ/(λ² − Cᵢ) + Σ Eⱼ·λ^qⱼ (یا n = … برای کوشی)، با قطب به‌صورت C یا طول موج
  تشدید λᵢ، واحد µm یا nm، و ضرایب وابسته به دما به‌صورت چندجمله‌ای بر حسب T.
- هر ۹ نوع فرمول refractiveindex.info طبق سند تعریف خود پایگاه پیاده‌سازی شده است.
- هر فرمول استخراج‌شده سه بررسی دارد: همه‌ی ضرایب در متن منبع هستند؟ فرمول از نظر فیزیکی معقول است
  (1 < n < 5، بدون تشدید در بازه، |dn/dλ| کوچک)؟ و اختلافش با مدخل همان مقاله در refractiveindex.info چقدر است؟
- درستی‌سنجی موتور: ضرایب جدول ۵ مقاله‌ی Leviton و همکاران (CaF₂، وابسته به دما) مقدارهای جدول ۱ همان مقاله را
  تا رقم پنجم بازتولید می‌کنند (n = 1.44221 در 0.40 µm و 295 K).

```
matrag --corpus optical formulas                     # استخراج و مقایسه → results/formulas.jsonl
matrag formula-table results/formulas.jsonl --index 0 --from 0.4 --to 2 --step 0.01   # جدول n(λ)
```

برای مقاله‌هایی که فرمول را فقط به شکل معادله‌ی تصویری دارند، `MATRAG_DO_FORMULA_ENRICHMENT=true` معادله‌ها را با
مدل CodeFormula در Docling به LaTeX تبدیل می‌کند (روی کارت گرافیک؛ بدون آن کند است).

### یادداشت‌های فنی که در مقاله قابل ذکرند

- **سؤال فارسی:** مقاله‌ها انگلیسی‌اند، پس سؤال فارسی اول با همان مدل زبانی به انگلیسی ترجمه می‌شود و جست‌وجو
  با ترجمه انجام می‌شود؛ مدل هر دو (اصل و ترجمه) را می‌بیند و به فارسی جواب می‌دهد. برای اصطلاحاتی که ترجمه‌ی
  تحت‌اللفظی‌شان غلط است (مثلاً «عدد موج» = wavenumber، نه wavelength) واژه‌نامه‌ی فیزیکی به مدل داده می‌شود
  ([`qa.py`](src/matrag/qa.py)). اثر ترجمه با `matrag evaluate retrieval --persian` سنجیده می‌شود.
- **نمایش منبع:** Docling مختصات هر پاراگراف و جدول را نگه می‌دارد؛ این مختصات همراه هر قطعه ذخیره و روی
  تصویر صفحه (pypdfium2) رنگی می‌شود ([`pdfview.py`](src/matrag/pdfview.py)).

- **حروف یونانی گمشده:** PDFهای ساخته‌شده با Word حروف یونانی را با فونت Symbol و در ناحیه‌ی Private Use
  یونیکد ذخیره می‌کنند (مثلاً ν به‌صورت U+F06E). این نویسه‌ها برای مدل زبانی و جست‌وجو نامرئی‌اند. با جدول
  استاندارد Adobe Symbol Encoding به یونیکد برگردانده می‌شوند ([`textfix.py`](src/matrag/textfix.py)).
- **جدول‌ها** به‌صورت «سطر، ستون = مقدار» سریالایز می‌شوند و سطر عنوان در هر قطعه تکرار می‌شود، تا هر عدد
  همراه با معنایش بازیابی شود.
- **بازیابی ترکیبی:** جست‌وجوی برداری مترادف‌ها را پیدا می‌کند و BM25 نمادهای دقیق (γ_air، R(50)، ν3) را.
  روی مجموعه‌ی آزمایشی، ترکیب این دو بهترین MRR را داشت.

## سایت (Cloudflare Workers + Qdrant Cloud)

پوشه‌ی `web/` یک سایت خصوصی (با رمز) است که روی پایگاه داده‌ی پردازش‌شده جست‌وجو می‌کند. سایت **پاسخ نمی‌نویسد**:
منابع را با نام مقاله، صفحه و محل روی صفحه نشان می‌دهد و «فایل برای هوش مصنوعی» (همان context pack برنامه) می‌سازد.

- **جست‌وجو:** سؤال فارسی با Llama 3.3 70B (Workers AI) و همان واژه‌نامه‌ی `qa.PERSIAN_GLOSSARY` ترجمه می‌شود؛
  بردار سؤال با همان مدل bge-base-en-v1.5 (pooling = cls، یعنی همان بردار محلی) ساخته می‌شود؛ Qdrant جست‌وجوی
  برداری و BM25 را با RRF ترکیب می‌کند.
- **داده:** سلول ۱۱ نوت‌بوک (`matrag export-qdrant`) بخش‌ها را با **همان بردارهای ذخیره‌شده** در Qdrant بارگذاری
  می‌کند؛ `matrag evaluate retrieval --backend qdrant` همان ارزیابی را روی جست‌وجوی سایت اجرا می‌کند.
- **نمایش صفحه:** PDFها روی سرور نیستند (حق نشر). در زبانه‌ی «مجموعه» پوشه‌ی مقاله‌ها روی رایانه‌ی خودتان انتخاب
  می‌شود و صفحه با pdf.js در مرورگر باز می‌شود، با بخشِ پیداشده به رنگ زرد. بدون پوشه، نقشه‌ی محل بخش روی صفحه نمایش داده می‌شود.
- متن‌های مشترک (پرامپت‌ها، واژه‌نامه، قاعده‌ی فرمول‌ها) از پایتون در `web/src/shared.json` نوشته می‌شوند
  (`python -m matrag.web_shared`) و تست‌ها یکسان بودن دو طرف را بررسی می‌کنند.
- **استقرار:** `cd web && npm install && npx wrangler deploy`؛ رازها با `npx wrangler secret put`:
  `QDRANT_URL`، `QDRANT_API_KEY`، `SITE_PASSWORD`. یک cron روزانه کلاستر رایگان Qdrant را بیدار نگه می‌دارد.

## اجرای محلی (اختیاری)

```
pip install -e ".[dev]"                   # یا نسخه‌های دقیق: pip install -r requirements-lock.txt
matrag --corpus hitran add 1906.01475     # افزودن مقاله از arXiv
matrag app                                # رابط وب روی http://127.0.0.1:7860
pytest                                    # تست‌ها (بدون اینترنت و بدون مدل)
```

مدل محلی نیاز به [Ollama](https://ollama.com) دارد (`ollama pull qwen3:4b-instruct-2507-q4_K_M`)؛ برای Gemini
کلید را در `MATRAG_GOOGLE_API_KEY` قرار دهید (نمونه: [`.env.example`](.env.example)).

## حق نشر

فایل‌های PDF مقالات هرگز در این مخزن قرار نمی‌گیرند (`.gitignore`). فقط کد، سؤال‌های مرجع و فهرست مشخصات
مقاله‌ها منتشر می‌شود.
