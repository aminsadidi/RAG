# Transcription of loiko2015.pdf

## ۱. مشخصات کتاب‌شناختی (صفحه اول مقاله / PDF Page 1)
- **عنوان:** Thermo-optic dispersion formulas for YCOB and GdCOB laser host crystals
- **نویسندگان:** Pavel Loiko,1 Xavier Mateos,2,* Yicheng Wang,3 Zhongben Pan,4 Konstantin Yumashev,1 Huaijin Zhang,5 Uwe Griebner,3 and Valentin Petrov3
- **وابستگی سازمانی (Affiliations):**
  - 1 Center for Optical Materials and Technologies, Belarusian National Technical University, 65/17 Nezavisimosti Ave., 220013 Minsk, Belarus
  - 2 Física i Cristal·lografia de Materials i Nanomaterials (FiCMA-FiCNA), Universitat Rovira i Virgili (URV), Campus Sescelades, c/ Marcel·lí Domingo, s/n., Tarragona, E-43007 Spain
  - 3 Max Born Institute for Nonlinear Optics and Short Pulse Spectroscopy, Max-Born-Str. 2a, D-12489 Berlin, Germany
  - 4 Institute of Chemical Materials and Advanced Materials Center, China Academy of Engineering Physics, Mianyang 621900, China
  - 5 State Key Laboratory of Crystal Materials and Institute of Crystal Materials, Shandong University, Jinan 250100, China
  - * xavier.mateos@urv.cat
- **مجله:** OPTICAL MATERIALS EXPRESS
- **مشخصات نشر:** Vol. 5, No. 5, pp. 1089–1097 (2015)
- **تاریخ‌ها:** Received 27 Jan 2015; revised 31 Mar 2015; accepted 3 Apr 2015; published 15 Apr 2015
- **شناسه دیجیتال (DOI):** 10.1364/OME.5.001089

---

## ۲. محورها و قرارداد نامگذاری
بلورهای مونوکلینیک تک‌محور-نوری دو‌محوره (Biaxial monoclinic crystals).
عین جملات مقاله در متن:
- صفحه PDF 6 (OME Vol. 5, p. 1094):
  > "For a monoclinic crystal, the orientation of the optical indicatrix axes is constrained by the crystal symmetry. There are three point groups corresponding to the monoclinic crystal class, namely 2, m and 2/m (Hermann–Mauguin notations) where 2 stands for a two-fold axis ($C_2$) and m for a mirror plane. A “monoclinic” axis is selected for each point group. This axis is parallel to the two-fold axis for 2 and 2/m groups and it is perpendicular to the mirror plane for m and 2/m groups. The usual convention is to denote the monoclinic axis as the crystallographic b-axis while the angle $\beta = a\wedge c$ between the a and c axes located in the orthogonal plane is $> 90^\circ$, see Fig. 1. The orientation of only one of the principal axes of the optical indicatrix is constrained to be parallel to the b-axis. However, as the notations for the axes of the optical indicatrix are determined from the relation for the refractive indices ($n_X < n_Y < n_Z$), any of the X, Y or Z axes may happen to be parallel to the monoclinic axis. It was shown for monoclinic crystals that the values of n depend mainly on the electronic polarizabilities of the species occupying the sites, i.e. mainly on the chemical crystal composition [29]. As a result, indeed all three cases ($b \parallel X$, $Y$ or $Z$) are possible for such crystals [30]."
  > برای این دو بلور: محور نوری $Y$ منطبق بر محور کریستالوگرافی $b$ است ($b \parallel Y$).
- صفحه PDF 4 (OME Vol. 5, p. 1092):
  > "The three possible light propagation directions along the X, Y or Z axes (denoted further as X-, Y- or Z-cut) alongside the two possible principal polarizations yield a total of 6 TCOP values."
  > "The principal TOCs, $dn_X/dT$, $dn_Y/dT$ and $dn_Z/dT$, were determined from the corresponding TCOP values, $dn/dT = W - (n-1)\alpha$; the refractive indices n were calculated from Sellmeier equations [9,15]."

---

