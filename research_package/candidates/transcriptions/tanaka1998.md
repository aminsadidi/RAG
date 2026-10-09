# Transcription of tanaka1998.pdf

## ۱. مشخصات کتاب‌شناختی (صفحه اول مقاله / PDF Page 1)
- **عنوان:** Thermo-optic dispersion formula of AgGaSe2 and its practical applications
- **نویسندگان:** Eiko Tanaka and Kiyoshi Kato
- **وابستگی سازمانی (Affiliations):**
  - E. Tanaka is with the Department of Computer Science, Keio University, Hiyoshi 3-14-1, Kohoku, Yokohama, Japan.
  - K. Kato is with the Second Research Center, Japan Defense Agency, Ikejiri 1-2-24, Setagaya, Tokyo, Japan.
- **مجله:** APPLIED OPTICS
- **مشخصات نشر:** Vol. 37, No. 3, pp. 561–564 (20 January 1998)
- **تاریخ دریافت:** Received 3 April 1997
- **شناسه دیجیتال (DOI):** در منبع نیست (روی صفحه اول چاپ نشده است)

---

## ۲. محورها و قرارداد نامگذاری
بلور تک‌محوری نوری منفی (Uniaxial crystal: $n_o, n_e$).
عین جملات مقاله در متن:
- صفحه PDF 1 (Applied Optics Vol. 37, p. 561):
  > "The AgGaSe2 prism used in this experiment was cut at an apex angle of 20.00° with a hypotenuse of 10 × 15 mm2."
- صفحه PDF 2 (p. 562):
  > "The subscripts of the phase-matching angles represent the polarization directions of the interacting wavelengths, in order. o and e denote ordinary and extraordinary polarization."
- متن صفحه PDF 2:
  > "The crystal is oriented at $\theta = 49.8^\circ$."

---

## ۳. معادلات سلمایر (Sellmeier Equations) — معادله (1)
- **شماره معادله:** (1)
- **شماره صفحه PDF:** صفحه 2 (p. 562)
- **دمای مرجع:** دمای اتاق (room temperature، حدود 20.0 °C بر اساس متن صفحه 1: "between 20.0 and 120.0 °C")
- **محدوده طول موج:** فروسرخ میانی تا دور (واحد $\lambda$ بر حسب میکرومتر: "where $\lambda$ is in micrometers")

شکل کامل فرمول:
$$n_o^2 = 6.8507 + \frac{0.4297}{\lambda^2 - 0.1584} - 0.00125\lambda^2,$$

$$n_e^2 = 6.6792 + \frac{0.4597}{\lambda^2 - 0.2122} - 0.00126\lambda^2, \quad (1)$$

> [MISMATCH]: در استخراج لایه متنی خام PDF، به دلیل کدگذاری نویسه‌های ریاضی، علامت مساوی به عدد 5، علامت مثبت به عدد 1، علامت منفی به عدد 2 و علامت $\lambda$ به حرف l تبدیل شده است (`no 2 5 6.8507 1 0.4297 l2 2 0.1584 2 0.00125l2`). تصویر اسکن‌شده صفحه به طور قطعی فرمول صحیح بالا را نشان می‌دهد.

---

## ۴. فرمول‌های ترمواپتیک ($dn/dT$) — معادله (2)
- **شماره معادله:** (2)
- **شماره صفحه PDF:** صفحه 2 (p. 562)
- **محدوده دمایی اندازه‌گیری:** between 20.0 and 120.0 °C
- **محدوده طول موج اندازه‌گیری:** اندازه‌گیری در 2.052, 3.3913, 5.2955, و 10.5910 µm
- **واحد:** $(^\circ\text{C}^{-1})$
- **واحد طول موج:** $\lambda$ بر حسب میکرومتر ("where $\lambda$ is in micrometers")

شکل کامل فرمول:
$$\frac{dn_o}{dT} = (0.046\lambda + 7.514) \times 10^{-5}\ (^\circ\text{C}^{-1}),$$

$$\frac{dn_e}{dT} = (0.061\lambda + 7.984) \times 10^{-5}, \quad (2)$$

> [MISMATCH]: در لایه متنی خام PDF، فرمول به صورت `dnoydT 5 ~0.046l 1 7.514! 3 1025~°C21!` استخراج می‌شود که کاملاً مغشوش است. تصویر چاپی نسخه دقیق بالا را تأیید می‌کند.

---

## ۵. جدول‌های عددی

### جدول 1 (Table 1)
- **عنوان:** Table 1. Temperature Phase-Matching Bandwidths (FWHM) for SHG and SFG of the CO2 Laser Frequency at 10.5910 µm in AgGaSe2
- **شماره صفحه PDF:** صفحه 2 (p. 562)

| Type | Wavelength ($\mu\text{m}$)$^\text{a}$: $\lambda_1$ | Wavelength ($\mu\text{m}$)$^\text{a}$: $\lambda_2$ | Wavelength ($\mu\text{m}$)$^\text{a}$: $\lambda_3$ | Phase-Matching Angle (deg)$^\text{b}$ | $\Delta\theta_\text{ext}l$ (deg cm) | $\Delta T l$ ($^\circ\text{C cm}$): Calculated | $\Delta T l$ ($^\circ\text{C cm}$): Observed | Ref. |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SHG** | 10.5910 | 10.5910 | 5.2955 | $\theta_{ooe} = 55.5$ | 2.29 | 351 | 350 | در منبع نیست |
| | | | | | | | 428 | 5 |
| | | | | | | | 364 | 6, 7 |
| | 5.2955 | 5.2955 | 2.6478 | $\theta_{ooe} = 41.3$ | 1.11 | 225 | 230 | در منبع نیست |
| | 5.2955 | 5.2955 | 2.6478 | $\theta_{eoe} = 72.2$ | 3.94 | 254 | 260 | در منبع نیست |
| **SFG** | 10.5910 | 5.2955 | 3.5303 | $\theta_{ooe} = 42.4$ | 1.44 | 390 | 390 | در منبع نیست |
| | 10.5910 | 5.2955 | 3.5303 | $\theta_{eoe} = 56.6$ | 2.41 | 541 | 550 | در منبع نیست |
| | 10.5910 | 3.5303 | 2.6478 | $\theta_{ooe} = 41.3$ | 1.11 | 225 | 220 | در منبع نیست |
| | 10.5910 | 3.5303 | 2.6478 | $\theta_{eoe} = 50.4$ | 1.53 | 257 | 260 | در منبع نیست |

