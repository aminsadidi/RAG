# Transcription of mikami2011.pdf

## ۱. مشخصات کتاب‌شناختی (صفحه اول مقاله / PDF Page 2)
- **عنوان:** Sellmeier and thermo-optic dispersion formulas for CsTiOAsO4
- **نویسندگان:** Takuya Mikami,1,2,a) Takayuki Okamoto,2 and Kiyoshi Kato1
- **وابستگی سازمانی (Affiliations):**
  - 1 Chitose Institute of Science and Technology, Bibi 758-65, Chitose, Hokkaido 066-8655, Japan
  - 2 Okamoto Optics Work, Inc., Haramachi 8-34, Isogo-ku, Yokohama, Kanagawa 235-0008, Japan
  - a) Electronic mail: mikami@okamoto-optics.co.jp
- **مجله:** JOURNAL OF APPLIED PHYSICS
- **مشخصات نشر:** 109, 023108 (2011)
- **تاریخ‌ها:** Received 13 September 2010; accepted 10 November 2010; published online 19 January 2011
- **شناسه دیجیتال (DOI):** 10.1063/1.3525800

---

## ۲. محورها و قرارداد نامگذاری
عین جملات مقاله در متن:
- صفحه PDF 2 (Journal page 023108-1):
  > "In order to check the validity of these equations, we have calculated the phase-matching angles for type-2 SHG in the x-y ($\theta=90^\circ$) and y-z ($\phi=90^\circ$) planes for the short and long wavelength range."
- صفحه PDF 4 (Journal page 023108-3):
  > "...our Sellmeier equations having a normal dispersion $n_z > n_y > n_x$ in the whole spectral range."
- صفحه PDF 4 (Journal page 023108-3):
  > "Two right triangle prisms used in this experiment were cut from the same sample that was used for the OPO experiments, and fabricated at apex angles of 30.09° and 29.91° in the x-y plane with the light incident surface being normal to the x or y axis."
- در پانویس جدول I و II:
  > "The superscripts of the interacting wavelengths represent the polarization directions."

---

## ۳. معادلات سلمایر (Sellmeier Equations)

### معادله (1) — CsTiOAsO4 (CTA)
- **شماره معادله:** (1)
- **شماره صفحه PDF:** صفحه 2 (Journal page 023108-1)
- **دمای مرجع:** 20.0 °C (بر اساس متن چکیده و بخش مقدمه: "at 20.0 °C")
- **محدوده طول موج:** $0.5321\ \mu\text{m} \le \lambda \le 3.183\ \mu\text{m}$ (واحد $\lambda$ به میکرومتر است: "where $\lambda$ is in micrometers")

شکل فرمول دقیقاً طبق چاپ:
$$n_x^2 = 1.91529 + \frac{1.47442\lambda^2}{\lambda^2 - 0.03636} + \frac{3.34240\lambda^2}{\lambda^2 - 256.3489}$$

$$n_y^2 = 2.17626 + \frac{1.25709\lambda^2}{\lambda^2 - 0.04516} + \frac{3.57582\lambda^2}{\lambda^2 - 268.5551}$$

$$n_z^2 = 2.46519 + \frac{1.16730\lambda^2}{\lambda^2 - 0.06049} + \frac{3.69079\lambda^2}{\lambda^2 - 278.8889}$$

$$(0.5321\ \mu\text{m} \le \lambda \le 3.183\ \mu\text{m}) \quad (1)$$

> [MISMATCH]: در لایه متنی خام PDF عبارت محدوده به صورت `(0.5321  m       3.183  m )` استخراج می‌شود که نماد $\mu$ و علامت‌های $\le$ و کاما افتاده‌اند، اما در تصویر اسکن‌شده صفحه به وضوح `(0.5321 µm ≤ λ ≤ 3.183 µm),` چاپ شده است. همچنین توان ۲ در $n_x^2$ در لایه متن به سطر بعد رفته است.

---

### پانویس 10 — معادلات سلمایر RbTiOAsO4 (RTA)
- **شماره پانویس:** 10
- **شماره صفحه PDF:** صفحه 5 (Journal page 023108-4)
- **منبع ارجاع:** K. Kato, E. Takaoka, and N. Umemura, Jpn. J. Appl. Phys., Part 1 42, 6420 (2003)
- **متن چاپ‌شده:**
  > "The IR dispersion terms of $n_x$ and $n_y$ were improved. The new formula is expressed as:"

$$n_x^2 = 2.04726 + \frac{1.17229\lambda^2}{\lambda^2 - 0.04063} + \frac{1.31785\lambda^2}{\lambda^2 - 131.0365}$$

$$n_y^2 = 2.12600 + \frac{1.11562\lambda^2}{\lambda^2 - 0.04532} + \frac{1.38410\lambda^2}{\lambda^2 - 134.0264}$$