## ۳. معادلات سلمایر (Sellmeier Equations)
- **وضعیت در مقاله:** مقاله فرمول سلمایر جدیدی ارائه نکرده است، بلکه ضرایب شکست $n$ را برای محاسبه $dn/dT$ از معادلات سلمایر مراجع [9] و [15] اخذ کرده است:
  > صفحه PDF 4: "...the refractive indices n were calculated from Sellmeier equations [9,15]."
  - مرجع 9: فرمول سلمایر ارائه شده توسط Kato و Umemura
  - مرجع 15: P. Segonds, B. Boulanger, B. Menaert, J. Zaccaro, J. P. Salvestrini, M. D. Fontana, R. Moncorge, F. Poree, G. Gadret, J. Mangin, A. Brenier, G. Boulon, G. Aka, and D. Pelenc, “Optical characterizations of YCa4O(BO3)3 and Nd:YCa4O(BO3)3 crystals,” Opt. Mater. 29(8), 975–982 (2007).

---

## ۴. فرمول‌های ترمواپتیک ($dn/dT$) و TCOP

### مدل فیزیکی نیمه‌تجربی — معادله (1)
- **شماره معادله:** (1)
- **شماره صفحه PDF:** صفحه 7 (p. 1095)
- **شکل کامل فرمول:**
$$\frac{dn}{dT} = -\alpha_\text{vol} \frac{(n_\infty^2 - 1)}{2n(\lambda)} \frac{\lambda^2}{\lambda^2 - \lambda_g^2} - \frac{1}{E_g} \frac{dE_g}{dT} \frac{(n_\infty^2 - 1)}{2n(\lambda)} \left( \frac{\lambda^2}{\lambda^2 - \lambda_g^2} \right)^2 \quad (1)$$

- **پارامترها و ضرایب طبق متن صفحه 7:**
  - $\lambda$: طول‌موج بر حسب میکرومتر ($\mu\text{m}$)
  - $\lambda_g\ [\mu\text{m}] = 1.2398 / E_g\ [\text{eV}]$
  - $n(\lambda)$: معادله سلمایر
  - $n_\infty$: ضریب شکست در حد فروسرخ طول‌موج بلند
  - $\alpha_\text{vol}$: انبساط حرارتی حجمی:
    - برای YCOB برابر $20.8 \times 10^{-6}\ \text{K}^{-1}$
    - برای GdCOB برابر $22.4 \times 10^{-6}\ \text{K}^{-1}$
  - $E_g = 5.4 \pm 0.1\ \text{eV}$
  - $dE_g/dT = -1.0 \pm 0.3 \times 10^{-4}\ \text{eV/K}$

---

### فرمول پاشش ترمواپتیک تحلیلی (Analytical Thermo-Optic Dispersion Formula) — معادله (2)
- **شماره معادله:** (2)
- **شماره صفحه PDF:** صفحه 7 (p. 1095)
- **محدوده طول موج معتبر:** $0.4\ \mu\text{m} \le \lambda \le 2\ \mu\text{m}$ (طبق متن چکیده و صفحه 7)
- **دمای مرجع:** دمای اتاق (room-temperature، حدود 20 °C تا 25 °C، اختلاف دمای اعمالی 20 °C سرد تا 50 °C گرم با گرادیان 6–8 °C/mm)
- **شکل فرمول:**
$$\frac{dn}{dT} = A_0 + \frac{A_1}{\lambda^2} + \frac{A_2}{\lambda^4} + \frac{A_3}{\lambda^6}, \quad 10^{-6}\ \text{K}^{-1}. \quad (2)$$

"Here $\lambda$ is in $\mu\text{m}$; $A_{0-3}$ are the expansion coefficients ($A_0$ corresponds to the dn/dT value in the long-wavelength limit, $A_{1-3}$ represent its dispersion)."

ضرایب در جدول 4 ارائه شده‌اند.

---

### فرمول‌های جهت‌های بی‌حرارت (Athermal Directions) — معادلات (3a) و (3b)
- **شماره معادلات:** (3a) و (3b)
- **شماره صفحه PDF:** صفحه 8 (p. 1096)
$$W_{Y-Z} = \frac{dn_X}{dT} + (n_X - 1) [\alpha_Y \cos^2\theta + \alpha_Z \sin^2\theta], \quad (3\text{a})$$

$$W_{X-Y} = \frac{dn_Z}{dT} + (n_Z - 1) [\alpha_Y \cos^2\theta + \alpha_X \sin^2\theta]. \quad (3\text{b})$$

---

## ۵. جدول‌های عددی

### جدول 1 (Table 1)
- **عنوان:** Table 1. Thermal Expansion Coefficients for YCOB and GdCOB Crystals
- **شماره صفحه PDF:** صفحه 4 (p. 1092)

