# رونویسی بخش GdCa4O(BO3)3 (Gadolinium Calcium Oxyborate, GdCOB) از کتاب Nikogosyan (2005)

**منبع:**
- کتاب: *Nonlinear Optical Crystals: A Complete Survey*, David N. Nikogosyan, Springer, 2005.
- فصل: Chapter 6: *Newly Developed and Perspective Crystals*
- بخش: Section 6.6: *GdCa4O(BO3)3, Gadolinium Calcium Oxyborate (GdCOB)*
- صفحات کتاب: 227–233
- صفحات فایل PDF: صص ۲۳۵–۲۴۱ (235–241)

---

## ۱. ساختار بلوری، گروه نقطه‌ای و قرارداد محورها (Point Group & Axis Convention)
*(صفحات کتاب: 227–228، صفحات PDF: 235–236)*

- Negative biaxial crystal: $2V_Z = 120.7^\circ$ at $\lambda = 0.546\ \mu\text{m}$ [1], [2]
- Molecular mass: 509.986
- Specific gravity: $3.736\text{ g/cm}^3$ (calculated) [3]
- Point group: $m$
- Lattice constants:
  - $a = 8.106 \pm 0.002\text{ \AA}$ [1]; $8.095 \pm 0.007\text{ \AA}$ [4]; $8.0937\text{ \AA}$ [5]; $8.098 \pm 0.002\text{ \AA}$ [6]
  - $b = 16.028 \pm 0.003\text{ \AA}$ [1]; $16.018 \pm 0.006\text{ \AA}$ [4]; $16.013\text{ \AA}$ [5]; $16.019 \pm 0.006\text{ \AA}$ [6]
  - $c = 3.557 \pm 0.001\text{ \AA}$ [1]; $3.558 \pm 0.008\text{ \AA}$ [4]; $3.5579\text{ \AA}$ [5]; $3.559 \pm 0.007\text{ \AA}$ [6]
  - $\beta = 101.25^\circ$ [1]; $101.26^\circ \pm 0.01^\circ$ [4]; $101.27^\circ$ [5], [6]
- Assignment of dielectric and crystallographic axes:
  > "Y∥b, the axes a and c lie in XZ plane, the angle between them is $\beta = 101.27^\circ$, the angle between the axes Z and a is $27.2^\circ$, the angle between the axes X and c is $16.2^\circ$ [7], [8]. A slightly different assignment: (a, Z) = $26^\circ$, (c, X) = $15^\circ$, was reported earlier [1], [2]."
- Mohs hardness: 6.5 [9]
- Knoop hardness: 550–715 kg/mm$^2$ [2]
- Melting point: 1753 K [4], [5]; 1756 K (congruent melting) [10]

---

## ۲. ضرایب غیرخطی مرتبهٔ دوم ($d_{il}$)
*(صفحهٔ کتاب: 230، صفحهٔ PDF: 238)*

Most reliable experimental values of second-order nonlinear coefficients:
- $d_{11}(1.0642\ \mu\text{m}) = 0$ [17]
- $d_{12}(1.0642\ \mu\text{m}) = 0.24\text{ pm/V}$ [18]; $0.27\text{ pm/V}$ [17]; $0.31\text{ pm/V}$ [19]
- $d_{13}(1.0642\ \mu\text{m}) = -0.74\text{ pm/V}$ [18]; $-0.85\text{ pm/V}$ [17]; $-0.87\text{ pm/V}$ [19]
- $d_{31}(1.0642\ \mu\text{m}) = 0.20\text{ pm/V}$ [17]
- $d_{32}(1.0642\ \mu\text{m}) = 2.23\text{ pm/V}$ [17]; $2.26\text{ pm/V}$ [19]; $2.39\text{ pm/V}$ [18]
- $d_{33}(1.0642\ \mu\text{m}) = -1.87\text{ pm/V}$ [17]