$$n_z^2 = 2.19499 + \frac{1.29498\lambda^2}{\lambda^2 - 0.05241} + \frac{3.51232\lambda^2}{\lambda^2 - 261.3629}$$

---

## ۴. فرمول‌های ترمواپتیک ($dn/dT$)
- **شماره معادله:** (2)
- **شماره صفحه PDF:** صفحه 5 (Journal page 023108-4)
- **محدوده دمایی اندازه‌گیری:** 20 to 120 °C at temperature intervals of 20 °C (روش انحراف کمینه در محدوده 0.532–1.571 µm)
- **محدوده طول موج فرمول:** $0.5321\ \mu\text{m} \le \lambda \le 2.023\ \mu\text{m}$ (واحد $\lambda$ به میکرومتر: "where $\lambda$ is in micrometers")
- **واحد:** $(^\circ\text{C}^{-1})$

شکل کامل فرمول‌ها:
$$\frac{dn_x}{dT} = \left( \frac{0.3436}{\lambda^3} - \frac{0.4197}{\lambda^2} + \frac{0.3161}{\lambda} + 0.8231 \right) \times 10^{-5}, \quad (^\circ\text{C}^{-1})$$

$$\frac{dn_y}{dT} = \left( \frac{0.5958}{\lambda^3} - \frac{0.8120}{\lambda^2} + \frac{0.6376}{\lambda} + 0.8546 \right) \times 10^{-5},$$

$$\frac{dn_z}{dT} = \left( \frac{1.5170}{\lambda^3} - \frac{2.7879}{\lambda^2} + \frac{2.5353}{\lambda} + 2.5586 \right) \times 10^{-5},$$

$$(0.5321\ \mu\text{m} \le \lambda \le 2.023\ \mu\text{m}) \quad (2)$$

> [MISMATCH]: در لایه متنی خام PDF عبارت $\times 10^{-5}$ و خطوط کسری فرمول به صورت چندخطی نامنظم استخراج می‌شود و علائم توان و بازه به صورت `0.5321  m       2.023  m` درمی‌آید. متن از روی تصویر با فرمول ریاضی فوق تطبیق داده شد.

---

## ۵. جدول‌های عددی

### جدول I (TABLE I)
- **عنوان:** TABLE I. Phase-matching conditions for type-2 OPO, SHG, and SFG in CTA. Note: $1/\lambda_1 + 1/\lambda_2 = 1/\lambda_3$. The superscripts of the interacting wavelengths represent the polarization directions.
- **شماره صفحه PDF:** صفحه 3 (Journal page 023108-2)

| Process | Wavelength $\lambda_1$ ($\mu\text{m}$) | Wavelength $\lambda_2$ ($\mu\text{m}$) | Wavelength $\lambda_3$ ($\mu\text{m}$) | Calculated Phase-matching loci $(\theta, \phi)$: Cheng et al. | Calculated Phase-matching loci $(\theta, \phi)$: Feve et al. | Calculated Phase-matching loci $(\theta, \phi)$: Mikami et al. | Measured Phase-matching loci $(\theta, \phi)$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SHG** | $1.2836^x$ | $1.2836^z$ | $0.6418^x$ | $(85.5^\circ, 90^\circ)$ | $(80.4^\circ, 90^\circ)$ | $(90^\circ, 90^\circ)$ | $(90^\circ, 90^\circ)$ |
| | $1.3188^x$ | $1.3188^{yz}$ | $0.6594^x$ | $(76.4, 90)$ | $(73.7, 90)$ | $(77.4, 90)$ | $(77.4, 90)$<br>$(76.0, 90)^\text{a}$<br>$(73.1, 90)^\text{b}$ |
| | $1.3188^{xy}$ | $1.3188^z$ | $0.6594^{xy}$ | $(90, 63.1)$ | $(90, 62.3)$ | $(90, 66.2)$ | $(90, 66.2)$<br>$(90, 64.3)^\text{c}$<br>$(90, 64.0)^\text{a}$<br>$(90, 59.0)^\text{b}$ |
| | $1.5556^y$ | $1.5556^z$ | $0.7778^y$ | $(86.6, 0)$ | $(90, 10.8)$ | $(90, 0)$ | $(90, 0)$ |
| | $3.183^x$ | $3.183^z$ | $1.5915^x$ | $\cdots$ | $\cdots$ | $(90, 90)$ | $(90, 90)$ |
| **SFG** | $1.3408^x$ | $1.0642^z$ | $0.5933^x$ | $(85.0, 90)$ | $(80.9, 90)$ | $(90, 90)$ | $(90, 90)$ |
| | $1.8645^y$ | $1.0642^{xz}$ | $0.6775^y$ | $(70.7, 0)$ | $(73.8, 0)$ | $(72.5, 0)$ | $(72.4, 0)$ |
| | $1.4437^x$ | $0.8427^z$ | $0.5321^x$ | $\cdots$ | $(81.6, 90)$ | $(90, 90)$ | $(90, 90)$ |
| | $1.9059^{xy}$ | $0.7382^z$ | $0.5321^{xy}$ | $(84.3, 0)$ | $(90, 24.5)$ | $(90, 13.0)$ | $(90, 13.0)$ |
| | $2.023^y$ | $0.722^{xz}$ | $0.5321^y$ | $(77.0, 0)$ | $(90, 8.0)$ | $(79.8, 0)$ | $(80.2, 0)$ |
| **OPO** | $2.4793^z$ | $1.8645^y$ | $1.0642^y$ | $(90, 37.2)$ | $(90, 17.8)$ | $(90, 0)$ | $(90, 0)$ |
| | $1.9365^y$ | $0.7337^z$ | $0.5321^y$ | $(81.7, 0)$ | $(90, 21.1)$ | $(90, 0)$ | $(90, 0)$ |