| Crystal | Thermal expansion, $10^{-6}\ \text{K}^{-1}$: $\alpha_X$ | Thermal expansion, $10^{-6}\ \text{K}^{-1}$: $\alpha_c$ | Thermal expansion, $10^{-6}\ \text{K}^{-1}$: $\alpha_Y = \alpha_b$ | Thermal expansion, $10^{-6}\ \text{K}^{-1}$: $\alpha_Z$ | Thermal expansion, $10^{-6}\ \text{K}^{-1}$: $\alpha_a$ | Ref. |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| YCOB | 12.0 | در منبع نیست | 2.6 | 6.2 | در منبع نیست | This paper |
| | 12.6 | در منبع نیست | 4.1 | 7.5 | در منبع نیست | [15] |
| | در منبع نیست | 12.8 | 8.2 | در منبع نیست | 9.9 | [13] |
| Nd:YCOB | 10.9 | در منبع نیست | 4.2 | 5.9 | در منبع نیست | [24] |
| | 12.1 | در منبع نیست | 4.4 | 7.7 | در منبع نیست | [15] |
| GdCOB | 11.1 | در منبع نیست | 3.6 | 7.7 | در منبع نیست | This paper |
| | در منبع نیست | 14.3 | 8.3 | در منبع نیست | 10.2 | [12] |
| | در منبع نیست | 13.1 | 7.8 | در منبع نیست | 10.4 | [25] |
| Nd:GdCOB | 11.6 | در منبع نیست | 5.4 | 5.9 | در منبع نیست | [24] |

---

### جدول 2 (Table 2)
- **عنوان:** Table 2. Anisotropy of Thermal Coefficients of the Optical Path (TCOP) for YCOB and GdCOB Crystals at 1.06 μm
- **شماره صفحه PDF:** صفحه 5 (p. 1093)

| Crystal | Orientation | TCOP, $10^{-6}\ \text{K}^{-1}$: $E \parallel X$ | TCOP, $10^{-6}\ \text{K}^{-1}$: $E \parallel Y$ | TCOP, $10^{-6}\ \text{K}^{-1}$: $E \parallel Z$ |
| :--- | :--- | :--- | :--- | :--- |
| YCOB | X-cut | – | +4.5 | +5.9 |
| | Y-cut | +0.6 | – | –0.8 |
| | Z-cut | +2.9 | +0.5 | – |
| GdCOB | X-cut | – | +3.0 | +4.2 |
| | Y-cut | –1.4 | – | –1.1 |
| | Z-cut | +1.4 | +0.6 | – |

---

### جدول 3 (Table 3)
- **عنوان:** Table 3. Thermo-Optic Coefficients (TOC) for YCOB and GdCOB Crystals
- **شماره صفحه PDF:** صفحه 6 (p. 1094)

| Crystal | $\text{TOC}^*$, $10^{-6}\ \text{K}^{-1}$: $dn_X/dT$ | $\text{TOC}^*$, $10^{-6}\ \text{K}^{-1}$: $dn_Y/dT$ | $\text{TOC}^*$, $10^{-6}\ \text{K}^{-1}$: $dn_Z/dT$ |
| :--- | :--- | :--- | :--- |
| YCOB | –1.2 | –3.7 | –2.5 |
| GdCOB | –3.8 | –4.8 | –3.7 |

| Crystal | $d\Delta/dT^{**}$, $10^{-6}\ \text{K}^{-1}$: $d\Delta_{XY}/dT$ | $d\Delta/dT^{**}$, $10^{-6}\ \text{K}^{-1}$: $d\Delta_{XZ}/dT$ | $d\Delta/dT^{**}$, $10^{-6}\ \text{K}^{-1}$: $d\Delta_{YZ}/dT$ |
| :--- | :--- | :--- | :--- |
| YCOB | 2.5 | 1.3 | 1.2 |
| GdCOB | 1.0 | 0.1 | 1.1 |

**پانویس‌های جدول 3:**
- $^*\text{At } \sim 1\ \mu\text{m};$
- $^{**}d\Delta/dT\text{ is the thermal coefficient of birefringence.}$

---

### جدول 4 (Table 4)
- **عنوان:** Table 4. Coefficients in the Thermo-Optic Dispersion Formulas for YCOB and GdCOB Crystals, Eq. (2)
- **شماره صفحه PDF:** صفحه 7 (p. 1095)

