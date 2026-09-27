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
3. سلول‌های ۱ تا ۵ را به ترتیب اجرا کنید. بعد از سلول ۵ برنامه باز می‌شود.

همه‌ی داده‌ها در Google Drive، پوشه‌ی `matrag_data`، ذخیره می‌شوند و با بسته شدن کولب از بین نمی‌روند.

## کار با برنامه

| زبانه | کار |
|---|---|
| 📚 مقاله‌ها | آپلود PDF (کشیدن و رها کردن) یا دادن شناسه‌ی arXiv؛ مشخصات مقاله (عنوان، نویسندگان، سال، DOI) خودکار پیدا می‌شود |
| ❓ پرسش و پاسخ | جواب با ارجاع (مثلاً «Tan et al. (2019), p. 5») و در کنارش جواب همان مدل **بدون** منابع، برای مقایسه |
| 📄 بسته‌ی منابع | فایلی برای آپلود در چت Gemini یا هر هوش مصنوعی دیگر، بدون مصرف API |
| 📊 استخراج خواص | جدول مقدارها با منبع، صفحه، واحد و شرایط اندازه‌گیری، به‌علاوه‌ی سه بررسی خودکار (پایین) |
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

نتیجه‌ها در `results/eval/` ذخیره می‌شوند. در کولب، سلول‌های ۶ و ۷ همین کار را انجام می‌دهند.

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

### یادداشت‌های فنی که در مقاله قابل ذکرند

- **حروف یونانی گمشده:** PDFهای ساخته‌شده با Word حروف یونانی را با فونت Symbol و در ناحیه‌ی Private Use
  یونیکد ذخیره می‌کنند (مثلاً ν به‌صورت U+F06E). این نویسه‌ها برای مدل زبانی و جست‌وجو نامرئی‌اند. با جدول
  استاندارد Adobe Symbol Encoding به یونیکد برگردانده می‌شوند ([`textfix.py`](src/matrag/textfix.py)).
- **جدول‌ها** به‌صورت «سطر، ستون = مقدار» سریالایز می‌شوند و سطر عنوان در هر قطعه تکرار می‌شود، تا هر عدد
  همراه با معنایش بازیابی شود.
- **بازیابی ترکیبی:** جست‌وجوی برداری مترادف‌ها را پیدا می‌کند و BM25 نمادهای دقیق (γ_air، R(50)، ν3) را.
  روی مجموعه‌ی آزمایشی، ترکیب این دو بهترین MRR را داشت.

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
