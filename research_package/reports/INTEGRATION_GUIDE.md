# راهنمای جامع ادغام و سرهم‌بندی نهایی در پروژه وب‌سایت
## (Integration & Deployment Guide)

این راهنما برای زمانی تهیه شده است که شما تصمیم بگیرید تمام دستاوردهای مستقل این بسته پژوهشی (`research_package/`) را به سایت اصلی و فرانت‌اند متصل کنید. تمام گام‌ها تست‌شده و در یک دستور قابل پیاده‌سازی هستند.

---

### ۱. نقشه ادغام ماژول‌ها در پروژه وب:

| فایل منبع در پکیج مستقل | مقصد در پروژه اصلی | کاربرد در فرانت‌اند |
| :--- | :--- | :--- |
| `data/thermo_optic_expanded.yml` | `data/rag-optics/thermo_optic.yml` | تب محاسبات انطباق فاز دمایی بلورها |
| `data/nonlinear_tensors_expanded.yml` | `data/rag-optics/nonlinear_coefficients.yml` | محاسبه خودکار $d_{\text{eff}}$ برای ۷۱ بلور |
| `modules/spdc/` | `web/src/spdc.client.js` & `src/matrag/quantum/` | تب اختصاصی محاسبات کوانتومی فوتونیک (SPDC) |
| `data/spdc_benchmarks.json` | `web/public/ri/quantum_benchmarks.json` | اعتبارسنجی مقایسه‌ای کاربر با مقالات تجربی |
| `data/eval_dataset_persian.json` | `data/eval/rag_persian_optics.json` | تست دقت پاسخ‌دهی سیستم RAG به فارسی |

---

### ۲. دستور تک‌مرحله‌ای سرهم‌بندی (One-Click Merge Command):

زمانی که آماده ادغام بودید، کافی است به من پیام دهید:
> **«پکیج research_package را با پروژه اصلی ادغام کن»**

من فرآیند زیر را خودکار اجرا خواهم کرد:
1. انتقال داده‌های گرما-نوری و اجرای اسکریپت بازسازی شاخص‌ها:
   ```bash
   cp research_package/data/thermo_optic_expanded.yml data/rag-optics/thermo_optic.yml
   cp research_package/data/nonlinear_tensors_expanded.yml data/rag-optics/nonlinear_coefficients.yml
   PYTHONPATH=src python3 -c "
   from matrag.references import anisotropic, paper_formulas; from pathlib import Path
   out = Path('web/public/ri')
   anisotropic.build(out, Path('data/rag-optics/thermo_optic.yml'))
   anisotropic.build_nonlinear(out, Path('data/rag-optics/nonlinear_coefficients.yml'))
   "
   ```
2. کامپایل موتور کلاینت ساید جاوااسکریپت برای ماژول SPDC در مرورگر:
   - انتقال کدهای JSA, Schmidt Purity, HOM Dip به `web/src/spdc.client.js`.
3. اجرای تست‌های کامل:
   ```bash
   cd web && npm test
   ```

---

### ۳. پایداری داده‌ها و تضمین دسترسی:

تمام فایل‌های این پکیج هم‌اکنون به مخزن گیت‌هاب شما در شاخه `claude/festive-bardeen-nnw123` ارسال (Push) شده‌اند:
🔗 [مشاهده بسته پژوهشی در گیت‌هاب](https://github.com/aminsadidi/RAG/tree/claude/festive-bardeen-nnw123/research_package)
همچنین نسخه‌های محلی روی سرور در مسیر `/home/aminsadidi11584/RAG/research_package/` دائماً در دسترس هستند.