### روابط ضریب غیرخطی مؤثر در صفحات اصلی بلور GdCOB
*(تقریب زاویه واگرایی کوچک (small walk-off angle)، با برقراری شرایط تقارن کلاینمن: $d_{12} = d_{26}$, $d_{13} = d_{35}$, $d_{15} = d_{31}$, $d_{24} = d_{32}$) [2], [17]:*
*(صفحهٔ کتاب: 229، صفحهٔ PDF: 237)*

- XY plane, $\theta = 90^\circ$:
  $$d_{ooe} = d_{13} \sin \phi$$
  $$d_{eoe} = d_{oee} = d_{31} \sin^2 \phi + d_{32} \cos^2 \phi$$
- YZ plane, $\phi = 90^\circ$:
  $$d_{eeo} = d_{13} \sin^2 \theta + d_{12} \cos^2 \theta$$
  $$d_{oeo} = d_{eoo} = d_{31} \sin \theta$$
- XZ plane, $\phi = 0^\circ$, $V_z > \theta > 0^\circ$:
  $$d_{ooe} = d_{12} \cos \theta - d_{32} \sin \theta$$
- XZ plane, $\phi = 0^\circ$, $90^\circ > \theta > V_z$:
  $$d_{oeo} = d_{eoo} = d_{12} \cos \theta - d_{32} \sin \theta$$
- XZ plane, $\phi = 0^\circ$, $180^\circ - V_z > \theta > 90^\circ$; or $\phi = 180^\circ$, $90^\circ > \theta > V_z$:
  $$d_{oeo} = d_{eoo} = d_{12} \cos \theta + d_{32} \sin \theta$$
- XZ plane, $\phi = 0^\circ$, $180^\circ > \theta > 180^\circ - V_z$; or $\phi = 180^\circ$, $V_z > \theta > 0^\circ$:
  $$d_{ooe} = d_{12} \cos \theta + d_{32} \sin \theta$$

---

## ۳. معادلات سلمایر (Sellmeier Equations)
*(صفحهٔ کتاب: 229، صفحهٔ PDF: 237)*

Best set of Sellmeier equations ($T = 293\text{ K}$, $\lambda$ in $\mu\text{m}$, $0.4129\ \mu\text{m} < \lambda < 1.3382\ \mu\text{m}$) [14]:

$$n_X^2 = 2.8063 + \frac{0.02315}{\lambda^2 - 0.01378} - 0.00537 \lambda^2$$

$$n_Y^2 = 2.8959 + \frac{0.02398}{\lambda^2 - 0.01389} - 0.01132 \lambda^2$$

$$n_Z^2 = 2.9248 + \frac{0.02410}{\lambda^2 - 0.01406} - 0.01139 \lambda^2$$

متن کتاب:
> "Other sets of dispersion relations are given in [1], [2], [5], [8], [15]."

---

## ۴. روابط پاشندگی وابسته به دما و فرمول‌های ترمواپتیک ($dn/dT$)
در منبع نیست (فرمول صریح یا جدول عددی $dn/dT$ در بخش 6.6 کتاب Nikogosyan برای بلور GdCOB ارائه نشده است).

---

## ۵. جدول‌های عددی متن کتاب

### جدول ۱: مقدار میانگین ضریب انبساط حرارتی خطی (Mean value of linear thermal expansion coefficient)
*(صفحهٔ کتاب: 228، صفحهٔ PDF: 236)*

| $T$ [K] | $\alpha_t \times 10^6$ [K$^{-1}$], $\parallel a$ | $\alpha_t \times 10^6$ [K$^{-1}$], $\parallel b$ | $\alpha_t \times 10^6$ [K$^{-1}$], $\parallel c$ | Ref. |
| :--- | :--- | :--- | :--- | :--- |
| 293–1133 | 10.2 | 8.3 | 14.3 | [11] |
| 293–1273 | 10.35 | 7.78 | 13.10 | [6] |

