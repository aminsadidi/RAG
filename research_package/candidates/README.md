# MatRAG Thesis Project: NLO Crystal Candidates Package (`gemini/drafts`)

این پکیج شامل رونویسی‌ها، ممیزی‌های مو به مو (Audit)، استخراج گزیده‌های کاندید (Passages) و جداول اعتبارسنجی مقالات اصلی پروژه پایان‌نامه MatRAG برای بلورهای اپتیک غیرخطی (NLO) است. 

تمام این داده‌ها به عنوان **Candidate** جهت بازبینی نهایی توسط کِلود (Claude) در برنچ اصلی استخراج و ساختاربندی شده‌اند. طبق اصول سخت‌گیرانه پروژه، هیچ تغییری خارج از پوشه `research_package/candidates/` اعمال نشده و هیچ مقداری بدون باز شدن مستقیم مقاله و ذکر نقل‌قول مستقیم (Verbatim Quote) ثبت نشده است.

---

## ۱. گزارش جامع کارهای انجام‌شده (Tasks Overview)

### تسک ۱: ممیزی کار قبلی (Task 1: Audit of Earlier Work)
* **جامعه ممیزی:** بررسی تک‌تک ورودی‌های فایل‌های `thermo_optic_expanded.yml` (۲۵ ورودی) و `nonlinear_tensors_expanded.yml` (۷۱ ورودی).
* **خروجی:** [`candidates/audit.jsonl`](audit.jsonl) شامل **۹۶ رکورد کامل**.
* **رفع ابهامات و اشکالات شناخته‌شده:**
  1. **Dolev 2009:** شناسه قبلی `10.1007_s00340-009-3547-4` غلط بود؛ شناسه واقعی چاپ‌شده روی مقاله `10.1007/s00340-009-3502-3` (*Appl. Phys. B* 96: 423–432) ثبت گردید. مقادیر با جدول ۳ مطابقت کامل دارند.
  2. **Sugawara 1998:** شناسه قبلی `10.1016_s0921_5107_98_00234_7` مربوط به ژورنال دیگری بود؛ ژورنال واقعی *Solid State Communications* (Vol. 107, No. 5, pp. 233–237) و شناسه `10.1016/S0038-1098(98)00190-2` ثبت شد.
  3. **Zhai 2013:** عنوان رسمی مقاله *"Measurement of thermal refractive index coefficients of nonlinear optical crystal RbBe2BO3F2"* در *Optical Materials* 36 (2013) 482–485 با DOI رسمی `10.1016/j.optmat.2013.09.017` بررسی و معادله (۲) مو به مو استخراج شد.
  4. **Ghosh 1992:** شناسه قبلی `10.1117_12.138865` غلط بود؛ شناسه واقعی در مجموعه‌مقالات SPIE برابر `10.1117/12.637003` است.
  5. **علامت منفی $dn/dT$ در KDP:** در فایل قبلی ترم شبکه (Lattice contribution) $L = -30.841 \times 10^{-6}$ /°C از معادله (۴) قوش جا افتاده بود که باعث می‌شد $dn/dT$ در ناحیه مرئی/فروسرخ به اشتباه مثبت به دست آید؛ در نقل‌قول مستقیم و گزارش ممیزی تصحیح شد.
  6. **Ghosh 1995:** ژورنال *Journal of Applied Physics* (Vol. 78, No. 11, pp. 6752–6760) و مقادیر جدول ۲ برای LBO و BBO تطبیق داده شد.
  7. **منبع RBBF:** مشخص شد داده‌های گرما-نوری RBBF از ژای ۲۰۱۳ موجود است ولی در فایل `nonlinear_tensors_expanded.yml` ماده RBBF درج نشده بود (تنها KBBF وارد شده بود).
  8. **مقدار $d_{36}$ بلور CdSiP2 در گزارش:** در جدول گزارش `CRYSTAL_CATALOG_OVERVIEW.md` خط ۱۰۳۲ به اشتباه $d_{36} = 34.5$ تایپ شده بود، در حالی که در متن مقاله کاتو، اومه‌مورا و پتروف (۲۰۱۱) و چک‌پوینت‌ها مقدار واقعی $d_{36} = 84.5\text{ pm/V}$ است.

---

### تسک ۲: رونویسی مو به مو از جداول پتروف ۲۰۱۲ و ۲۰۱۵ (Task 2: Petrov Tables)
* **فایل‌های مرجع:** `petrov2012.pdf` و `petrov2015.pdf`.
* **خروجی:** [`candidates/petrov_tables.jsonl`](petrov_tables.jsonl) شامل **۳۷ سطر دقیق**.
  - **جدول ۲ پتروف ۲۰۱۲ (Optical Materials):** ۱۷ سطر مربوط به بلورهای غیر اکسیدی فروسرخ میانی به همراه ضرایب $d_{il}$، تصحیح میلر، زوایای همگامی فاز، رسانندگی گرمایی و گاف انرژی.
  - **جدول ۲ پتروف ۲۰۱۵ (Progress in Quantum Electronics):** ۱۷ سطر مشخصات بلورهای غیر اکسیدی دوشکستی.
  - **جدول ۳ پتروف ۲۰۱۵:** ۳ سطر نیمه‌رساناهای مکعبی ساختار QPM شامل GaAs ($d_{14} = 83\text{--}86\text{ pm/V}$)، GaP ($d_{14} = 37\text{ pm/V}$) و ZnSe ($d_{14} = 26.4\text{ pm/V}$).
  - پانویس‌ها، مراجع اختصاصی هر سطر و دستگاه مختصات بلوری عیناً منتقل شدند.