| Crystal | TOC | $A_0$ | $A_1$, $\mu\text{m}^2$ | $A_2$, $\mu\text{m}^4$ | $A_3$, $\mu\text{m}^6$ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **YCOB** | $dn_X/dT$ | –1.5 | 0.3290 | 0.0137 | 0.0027 |
| | $dn_Y/dT$ | –3.9 | 0.2483 | –0.0063 | 0.0059 |
| | $dn_Z/dT$ | –2.8 | 0.3006 | 0.0027 | 0.0044 |
| **GdCOB** | $dn_X/dT$ | –4.1 | 0.1937 | 0.0087 | 0.0034 |
| | $dn_Y/dT$ | –5.0 | 0.1808 | –0.0082 | 0.0077 |
| | $dn_Z/dT$ | –4.0 | 0.2243 | 0.0058 | 0.0043 |

---

### جدول 5 (Table 5)
- **عنوان:** Table 5. Athermal Directions (ADs) in YCOB and GdCOB Crystals at ~1 µm
- **شماره صفحه PDF:** صفحه 8 (p. 1096)

| Crystal | Polarization (plane): $E \parallel X$ (Y-Z plane) | Polarization (plane): $E \parallel Y$ (X-Z plane) | Polarization (plane): $E \parallel Z$ (X-Y plane) |
| :--- | :--- | :--- | :--- |
| YCOB | – | ~Z-axis | $Y \pm 27.4^\circ$ |
| GdCOB | $Y \pm 43.5^\circ$ | ~Z-axis | $Y \pm 18.2^\circ$ |

---

## ۶. مقادیر عددی تجربی دیگر در متن
- **طول موج‌های لیزرهای پروب (صفحه PDF 4):**
  - 400, 532, 633, 652, 780, 980 و 1064 nm (توان کمتر از 10 mW)
- **رسانندگی گرمایی GdCOB (صفحه PDF 4):**
  - $\kappa_X = 2.17\ \text{W/mK}$, $\kappa_Y = 1.32\ \text{W/mK}$, $\kappa_Z = 2.40\ \text{W/mK}$ (مرجع [12])
- **عدم قطعیت تجربی TOC (صفحه PDF 4):**
  - انحراف از $0.3 \times 10^{-6}\ \text{K}^{-1}$ تجاوز نمی‌کند.
- **مقادیر TOC در ~1 µm (صفحه PDF 5):**
  - YCOB: $dn_X/dT = -1.2 \times 10^{-6}\ \text{K}^{-1}$، $dn_Y/dT = -3.7 \times 10^{-6}\ \text{K}^{-1}$، $dn_Z/dT = -2.5 \times 10^{-6}\ \text{K}^{-1}$
  - GdCOB: $dn_X/dT = -3.8 \times 10^{-6}\ \text{K}^{-1}$، $dn_Y/dT = -4.8 \times 10^{-6}\ \text{K}^{-1}$، $dn_Z/dT = -3.7 \times 10^{-6}\ \text{K}^{-1}$

---

## ۷. بازخوانی (Proofreading)
- **جدول‌های 1 تا 5:** کلیه سلول‌ها، ردیف‌ها و ستون‌ها با تصاویر مستقیم صفحات ۴، ۵، ۶، ۷ و ۸ در فایل PDF بازخوانی شدند.
- **علامت‌های منفی:** در جدول‌های 2، 3 و 4 علامت‌های منفی به دقت با تصویر صفحه تطبیق داده شدند (به‌خصوص ضرایب منفی $A_0$ در تمام ردیف‌های جدول 4 و ضرایب منفی $A_2$ در سطر دوم YCOB و سطر دوم GdCOB).
- **ستون‌های خالی:** در جدول 1 ستون‌های فاقد مقدار برای برخی مراجع با «در منبع نیست» مشخص شدند. در جدول‌های 2 و 5 خط تیره‌ها (–) که نشان‌دهنده عدم امکان فیزیکی یا انتشار در راستای قطبش است دقیقاً طبق چاپ حفظ شدند.
- **فهرست تفاوتهای پیدا و اصلاح شده:**
  1. در استخراج لایه متن در جدول 4 علامت منفی ضریب $A_0$ و $A_2$ در برخی خطوط جابه‌جا یا نامنظم دیده می‌شد؛ از روی تصویر تأیید شد که تمام ۶ ضریب $A_0$ منفی هستند، و ضریب $A_2$ فقط برای $dn_Y/dT$ در هر دو بلور منفی است (–0.0063 و –0.0082) و بقیه مثبت هستند.
  2. معادله (2) واحد $10^{-6}\ \text{K}^{-1}$ در انتهای فرمول دارد که به صراحت در متن و سرستون جدول 4 منعکس شده است.