### جدول ۲: ضریب هدایت حرارتی در دمای $T = 293\text{ K}$ (Thermal conductivity coefficient at T = 293 K)
*(صفحهٔ کتاب: 228، صفحهٔ PDF: 236)*

| $T$ [K] | $\kappa$ [W/mK], $\parallel X$ | $\kappa$ [W/mK], $\parallel Y$ | $\kappa$ [W/mK], $\parallel Z$ | Ref. |
| :--- | :--- | :--- | :--- | :--- |
| 287 | 2.173 | | | [12] |
| 289 | | 2.401 | | [12] |
| 291 | | | 1.32 | [12] |
| 293 | 2.54 | 1.32 | 2.06 | [9] |
| 297 | 2.539 | | | [12] |
| 324 | 2.227 | | | [12] |
| 345 | 1.880 | | | [12] |
| 353 | | | 2.016 | [12] |
| 394 | 1.799 | | | [12] |
| 403 | | | 1.22 | [12] |
| 424 | 2.237 | | | [12] |
| 445 | 1.807 | | | [12] |
| 474 | 2.277 | | | [12] |
| 496 | 1.852 | | | [12] |
| 525 | 1.789 | | | [12] |
| 526 | | 2.009 | | [12] |
| 545 | | | 1.18 | [12] |

### سایر ویژگی‌های اپتیکی
*(صفحهٔ کتاب: 228، صفحهٔ PDF: 236)*
- High transmittance range: $0.32–2.6\ \mu\text{m}$ [13]
- In the UV transparency range $0.2–0.32\ \mu\text{m}$ there are three groups of sharp absorption lines centered around 0.25, 0.277, and $0.31\ \mu\text{m}$ [2].
- In the IR transparency range $2.6–3.7\ \mu\text{m}$ there are absorption bands at 2.72, 2.9, and $3.25\ \mu\text{m}$ [2], [13].

### جدول ۳: مقادیر تجربی ضرایب شکست (Experimental values of refractive indices) [2]
*(صفحهٔ کتاب: 229، صفحهٔ PDF: 237)*

| $\lambda$ [$\mu$m] | $n_X$ | $n_Y$ | $n_Z$ | $\lambda$ [$\mu$m] | $n_X$ | $n_Y$ | $n_Z$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0.4047 | 1.7209 | 1.7476 | 1.7563 | 0.5780 | 1.6966 | 1.7225 | 1.7310 |
| 0.4358 | 1.7142 | 1.7409 | 1.7493 | 0.5876 | 1.6960 | 1.7218 | 1.7303 |
| 0.4678 | 1.7089 | 1.7350 | 1.7436 | 0.6439 | 1.6923 | 1.7181 | 1.7265 |
| 0.4800 | 1.7068 | 1.7333 | 1.7418 | 0.6678 | 1.6910 | 1.7168 | 1.7250 |
| 0.5086 | 1.7033 | 1.7295 | 1.7379 | 0.7290 | 1.6879 | 1.7133 | 1.7216 |
| 0.5461 | 1.6992 | 1.7253 | 1.7340 | 0.7960 | 1.6860 | 1.7112 | 1.7197 |

### جدول ۴: ضرایب الکترواپتیک خطی اندازه‌گیری‌شده در بسامدهای پایین (بلور آزاد) در دمای اتاق (برحسب pm/V) [16]
*(صفحهٔ کتاب: 229، صفحهٔ PDF: 237)*
Linear electrooptic coefficients measured at low frequencies (well below the acoustic resonances of GdCOB crystal, i.e., for the “free” crystal) at room temperature (in pm/V) [16]:

| $\lambda$ [$\mu$m] | $r^T_{11}$ | $r^T_{21}$ | $r^T_{31}$ | $r^T_{13}$ | $r^T_{23}$ | $r^T_{33}$ | $r^T_{51}$ | $r^T_{53}$ | $r^T_{42}$ | $r^T_{62}$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0.6328 | 0.4 | 0.5 | 0.6 | 0.1 | 0.4 | 2.0 | 0.7 | 1.5 | 0.5 | 0.8 |