**پانویس‌های جدول I:**
- $^\text{a}\text{Reference 7.}$ (L. T. Cheng, L. K. Cheng, and J. D. Bierlein, Proc. SPIE 1863, 43 (1993).)
- $^\text{b}\text{Reference 8.}$ (B. Boulanger, J. P. Feve, G. Marnier, G. M. Loiacono, D. N. Loiacono, and C. Bonnin, IEEE J. Quantum Electron. 33, 945 (1997).)
- $^\text{c}\text{Reference 4.}$ (L. T. Cheng, L. K. Cheng, J. D. Bierlein, and F. C. Zumsteg, Appl. Phys. Lett. 63, 2618 (1993).)

---

### جدول II (TABLE II)
- **عنوان:** TABLE II. Temperature phase-matching bandwidths (FWHM) for type-2 SHG and SFG in CTA. Note: $1/\lambda_1 + 1/\lambda_2 = 1/\lambda_3$. The superscripts of the interacting wavelengths represent the polarization directions.
- **شماره صفحه PDF:** صفحه 4 (Journal page 023108-3)

| Process | Wavelength $\lambda_1$ ($\mu\text{m}$) | Wavelength $\lambda_2$ ($\mu\text{m}$) | Wavelength $\lambda_3$ ($\mu\text{m}$) | Phase-matching loci $(\theta, \phi)$: Measured | Phase-matching loci $(\theta, \phi)$: Calculated | Angular acceptance | $\Delta T \cdot \ell$ ($^\circ\text{C cm}$): Measured | $\Delta T \cdot \ell$ ($^\circ\text{C cm}$): Calculated |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SHG** | $1.2836^x$ | $1.2836^z$ | $0.6418^x$ | $(90^\circ, 90^\circ)$ | $(90^\circ, 90^\circ)$ | $\Delta\theta_\text{ext}\cdot \ell^{1/2} = 4.8$<br>$\Delta\phi_\text{ext}\cdot \ell^{1/2} = 8.8$<br>$(\text{deg cm}^{1/2})$ | $8.4^\text{a}$ | $8.5$ |
| | $1.3188^x$ | $1.3188^{yz}$ | $0.6594^x$ | $(77.4, 90)$ | $(77.4, 90)$ | $\Delta\theta_\text{ext}\cdot \ell = 9.0\ (\text{mrad cm})$ | $8.9$ | $8.9$ |
| | $1.3188^{xy}$ | $1.3188^z$ | $0.6594^{xy}$ | $(90, 66.2)$ | $(90, 66.2)$ | $\Delta\phi_\text{ext}\cdot \ell = 17.9\ (\text{mrad cm})$ | $9.0$ | $8.9$ |
| | $1.5556^y$ | $1.5556^z$ | $0.7778^y$ | $(90, 0)$ | $(90, 0)$ | $\Delta\theta_\text{ext}\cdot \ell^{1/2} = 4.8$<br>$\Delta\phi_\text{ext}\cdot \ell^{1/2} = 10.3$<br>$(\text{deg cm}^{1/2})$ | $11.1^\text{a}$ | $10.4$ |
| **SFG** | $1.3408^x$ | $1.0642^z$ | $0.5933^x$ | $(90, 90)$ | $(90, 90)$ | $\Delta\theta_\text{ext}\cdot \ell^{1/2} = 4.3$<br>$\Delta\phi_\text{ext}\cdot \ell^{1/2} = 7.9$<br>$(\text{deg cm}^{1/2})$ | $7.5^\text{a}$ | $7.5$ |
| | $1.9059^{xy}$ | $0.7382^z$ | $0.5321^{xy}$ | $(90, 13.0)$ | $(90, 13.0)$ | $\Delta\phi_\text{ext}\cdot \ell = 14.5\ (\text{mrad cm})$ | $7.2$ | $8.6$ |
| | $2.023^y$ | $0.722^{xz}$ | $0.5321^y$ | $(80.2, 0)$ | $(79.8, 0)$ | $\Delta\theta_\text{ext}\cdot \ell = 4.5\ (\text{mrad cm})$ | $11.1$ | $8.6$ |