---

### تسک ۳: اسکن جامع مجموعه مقالات (Task 3: Whole Collection Scan)
* **اسکریپت اسکنر چندنخی:** [`candidates/run_scanner.py`](run_scanner.py) (کاملاً مستقل در پوشه candidates و مجهز به چک‌پوینت لحظه‌ای).
* **تعداد مقالات اسکن‌شده تا این مرحله:** **۱۷۶ مقاله** (شامل ۳۲ مقاله موجود در core، ۲۱ مقاله scratch و ۱۲۳ مقاله درایو).
* **خروجی‌های استخراج‌شده:**
  - [`candidates/scan_dij.jsonl`](scan_dij.jsonl): **۱۵۵ قطعه کاندید** تانسورهای غیرخطی $d_{ij}$ و $d_{eff}$ با ذکر شماره صفحه دقیق و نقل‌قول کامل.
  - [`candidates/scan_thermo.jsonl`](scan_thermo.jsonl): **۴ قطعه کاندید** روابط و ضرایب گرما-نوری $dn/dT$.
  - [`candidates/scan_sellmeier.jsonl`](scan_sellmeier.jsonl): **۲۹ قطعه کاندید** معادلات و ضرایب پاشندگی Sellmeier.
  - [`candidates/SCAN_SUMMARY.md`](SCAN_SUMMARY.md): جدول آماری مقالات و صفحات به تفکیک هر بلور.

---

### تسک ۴: فهرست مقالات مفقود در papers.json (Task 4: Missing Original Papers)
* **خروجی:** [`candidates/missing_papers.md`](missing_papers.md).
* **تعداد مقالات استخراج و تأیید شده:** **۲۰ مقاله اصلی**.
* **وضعیت Crossref:** تمام ۲۰ مقاله به صورت برخط از طریق Crossref API بررسی شدند و با وضعیت `crossref: ok` (تطابق کامل عنوان، نویسندگان، سال و ژورنال) ثبت گردیدند.

---

## ۲. آمار کمی و تفکیک وضعیت‌ها (Counts & Statuses)

| تسک | فایل خروجی | تعداد رکورد | وضعیت‌ها |
| :--- | :--- | :---: | :--- |
| **Task 1: Audit** | `audit.jsonl` | **۹۶** | `candidate`: 86, `not_found`: 10 (کتاب‌ها/مقالاتی که متن PDF آن‌ها در درایو موجود نبود) |
| **Task 2: Petrov** | `petrov_tables.jsonl` | **۳۷** | `candidate`: 37 (رونویسی دقیق ۱۰۰٪ سطربه‌سطر) |
| **Task 3: Scan** | `scan_dij.jsonl`<br>`scan_thermo.jsonl`<br>`scan_sellmeier.jsonl` | **۱۵۵**<br>**۴**<br>**۲۹** | `candidate`: 188 (بدون تفسیر، حاوی شماره صفحه و نقل‌قول مستقیم) |
| **Task 4: Missing**| `missing_papers.md` | **۲۰** | `crossref: ok`: 20 (تماماً تأیید شده در پایگاه کراس‌رف) |

---

## ۳. فهرست فایل‌های تولید شده در این پکیج

```text
research_package/candidates/
├── audit.jsonl                  # نتایج ممیزی ۹۶ ورودی تسک ۱
├── build_audit.py               # اسکریپت ممیزی تسک ۱
├── build_missing_papers.py      # اسکریپت استعلام کراس‌رف تسک ۴
├── build_petrov_tables.py       # اسکریپت رونویسی جداول پتروف تسک ۲
├── generate_audit.py            # ماژول کمکی مکانیابی فایل‌ها
├── missing_papers.md            # گزارش مقالات مفقود تسک ۴ با تاییدیه کراس‌رف
├── petrov_tables.jsonl          # داده‌های جداول پتروف ۲۰۱۲ و ۲۰۱۵ تسک ۲
├── README.md                    # همین مستند جامع
├── run_scanner.py               # اسکریپت اسکنر پرسرعت تسک ۳
├── SCAN_SUMMARY.md              # جدول خلاصه آماری صفحات و مواد تسک ۳
├── scan_checkpoint.json         # چک‌پوینت اسکن مقالات
├── scan_dij.jsonl               # قطعات کاندید dij تسک ۳
├── scan_sellmeier.jsonl         # قطعات کاندید سِلمایر تسک ۳
└── scan_thermo.jsonl            # قطعات کاندید گرما-نوری تسک ۳
```

تمام مراحل روی برنچ جدید `gemini/drafts` مرحله به مرحله کامیت و روی گیت‌هاب پوش شدند.