### جدول ۵: مقادیر تجربی زاویهٔ تطبیق فاز و پهنای پذیرش زاویه‌ای داخلی برای SHG در صفحات اصلی بلور GdCOB
*(صفحهٔ کتاب: 230، صفحهٔ PDF: 238)*
Experimental values of phase-matching angle and internal angular bandwidth for SHG in principal planes of GdCOB crystal:

| Interacting wavelengths [$\mu$m] | $\phi_{\text{pm}}$ [deg] | $\theta_{\text{pm}}$ [deg] | $\Delta\phi^{\text{int}}$ [deg] | $\Delta\theta^{\text{int}}$ [deg] | Ref. |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **XY plane, $\theta = 90^\circ$** | | | | | |
| SHG, $o + o \Rightarrow e$ | | | | | |
| $1.0642 \Rightarrow 0.5321$ | 46 | | 0.10 | | [2], [15], [18], [19] |
| $0.946 \Rightarrow 0.473$ | 55.9 | | 0.11 | | [20] |
| **XZ plane, $\phi = 0^\circ$, $\theta < V_z$** | | | | | |
| SHG, $o + o \Rightarrow e$ | | | | | |
| $1.0642 \Rightarrow 0.5321$ | | 19.7 | | 0.15 | [2], [15], [18], [19] |

Note: For a biaxial crystal, two angular acceptances exist: one in $\theta$ and other in $\phi$. The authors have presented only the smallest one.

### جدول ۶: مقادیر تجربی ضریب غیرخطی مؤثر مرتبه دوم برای برخی جهات تطبیق فاز
*(صفحهٔ کتاب: 230، صفحهٔ PDF: 238)*
Experimental values of effective second-order nonlinear coefficient for some phase-matching directions (SHG, type I, $1.0642\ \mu\text{m} \Rightarrow 0.5321\ \mu\text{m}$) in GdCOB crystal:

| Phase-matching direction | $d_{\text{eff}}$ [pm/V] | Ref. |
| :--- | :--- | :--- |
| $\theta = 90^\circ$, $\phi = 46^\circ$ (XY plane) | 0.59 | [17] |
| | 0.63 | [19] |
| $\theta = 19.7^\circ$, $\phi = 0^\circ$ (XZ plane) | 0.48 | [19] |
| | 0.50 | [17] |
| $\theta = 160.3^\circ$, $\phi = 0^\circ$ (XZ plane) | 1.01 | [17] |
| | 1.05 | [19] |
| $\theta = 66.8^\circ$, $\phi = 47.4^\circ$ | 0.68 | [17] |
| $\theta = 67^\circ$, $\phi = 46^\circ$ | 0.78 | [19] |
| $\theta = 66.8^\circ$, $\phi = 132.6^\circ$ | 1.51 | [6] |
| | 1.68 | [17] |
| $\theta = 67^\circ$, $\phi = 134^\circ$ | 1.8 | [19] |

Note: The properties of $d_{\text{eff}}$ in the case of GdCOB crystal include mirror and inversion symmetries [21]. This means that the spatial distribution of $d_{\text{eff}}$ can fully be described by choosing two independent quadrants, for example, ($0^\circ < \theta < 90^\circ$, $0^\circ < \phi < 90^\circ$) and ($0^\circ < \theta < 90^\circ$, $90^\circ < \phi < 180^\circ$). After that, the $d_{\text{eff}}$ value in each ($\theta$, $\phi$) direction in these two quadrants is equal to that in ($180^\circ - \theta$, $180^\circ - \phi$) direction and vice versa. For example, the directions ($\theta = 66.8^\circ$, $\phi = 132.6^\circ$) and ($\theta = 113.2^\circ$, $\phi = 47.4^\circ$) possess equal $d_{\text{eff}}$ values.