**پانویس‌های جدول 1:**
- $^\text{a} 1/\lambda_1 + 1/\lambda_2 = 1/\lambda_3.$
- $^\text{b} \text{The subscripts of the phase-matching angles represent the polarization directions of the interacting wavelengths, in order. } o \text{ and } e \text{ denote ordinary and extraordinary polarization.}$

---

## ۶. مقادیر عددی تجربی و محاسباتی دیگر در متن
- **ابعاد منشور (صفحه PDF 1):**
  - زاویه راس: $20.00^\circ$ با وتر $10 \times 15\ \text{mm}^2$.
- **مقادیر گزارش‌شده پیشین (صفحه PDF 1):**
  - Barnes et al. [4, 5]: $d[n_o^1 - n_e^2(\theta)]/dT = -1.1 \times 10^{-6}\ ^\circ\text{C}^{-1}$ برای SHG در $10.5910\ \mu\text{m}$
  - Barnes et al.: $d(n_o - n_e)/dT \cong +30 \times 10^{-6}\ ^\circ\text{C}^{-1}$ در $3.3913\ \mu\text{m}$
  - Bhar et al. [6, 7]: $d(n_o - n_e)/dT = -2.6 \times 10^{-6}\ ^\circ\text{C}^{-1}$
- **تصحیحات زاویه و دما (صفحه PDF 2-3):**
  - Bhar et al.: نقطه $10.2604\ \mu\text{m}$ باید خوانده شود $10.2744\ \mu\text{m}$
  - Bhar et al.: نقطه $9.56\ \mu\text{m}$ باید خوانده شود $9.5692\ \mu\text{m}$
  - در 100 K: زاویه تطبیق فاز $\theta_\text{pm} = 55.05^\circ$، $\Delta\theta_\text{pm} = \theta_\text{pm}(298\ \text{K}) - \theta_\text{pm}(100\ \text{K}) = 0.41^\circ$ و $\Delta T l = 428\ ^\circ\text{C cm}$.
- **رسانندگی گرمایی و اثر عدسی گرمایی (صفحه PDF 3):**
  - رسانندگی گرمایی در دمای اتاق: $K_s = 0.011\ \text{W/cm K}$
  - فرمول رسانندگی گرمایی (معادله 4):
    $$K_s = 9.8 \times 10^{-2} T^{-1/2} \exp(\theta/T)\ (\text{W/cm K}), \quad (4)$$
    با دمای دبی $\theta = 193\ \text{K}$.
  - ضریب ترمواپتیک در $2.05\ \mu\text{m}$:
    $$dn_e(\theta = 49.1^\circ)/dT = 7.90 \times 10^{-5}\ ^\circ\text{C}^{-1}$$
  - فاصله کانونی عدسی گرمایی در $21\ ^\circ\text{C}$:
    مقادیر محاسبه‌شده: $f = 3.2\ \text{cm}$ و $f = 25\ \text{cm}$؛
    مقادیر مشاهده‌شده: $f \cong 3.0\ \text{cm}^2$ [?] و $f = (24 \pm 3)\ \text{cm}^3$ [?].
    *(توجه: واحدهای $\text{cm}^2$ و $\text{cm}^3$ عیناً در متن مقاله چاپ شده‌اند و نشان‌دهنده خطای چاپی احتمالی خود مقاله در واحد طول کانونی است)*

---

## ۷. بازخوانی (Proofreading)
- **جدول 1:** تک‌تک ردیف‌ها و ستون‌های Calculated و Observed با تصویر جدول در صفحه PDF 2 سطر به سطر مقایسه شدند. ردیف اول دارای ۳ مقدار تجربی در ستون Observed است (350، 428، 364) که مربوط به مراجع مختلف هستند و با تفکیک سطر ثبت شدند.
- **معادله (1) و (2):** کلیه ارقام و ضرایب اعشاری صورت و مخرج کسرها و جملات چندجمله‌ای با تصویر مقایسه شدند. لایه متنی PDF به طور شدیدی دچار نقص فونت ریاضی بود که با استناد مستقیم به تصویر صفحه به طور کامل برطرف شد.
- **فهرست تفاوتهای پیدا و اصلاح شده:**
  1. در استخراج لایه متن، تمامی علامت‌های مساوی `=` به `5`، علامت‌های منفی `-` به `2` و علامت‌های مثبت `+` به `1` تبدیل شده بودند؛ تمام این خطاها از روی تصویر صفحه تصحیح شدند.
  2. در صفحه ۳ واحد فاصله کانونی عدسی در متن به صورت $\text{cm}^2$ و $\text{cm}^3$ چاپ شده بود که با علامت [?] مشخص شد و حدس زده نشد.
  3. شناسه DOI روی صفحه اول چاپ نشده و «در منبع نیست» درج شد.