**پانویس جدول II:**
- $^\text{a}\text{Measured by } d\lambda_1/dT.$

---

## ۶. بخش‌های عددی دیگر در متن مقاله
- **ضریب غیرخطی (صفحه PDF 5):**
  > "$d_{32}(1.064\ \mu\text{m}) = 3.4 \pm 0.7\ \text{pm/V}$" (ارجاع به مرجع 4 Cheng et al.)
- **پهنای پذیرش زاویه‌ای و دمایی در $0.775\ \mu\text{m}$ (صفحه PDF 5):**
  > "$\Delta T \cdot \ell \cong 10\ ^\circ\text{C cm}$"
  > "$\Delta\theta_\text{ext}\cdot \ell^{1/2} = 4.7\ \text{deg cm}^{1/2}$"
  > "$\Delta\phi_\text{ext}\cdot \ell^{1/2} = 10.1\ \text{deg cm}^{1/2}$"
- **طول موج‌های OPO با پمپ Nd:YAG در $20.0\ ^\circ\text{C}$ (صفحه PDF 2):**
  > پمپ $1.0642\ \mu\text{m}$: $\lambda_s = 1.8645\ \mu\text{m}$ و $\lambda_i = 2.4793\ \mu\text{m}$
  > پمپ SHG ($0.5321\ \mu\text{m}$): $\lambda_s = 0.7337\ \mu\text{m}$ و $\lambda_i = 1.9365\ \mu\text{m}$
- **طول موج SHG در $90^\circ$ با پمپ KTP/OPO در امتداد محور y (صفحه PDF 2):**
  > $\lambda = 1.2836\ \mu\text{m}$ و $\lambda = 3.1830\ \mu\text{m}$
- **طول موج قطع SHG (صفحه PDF 3):**
  > اندازه و محاسبه نویسندگان: $1.5915\ \mu\text{m}$
  > محاسبه با فرمول Cheng et al.: $\lambda_2 = 1.4734\ \mu\text{m}$
  > محاسبه با فرمول Feve et al.: $1.5498\ \mu\text{m}$

---

## ۷. بازخوانی (Proofreading)
- **مقایسه جدول I:** کل ۱۲ ردیف جدول و مقادیر طول‌موج، زوایای محاسبه‌شده Cheng، Feve، Mikami و مقادیر تجربی مجدداً با تصویر اصلی صفحه ۳ (PDF Page 3) سطر به سطر تطبیق داده شد. مقادیر خط تیره (سه نقطه `...`) در دو ردیف دقیقاً منعکس شد. هیچ مغایرتی باقی نماند.
- **مقایسه جدول II:** تمام ۷ ردیف جدول و مقادیر ستون‌های Angular acceptance و پهنای باند دمایی ($\Delta T \cdot \ell$) با تصویر اصلی صفحه ۴ (PDF Page 4) تطبیق داده شد. توان‌های $\ell^{1/2}$ و نمادهای $\Delta\theta_\text{ext}$ و $\Delta\phi_\text{ext}$ که در متن خام لایه PDF به صورت متنی نامفهوم درآمده بودند، کاملاً اصلاح و درج شدند.
- **معادلات (1) و (2):** تک‌تک ضرایب اعشاری صورت و مخرج کسرها و توان‌ها با تصویر بزرگ‌نمایی‌شده معادله (1) در صفحه 2 و معادله (2) در صفحه 5 بازبینی شدند؛ کلیه ارقام و علامت‌های منفی و مثبت دقیقاً برابر نسخه چاپی است.
- **فهرست تفاوتهای پیدا و اصلاح شده:**
  1. در استخراج خام لایه متن، نماد میکرومتر ($\mu\text{m}$) در انتهای معادله (1) و (2) حذف شده بود که از روی تصویر صفحه اصلاح شد.
  2. در استخراج خام لایه متن، عبارت‌های توان‌دار پذیرش زاویه‌ای در جدول II مانند $\Delta\theta_\text{ext}\cdot \ell^{1/2}$ به صورت `ext· 1/2` درآمده بودند که با تصویر چاپ‌شده تطبیق و تصحیح شدند.
  3. در جدول I، پانویس‌های چندگانه ردیف‌های ۲ و ۳ (اندازه‌گیری‌شده‌ها توسط مراجع ۴، ۷ و ۸) با تفکیک کامل و علائم پانویس ثبت شدند.