### جدول ۷: آستانهٔ آسیب توده‌ای ناشی از لیزر (Laser-induced bulk damage threshold)
*(صفحهٔ کتاب: 231، صفحهٔ PDF: 239)*

| $\lambda$ [$\mu$m] | $\tau_p$ [ns] | $I_{\text{thr}}$ [GW/cm$^2$] | Ref. | Note |
| :--- | :--- | :--- | :--- | :--- |
| 0.337 | 0.015–0.075 | >1.35 | [10] | |
| 0.532 | 7 | 1 | [2] | |
| 1.064 | 6 | >1 | [15] | 10 Hz |
| | 0.035 | >6 | [17] | |
| | | >8 | [22] | |
| | | 130 | [6] | 1 pulse |

---

## ۶. فهرست مراجع کتاب برای بلور GdCOB (References)
*(صفحات کتاب: 231–233، صفحات PDF: 239–241)*

- **[1]** G. Aka, L. Bloch, J.M. Benitez, P. Crochet, A. Kahn-Harari, D. Vivien, F. salin, P. Coquelin, D. Colin: A new non linear oxoborate crystal, characterized by using femtosecond broadband pulses. In: *Advanced Solid-State Lasers, OSA Trends in Optics and Photonics Series, Vol. 1*, ed. by S.A. Payne, C. Pollock (OSA, Washington DC, 1996), pp. 336–340.
- **[2]** G. Aka, A. Kahn-Harari, F. Mougel, D. Vivien, F. Salin, P. Coquelin, P. Colin, D. Pelenc, J.P. Damelet: Linear and nonlinear-optical properties of a new gadolinium calcium oxoborate crystal, Ca4GdO(BO3)3. *J. Opt. Soc. Am. B* **14**(9), 2238–2247 (1997).
- **[3]** A.B. Ilyukhin, B.F. Dzhurinskii: Crystal structures of binary oxoborates LnCa4O(BO3)3 (Ln = Gd, Tb, and Lu) and Eu2CaO(BO3)2. *Zh. Neorg. Khim.* **38**(6), 917–920 (1993) [In Russian, English trans.: *Russ. J. Inorg. Chem.* **38**(6), 847–850 (1993)].
- **[4]** G. Aka, A. Kahn-Harari, D. Vivien, J.-M. Benitez, F. Salin, J. Godard: A new nonlinear and neodymium laser self-frequency doubling crystal with congruent melting: Ca4GdO(BO3)3 (GdCOB). *Eur. J. Solid State Inorg. Chem.* **33**(8), 727–736 (1996).
- **[5]** M. Iwai, T. Kobayashi, H. Furuya, Y. Mori, T. Sasaki: Crystal growth and optical characterization of rare-earth (Re) calcium oxyborate ReCa4O(BO3)3 (Re = Y or Gd) as new nonlinear optical material. *Jpn. J. Appl. Phys.* **36**(3A), L276-L279 (1997).
- **[6]** J. Zhou, Z. Zhong, J. Xu, J. Luo, W. Hua, S. Fan: Bridgman growth and characterization of nonlinear optical single crystals Ca4GdO(BO3)3. *Mater. Sci. Eng. B* **97**(3), 283–287 (2003).
- **[7]** Z. Wang, J. Liu, R. Song, X. Xu, X. Sun, H. Jiang, K. Fu, J. Wang, Y. Liu, J. Wei, Z. Shao: The second-harmonic-generation property of GdCa4O(BO3)3 crystal with various phase-matching directions. *Opt. Commun.* **187**(4–6), 401–405 (2001).
- **[8]** Z. Shao, J. Lu, Z. Wang, J. Wang, M. Jiang: Anisotropic properties of Nd:ReCOB (Re = Y, Gd): a low symmetry self-frequency doubling crystal. *Progr. Cryst. Growth Character. Mater.* **40**(1–4), 63–73 (2000).
- **[9]** D. Vivien, G. Aka, A. Kahn-Harari, A. Aron, F. Mougel, J.-M. Benitez, B. Ferrand, R. Klein, G. Kugel, N. Le Nain, M. Jacquet: Crystal growth and optical properties of rare earth calcium oxoborates. *J. Cryst. Growth*, **237–239**, 621–628 (2002).
- **[10]** T. Łukasiewicz, A. Majchrowski, I.V. Kityk, J. Kroog: Influence of the rare-earth doping on the photoinduced EOEs in the GdCOB. *Mater. Lett.* **57**(13–14), 2049–2052 (2003).
- **[11]** C. Wang, H. Zhang, X. Meng, L. Zhu, Y.T. Chow, X. Liu, R. Cheng, Z. Yang, S. Zhang, L. Sun: Thermal, spectroscopic properties and laser performance at 1.06 and 1.33 µm of Nd:Ca4YO(BO3)3 and Nd:Ca4GdO(BO3)3 crystals. *J. Cryst. Growth* **220**(1–2), 114–120 (2000).
- **[12]** F. Auge, F. Druon, F. Balembois, P. Georges, A. Brun, F. Mougel, G. Aka, D. Vivien: Theoretical and experimental investigations of a diode-pumped quasi-three-level laser: the Yb3+-doped Ca4GdO(BO3)3 (Yb:GdCOB) laser. *IEEE. J. Quant. Electr.* **36**(5), 598–606 (2000).
- **[13]** S. Zhang, Z. Cheng, J. Lu, G. Li, J. Lu, Z. Shao, H. Chen: Studies of the effective nonlinear coefficient of GdCa4O(BO3)3 crystal. *J. Cryst. Growth* **205**(3), 453–456 (1999).
- **[14]** N. Umemura, H. Nakao, H. Furuya, M. Yoshimura, Y. Mori, T. Sasaki, K. Yoshida, K. Kato: 90° phase-matching properties of YCa4O(BO3)3 and GdxY1−xCa4O(BO3)3. *Jpn. J. Appl. Phys.* **40**(2A), 596–600 (2001).
- **[15]** G. Aka, F. Mougel, D. Pelenc, B. Ferrand, D. Vivien: Comparative evaluation of GdCOB and YCOB nonlinear-optical properties, in principal and out of principal plane configurations, for the 1064 nm Nd:YAG laser frequency conversion. *Proc. SPIE* **3928**, 108–114 (2000).
- **[16]** X. Yin, J.Y. Wang, H.D. Jiang: Measurement of electro-optic coefficients of low symmetry crystal GdCa4O(BO3)3. *Opt. Laser Technol.* **33**(8), 563–566 (2001).
- **[17]** Z.P. Wang, J.H. Liu, R.B. Song, H.D. Jiang, S.J. Zhang, K. Fu, C.Q. Wang, J.Y. Wang, Y.G. Liu, J.Q. Wei, H.C. Chen, Z.S. Shao: Anisotropy of nonlinear-optical property of RCOB (R = Gd, Y) crystal. *Chin. Phys. Lett.* **18**(3), 385–387 (2001).
- **[18]** F. Mougel, G. Aka, F. Salin, D. Pelenc, B. Ferrand, A. Kahn-Harari, D. Vivien: Accurate second harmonic generation phase matching angles prediction and evaluation of nonlinear coefficients of YCa4O(BO3)3 (YCOB) crystal. In: *Advanced Solid State Lasers, OSA Trends in Optics and Photonics Series, Vol. 26*, ed. by M.M. Fejer, H. Injeyan, U. Keller (OSA, Washington DC, 1999), pp. 709–714.
- **[19]** G. Aka, F. Mougel, D. Vivien, R. Klein, G. Kugel, B. Ferrand, D. Pelenc: Conversion efficiency and absolute effective nonlinear optical coefficients of YCOB and GdCOB measured for different type I SHG phase matching configurations. In: *Advanced Solid-State Lasers, OSA Trends in Optics and Photonics Series, Vol. 50*, ed. by C. Marshall (OSA, Washington DC, 2001), pp. 548–553.
- **[20]** E. Reino, E. Verdier, G. Aka, J.M. Benitez, D. Vivien: Frequency conversion for blue laser emission in Gd1−xYxCOB. In: *Advanced Solid-State Lasers, OSA Trends in Optics and Photonics Series, Vol. 68*, ed. by M.E. Fermann, L.R. Marshall (OSA, Washington DC, 2002), pp. 32–36.
- **[21]** X. Chen, M. Huang, Z. Luo, Y. Huang: Determination of the optimum phase-matching directions for the self-frequency conversion of Nd:GdCOB and Nd:YCOB crystals. *Opt. Commun.* **196**(1–6), 299–307 (2001).
- **[22]** J. Liu, Z. Wang, S. Zhang, J. Wang, H. Chen, Z. Shao, M. Jiang: Second-harmonic generation of 1.06 µm in Sr doped GdCa4O(BO3)3 crystal. *Opt. Commun.* **195**(1–4), 267–271 (2001).
- **[23]** S.-J. Zhang, Z.-X. Cheng, J.-H. Liu, J.-R. Han, J.-Y. Wang, Z.-S. Shao, H.-C. Chen: Effect of strontium ion on the growth and second-harmonic generation properties of GdCa4O(BO3)3 crystal. *Chin. Phys. Lett.* **18**(1), 63–64 (2001).
- **[24]** J. Liu, Z. Fei, S. Zhang, C. Du, J. Wang, H. Chen, Z. Shao: Investigation on intracavity second-harmonic generation of a new Li-doped GdCa4O(BO3)3 crystal. *Opt. Laser Technol.* **33**(8), 597–600 (2001).
- **[25]** J. Liu, X. Xu, C.Q. Wang, S. Zhang, J. Wang, H. Chen, Z. Shao, M. Jiang: Intracavity second-harmonic generation of 1.06 µm in GdCa4O(BO3)3. *Appl. Phys. B.* **72**(2), 163–166 (2001).

---

## ۷. بازخوانی (Proofreading)
تمام مقادیر عددی، جدول‌ها، توان‌ها، فرمول‌های سلمایر و ضرایب غیرخطی با تصاویر صفحات ۲۳۵ تا ۲۴۱ کتاب Nikogosyan (2005) خط به خط مقایسه و تطبیق داده شدند:
1. در جدول ضریب هدایت حرارتی (ص ۲۳۶)، ستون‌های $\parallel X$، $\parallel Y$ و $\parallel Z$ در دماهای مختلف دارای خانه‌های خالی هستند که عیناً مطابق چاپ درج گردیدند.
2. در جدول ضرایب شکست تجربی (ص ۲۳۷)، هر ۱۲ طول موج و مقادیر $n_X, n_Y, n_Z$ بدون هیچ تغییری رونویسی شدند.
3. در معادلات سلمایر (ص ۲۳۷)، هر سه معادلهٔ $n_X^2, n_Y^2, n_Z^2$ و بازهٔ $0.4129\ \mu\text{m} < \lambda < 1.3382\ \mu\text{m}$ با تصویر مطابقت دارند.
4. جدول ضرایب الکترواپتیک خطی (ص ۲۳۷)، ضرایب غیرخطی $d_{il}$ و علامت‌های منفی $d_{13}$ و $d_{33}$ (ص ۲۳۸)، جدول تطبیق فاز و جدول ضریب غیرخطی مؤثر $d_{\text{eff}}$ (ص ۲۳۸)، و جدول آستانه آسیب توده‌ای (ص ۲۳۹) سطر به سطر بازخوانی و تأیید شدند.
5. تعداد اختلافات تصحیح‌شده: ۰ مورد اختلاف حل‌نشده.
