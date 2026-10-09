# رونویسی بخش YCa4O(BO3)3 (Yttrium Calcium Oxyborate, YCOB) از کتاب Nikogosyan (2005)

**منبع:**
- کتاب: *Nonlinear Optical Crystals: A Complete Survey*, David N. Nikogosyan, Springer, 2005.
- فصل: Chapter 6: *Newly Developed and Perspective Crystals*
- بخش: Section 6.7: *YCa4O(BO3)3, Yttrium Calcium Oxyborate (YCOB)*
- صفحات کتاب: 233–242
- صفحات فایل PDF: صص ۲۴۱–۲۵۰ (241–250)

---

## ۱. ساختار بلوری، گروه نقطه‌ای و قرارداد محورها (Point Group & Axis Convention)
*(صفحات کتاب: 233–234، صفحات PDF: 241–242)*

- Negative biaxial crystal: $2V_z = 121.1^\circ$ at $\lambda = 0.546\ \mu\text{m}$
- Molecular mass: 441.642
- Specific gravity: $3.31\text{ g/cm}^3$ [1]
- Point group: $m$
- Lattice constants:
  - $a = 8.046\text{ \AA}$ [2]; $8.0770 \pm 0.0003\text{ \AA}$ [3]
  - $b = 15.959\text{ \AA}$ [2]; $16.0194 \pm 0.0005\text{ \AA}$ [3]
  - $c = 3.517\text{ \AA}$ [2]; $3.5308 \pm 0.0001\text{ \AA}$ [3]
  - $\beta = 101.19^\circ$ [2]; $101.167^\circ \pm 0.004^\circ$ [3]
- Assignment of dielectric and crystallographic axes:
  > "Y∥b, the axes a and c lie in XZ plane, the angle between them is $\beta = 101.167^\circ$, the angle between the axes Z and a is $24.7^\circ$, the angle between the axes X and c is $13.5^\circ$ [3]. The slightly different assignments: (a, Z) = $23^\circ$, (c, X) = $12^\circ$, and (a, Z) = $23.6^\circ$, (c, X) = $12.6^\circ$, were reported in [1] and [4], respectively."
- Thermal rotation of XZ plane relative to the crystallographic axes (a, c) {around Y axis} in the temperature range $293\text{ K} < T < 393\text{ K}$:
  $$d\theta_X/dT = d\theta_Z/dT = -12.4\ \mu\text{rad/K} \text{ [5]}$$
- Mohs hardness: 6–6.5 [6]
- Vickers hardness: $757\text{ kg/mm}^2$ [7]
- Melting point: 1783 K [2]; 1753 K [8]; 1763 K (congruent melting) [1]

---

## ۲. ضرایب غیرخطی مرتبهٔ دوم ($d_{il}$)
*(صفحهٔ کتاب: 235، صفحهٔ PDF: 243)*

Most reliable experimental values of second-order nonlinear coefficients:
- $d_{11}(1.0642\ \mu\text{m}) = 0$ [17]; $\approx 0$ [18]
- $d_{12}(1.0642\ \mu\text{m}) = 0.24\text{ pm/V}$ [17]; $0.34\text{ pm/V}$ [19]; $0.43\text{ pm/V}$ [3]
- $d_{13}(1.0642\ \mu\text{m}) = -0.71\text{ pm/V}$ [19]; $-0.73\text{ pm/V}$ [17]; $-0.92\text{ pm/V}$ [3]
- $d_{31}(1.0642\ \mu\text{m}) = 0.41\text{ pm/V}$ [17]
- $d_{32}(1.0642\ \mu\text{m}) = 2.00\text{ pm/V}$ [3]; $2.03\text{ pm/V}$ [19]; $2.35\text{ pm/V}$ [17]
- $d_{33}(1.0642\ \mu\text{m}) = -1.60\text{ pm/V}$ [17]

### روابط ضریب غیرخطی مؤثر در صفحات اصلی بلور YCOB
*(تقریب زاویه واگرایی کوچک (small walk-off angle)، برقراری شرایط تقارن کلاینمن: $d_{12} = d_{26}$, $d_{13} = d_{35}$, $d_{15} = d_{31}$, $d_{24} = d_{32}$) [16], [17]:*
*(صفحهٔ کتاب: 235، صفحهٔ PDF: 243)*

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
*(صفحهٔ کتاب: 235، صفحهٔ PDF: 243)*

Best set of Sellmeier equations ($T = 293\text{ K}$, $\lambda$ in $\mu\text{m}$, $0.3547\ \mu\text{m} < \lambda < 1.9079\ \mu\text{m}$) [10], [14]:

$$n_X^2 = 2.7697 + \frac{0.02034}{\lambda^2 - 0.01779} - 0.00643 \lambda^2$$

$$n_Y^2 = 2.8741 + \frac{0.02213}{\lambda^2 - 0.01871} - 0.01078 \lambda^2$$

$$n_Z^2 = 2.9107 + \frac{0.02232}{\lambda^2 - 0.01887} - 0.01256 \lambda^2$$

متن کتاب:
> "Other sets of dispersion relations are given in [2], [3], [4], [7], [12], [15]."

---

## ۴. روابط پاشندگی وابسته به دما و فرمول‌های ترمواپتیک ($dn/dT$)
*(صفحهٔ کتاب: 235، صفحهٔ PDF: 243)*

Temperature derivative of refractive indices for spectral range $0.3973–1.3382\ \mu\text{m}$ and temperature range $293–393\text{ K}$ ($\lambda$ in $\mu\text{m}$) [5]:

$$\frac{dn_X}{dT} = (8.2058 - 5.0188\lambda) \times 10^{-6}\text{ K}^{-1}$$

$$\frac{dn_Y}{dT} = (2.8217 + 1.9154\lambda) \times 10^{-6}\text{ K}^{-1}$$

$$\frac{dn_Z}{dT} = (3.0310 + 1.8399\lambda) \times 10^{-6}\text{ K}^{-1}$$

---

## ۵. جدول‌های عددی متن کتاب

### جدول ۱: مقدار میانگین ضریب انبساط حرارتی خطی (Mean value of linear thermal expansion coefficient) [9]
*(صفحهٔ کتاب: 234، صفحهٔ PDF: 242)*

| $T$ [K] | $\alpha_t \times 10^6$ [K$^{-1}$], $\parallel a$ | $\alpha_t \times 10^6$ [K$^{-1}$], $\parallel b$ | $\alpha_t \times 10^6$ [K$^{-1}$], $\parallel c$ | Ref. |
| :--- | :--- | :--- | :--- | :--- |
| 293–1073 | 10.9 | 6.8 | 10.8 | [9] |

### جدول ۲: ظرفیت گرمایی ویژه در فشار $P = 0.101325\text{ MPa}$ [9]
*(صفحهٔ کتاب: 234، صفحهٔ PDF: 242)*

| $T$ [K] | $c_p$ [J/kgK] |
| :--- | :--- |
| 293–773 | 682–745 |

### جدول ۳: ضریب هدایت حرارتی در دمای $T = 293\text{ K}$ [9]
*(صفحهٔ کتاب: 234، صفحهٔ PDF: 242)*

| $T$ [K] | $\kappa$ [W/mK], $\parallel a$ | $\kappa$ [W/mK], $\parallel b$ | $\kappa$ [W/mK], $\parallel c$ |
| :--- | :--- | :--- | :--- |
| 293–773 | 2.0–2.2 | 2.7–1.7 | 2.6–1.8 |

### شفافیت نوری
*(صفحهٔ کتاب: 234، صفحهٔ PDF: 242)*
- Transparency range at “ 0” transmittance level: $0.20–2.5\ \mu\text{m}$ [1]

### جدول ۴: ضریب جذب خطی $\alpha$ (Linear absorption coefficient $\alpha$)
*(صفحهٔ کتاب: 234، صفحهٔ PDF: 242)*

| $\lambda$ [$\mu$m] | $\alpha$ [cm$^{-1}$] | Ref. |
| :--- | :--- | :--- |
| 0.355 | 0.05 | [10] |
| 0.532 | 0.015 | [10] |
| 1.064 | 0.001 | [11] |
| | 0.005 | [12] |
| 1.06 | 0.013 | [13] |

### جدول ۵: مقادیر تجربی زاویهٔ تطبیق فاز برای SHG و SFG در صفحات اصلی بلور YCOB در دمای $T = 293\text{ K}$
*(صفحات کتاب: 236–237، صفحات PDF: 244–245)*
Experimental values of phase-matching angle for SHG and SFG in principal planes of YCOB crystal at $T = 293\text{ K}$:

| Interacting wavelengths [$\mu$m] | $\phi_{\text{pm}}$ [deg] | $\theta_{\text{pm}}$ [deg] | Ref. |
| :--- | :--- | :--- | :--- |
| **XY plane, $\theta = 90^\circ$** | | | |
| SHG, $o + o \Rightarrow e$ | | | |
| $1.0642 \Rightarrow 0.5321$ | 35.0 | | [3], [7], [19] |
| $0.7379 \Rightarrow 0.36895$ | 77.3 | | [10] |
| SHG, type I, along Y | | | |
| $0.724 \Rightarrow 0.362$ | 90 | | [20] |
| SFG, $o + o \Rightarrow e$ | | | |
| $1.0642 + 0.5321 \Rightarrow 0.3547$ | 73.2 | | [11] |
| | 73.6 | | [10] |
| | 73.7 | | [5] |
| | 73.8 | | [21] |
| SHG, $e + o \Rightarrow e$ | | | |
| $1.0642 \Rightarrow 0.5321$ | 73.4 | | [7] |
| | 74.8 | | [22] |
| | 75.2 | | [10] |
| | 75.3 | | [5] |
| SHG, type II, along Y | | | |
| $1.03 \Rightarrow 0.515$ | 90 | | [10] |
| SFG, $e + o \Rightarrow e$ | | | |
| $1.9079 + 1.0642 \Rightarrow 0.6831$ | 81.2 | | [10] |
| **YZ plane, $\phi = 90^\circ$** | | | |
| SHG, $e + e \Rightarrow o$ | | | |
| $0.7379 \Rightarrow 0.36895$ | | 66.9 | [10] |
| SFG, $e + e \Rightarrow o$ | | | |
| $1.0642 + 0.5321 \Rightarrow 0.3547$ | | 58.7 | [11] |
| | | 59.7 | [5] |
| | | 59.8 | [21] |
| | | 59.9 | [10] |
| SHG, $e + o \Rightarrow o$ | | | |
| $1.0642 \Rightarrow 0.5321$ | | 58.7 | [3], [7] |
| | | 61.1 | [22] |
| | | 62.7 | [5], [10] |
| SFG, $e + o \Rightarrow o$ | | | |
| $1.9079 + 1.0642 \Rightarrow 0.6831$ | | 73.5 | [10] |
| **XZ plane, $\phi = 0^\circ$, $\theta < V_Z$** | | | |
| SHG, type I, along Z | | | |
| $0.83 \Rightarrow 0.415$ | | 0 | [12] |
| $0.8325 \Rightarrow 0.41625$ | | 0 | [10], [5] |
| SHG, $o + o \Rightarrow e$ | | | |
| $0.9 \Rightarrow 0.45$ | | 18.7 | [5] |
| $0.954 \Rightarrow 0.477$ | | 24.1 | [10] |
| $1.0642 \Rightarrow 0.5321$ | | 30.8 | [10], [5] |
| | | 31.7 | [3], [7], [19] |
| $1.3382 \Rightarrow 0.6691$ | | 38.2 | [10] |
| | | 38.3 | [5] |
| SFG, $o + o \Rightarrow e$ | | | |
| $1.0642 + 0.7379 \Rightarrow 0.4358$ | | 17.1 | [5] |
| $1.569 + 0.5321 \Rightarrow 0.3973$ | | 18.6 | [5] |
| $1.3188 + 0.6594 \Rightarrow 0.4396$ | | 23.0 | [10] |
| $1.9079 + 0.5321 \Rightarrow 0.4161$ | | 26.6 | [10] |

### جدول ۶: مقادیر تجربی پهنای پذیرش زاویه‌ای داخلی برای SHG و SFG در صفحات اصلی بلور YCOB
*(صفحهٔ کتاب: 237، صفحهٔ PDF: 245)*
Experimental values of internal angular bandwidth for SHG and SFG in principal planes of YCOB crystal:

| Interacting wavelengths [$\mu$m] | $\phi_{\text{pm}}$ [deg] | $\theta_{\text{pm}}$ [deg] | $\Delta\phi^{\text{int}}$ [deg] | $\Delta\theta^{\text{int}}$ [deg] | Ref. |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **XY plane, $\theta = 90^\circ$** | | | | | |
| SHG, $o + o \Rightarrow e$ | | | | | |
| $1.0642 \Rightarrow 0.5321$ | 35.0 | | 0.09 | | [3], [7], [19] |
| SHG, $e + o \Rightarrow e$ | | | | | |
| $1.0642 \Rightarrow 0.5321$ | 73.4 | | 0.32 | | [7] |
| SFG, $o + o \Rightarrow e$ | | | | | |
| $1.0642 + 0.5321 \Rightarrow 0.3547$ | 73.2 | | 0.11 | | [23] |
| **YZ plane, $\phi = 90^\circ$** | | | | | |
| SHG, $e + o \Rightarrow o$ | | | | | |
| $1.0642 \Rightarrow 0.5321$ | | 58.7 | | 0.74 | [3], [7] |
| SFG, $e + e \Rightarrow o$ | | | | | |
| $1.0642 + 0.5321 \Rightarrow 0.3547$ | | 58.7 | | 0.19 | [23] |
| **XZ plane, $\phi = 0^\circ$, $\theta < V_Z$** | | | | | |
| SHG, $o + o \Rightarrow e$ | | | | | |
| $1.0642 \Rightarrow 0.5321$ | | 31.7 | | 0.08 | [3], [7], [19] |

Note: For a biaxial crystal, two angular acceptances exist: one in $\theta$ and other in $\phi$. The authors have presented only the smallest one.

### جدول ۷: مقدار تجربی پهنای پذیرش زاویه‌ای داخلی برای جهتی خاص [24]
*(صفحهٔ کتاب: 237، صفحهٔ PDF: 245)*
Experimental values of internal angular bandwidth for some specific phase-matching direction (SHG, type I, $0.946\ \mu\text{m} \Rightarrow 0.473\ \mu\text{m}$) in YCOB crystal [24]:

| Phase-matching direction | $\Delta$ [deg] |
| :--- | :--- |
| $\theta = 67.9^\circ$, $\phi = 136.8^\circ$ | 0.06 |

### جدول ۸: مقادیر تجربی پهنای دمایی (Temperature bandwidth) برای SHG و SFG در صفحات اصلی بلور YCOB
*(صفحات کتاب: 237–238، صفحات PDF: 245–246)*
Experimental values of temperature bandwidth for SHG and SFG in principal planes of YCOB crystal:

| Interacting wavelengths [$\mu$m] | $\Delta T$ [$^\circ$C] | Ref. | Note |
| :--- | :--- | :--- | :--- |
| **XY plane, $\theta = 90^\circ$** | | | |
| SHG, $o + e \Rightarrow e$ | | | |
| $1.0642 \Rightarrow 0.5321$ | 32.7 | [10] | |
| | 32.8 | [5] | $\phi = 75.3^\circ$ |
| SFG, $o + o \Rightarrow e$ | | | |
| $1.0642 + 0.5321 \Rightarrow 0.3547$ | 8.6 | [10] | $\phi = 73.7^\circ$ |
| | 9.7 | [25] | |
| | 10 | [12] | |
| **YZ plane, $\phi = 90^\circ$** | | | |
| SHG, $o + e \Rightarrow o$ | | | |
| $1.0642 \Rightarrow 0.5321$ | 31.5 | [10] | $\theta = 62.7^\circ$ |
| | 31.7 | [14] | |
| | 29.2 | [5] | |
| SFG, $e + e \Rightarrow o$ | | | |
| $1.0642 + 0.5321 \Rightarrow 0.3547$ | 6.2 | [10] | |
| | 8.5 | [23] | |
| **XZ plane, $\phi = 0^\circ$, $\theta < V_Z$ and $\theta > 180^\circ - V_Z$** | | | |
| SHG, type I, along Z | | | |
| $0.8325 \Rightarrow 0.41625$ | 21.6 | [5] | |
| | 31.5 | [10] | |
| SHG, $o + o \Rightarrow e$ | | | |
| $0.9 \Rightarrow 0.45$ | 24.6 | [5] | $\theta = 18.7^\circ$ |
| | 45.3 | [5] | $\theta = 161.3^\circ$ |
| $1.0642 \Rightarrow 0.5321$ | 75 | [5] | $\theta = 30.8^\circ$ |
| $1.3382 \Rightarrow 0.6691$ | 61 | [5] | $\theta = 141.7^\circ$ |
| SFG, $o + o \Rightarrow e$ | | | |
| $1.0642 + 0.7379 \Rightarrow 0.4358$ | 36.5 | [5] | $\theta = 162.9^\circ$ |
| $1.569 + 0.5321 \Rightarrow 0.3973$ | 16.9 | [5] | $\theta = 18.6^\circ$ |
| | 33.8 | [5] | $\theta = 161.4^\circ$ |

### جدول ۹: مقادیر تجربی ضریب غیرخطی مؤثر مرتبه دوم برای برخی جهات خاص تطبیق فاز
*(صفحات کتاب: 238–239، صفحات PDF: 246–247)*
Experimental values of effective second-order nonlinear coefficient for some specific phase-matching directions (SHG, type I, $1.0642\ \mu\text{m} \Rightarrow 0.5321\ \mu\text{m}$) in YCOB crystal:

| Phase-matching direction | $d_{\text{eff}}$ [pm/V] | Ref. |
| :--- | :--- | :--- |
| $\theta = 90^\circ$, $\phi = 35.3^\circ$ (XY plane) | 0.39 | [19] |
| $\theta = 90^\circ$, $\phi = 35^\circ$ (XY plane) | 0.42 | [17] |
| $\theta = 31.7^\circ$, $\phi = 0^\circ$ (XZ plane) | 0.78 | [17] |
| | 1.03 | [19] |
| $\theta = 148.3^\circ$, $\phi = 0^\circ$ (XZ plane) | 1.36 | [19] |
| | 1.44 | [17] |
| $\theta = 65^\circ$, $\phi = 36.5^\circ$ | 1.14 | [17] |
| $\theta = 65.9^\circ$, $\phi = 36.5^\circ$ | 0.91 | [9] |
| $\theta = 66.3^\circ$, $\phi = 143.5^\circ$ | 1.45 | [9] |
| $\theta = 67^\circ$, $\phi = 143.5^\circ$ | 1.73 | [17] |
| $\theta = 66^\circ$, $\phi = 145^\circ$ | 1.8 | [19] |

Note: The properties of $d_{\text{eff}}$ in the case of YCOB crystal include mirror and inversion symmetries [26]. This means that the spatial distribution of $d_{\text{eff}}$ can fully be described by choosing two independent quadrants, for example, ($0^\circ < \theta < 90^\circ$, $0^\circ < \phi < 90^\circ$) and ($0^\circ < \theta < 90^\circ$, $90^\circ < \phi < 180^\circ$). After that, the $d_{\text{eff}}$ value in each ($\theta$, $\phi$) direction in these two quadrants is equal to that in ($180^\circ - \theta$, $180^\circ - \phi$) direction and vice versa. For example, the directions ($\theta = 33^\circ$, $\phi = 9^\circ$) and ($\theta = 147^\circ$, $\phi = 171^\circ$) possess equal $d_{\text{eff}}$ values.

### جدول ۱۰: مقادیر تجربی بازده تبدیل THG برای برخی جهات خاص تطبیق فاز در بلور YCOB [21]
*(صفحهٔ کتاب: 239، صفحهٔ PDF: 247)*
Experimental values of THG conversion efficiency (type I, $1.0642\ \mu\text{m} + 0.5321\ \mu\text{m} \Rightarrow 0.3547\ \mu\text{m}$, $I = 0.8\text{ GW/cm}^2$, $l = 1.04\text{ cm}$) for some specific phase-matching directions in YCOB crystal [21]:

| Phase-matching direction | THG conversion efficiency [%] |
| :--- | :--- |
| $\theta = 65^\circ$, $\phi = 82.8^\circ$ | 2 |
| $\theta = 90^\circ$, $\phi = 73.8^\circ$ (XY plane) | 7 |
| $\theta = 111^\circ$, $\phi = 79.6^\circ$ | 20 |
| $\theta = 106^\circ$, $\phi = 77.2^\circ$ | 26 |

See the note to the previous table. Other proof of superiority of ($\theta = 106^\circ$, $\phi = 77.2^\circ$) direction for type I THG of 1.06-$\mu$m radiation in YCOB is given in [27].

### جدول ۱۱: آستانهٔ آسیب توده‌ای ناشی از لیزر (Laser-induced bulk damage threshold)
*(صفحهٔ کتاب: 239، صفحهٔ PDF: 247)*

| $\lambda$ [$\mu$m] | $\tau_p$ [ns] | $I_{\text{thr}}$ [GW/cm$^2$] | Ref. | Note |
| :--- | :--- | :--- | :--- | :--- |
| 0.532 | 6 | 1 | [7] | |
| 1.064 | 10 | 85 | [9] | 1 pulse |
| | 6 | >1 | [7] | 10 Hz |
| | 1.1 | 18.4 | [12] | along Y axis, E∥Z |

---

## ۶. فهرست مراجع کتاب برای بلور YCOB (References)
*(صفحات کتاب: 240–242، صفحات PDF: 248–250)*

- **[1]** Q. Ye, B.H.T. Chai: Crystal growth of YCa4O(BO3)3 and its orientation. *J. Cryst. Growth* **197**(1–2), 228–235 (1999).
- **[2]** M. Iwai, T. Kobayashi, H. Furuya, Y. Mori, T. Sasaki: Crystal growth and optical characterization of rare-earth (Re) calcium oxyborate ReCa4O(BO3)3 (Re = Y or Gd) as new nonlinear optical material. *Jpn. J. Appl. Phys.* **36**(3A), L276–L279 (1997).
- **[3]** F. Mougel, G. Aka, F. Salin, D. Pelenc, B. Ferrand, A. Kahn-Harari, D. Vivien: Accurate second harmonic generation phase matching angles prediction and evaluation of nonlinear coefficients of YCa4O(BO3)3 (YCOB) crystal. In: *Advanced Solid State Lasers, OSA Trends in Optics and Photonics Series, Vol. 26*, ed. by M.M. Fejer, H. Injeyan, U. Keller (OSA, Washington DC, 1999), pp. 709–714.
- **[4]** J. Wang, Z. Shao, J. Wei, X. Hu, Y. Liu, B. Gong, G. Li, J. Lu, M. Guo, M. Jiang: Research on growth and self-frequency doubling of Nd:ReCOB (Re = Y or Gd) crystals. *Progr. Cryst. Growth Character. Mater.* **40**(1–4), 17–31 (2000).
- **[5]** N. Umemura, M. Ando, K. Suzuki, E. Takaoka, K. Kato, M. Yoshimura, Y. Mori, T. Sasaki: Temperature-insensitive second-harmonic generation at 0.5321 µm in YCa4O(BO3)3. *Jpn. J. Appl. Phys.* **42**(8), 5040–5042 (2003).
- **[6]** Q. Ye, L. Shah, J. Eichenholz, D. Hammons, R. Peale, M. Richardson, A. Chin, B.H.T. Chai: Investigation of diode-pumped, self-frequency doubled RGB lasers from Nd:YCOB crystals. *Opt. Commun.* **164**(1–3), 33–37 (1999).
- **[7]** G. Aka, F. Mougel, D. Pelenc, B. Ferrand, D. Vivien: Comparative evaluation of GdCOB and YCOB nonlinear-optical properties, in principal and out of principal plane configurations, for the 1064 nm Nd:YAG laser frequency conversion. *Proc. SPIE* **3928**, 108–114 (2000).
- **[8]** D.A. Hammons, M. Richardson, B.H.T. Chai, A.K. Chin, R. Jollay: Scaling of longitudinally diode-pumped self-frequency-doubling Nd:YCOB lasers. *IEEE J. Quant. Electr.* **36**(8), 991–999 (2000).
- **[9]** J. Luo, S.J. Fan, H.Q. Xie, K.C. Xiao, S.X. Qian, Z.W. Zhong, G.X. Qiang, R.Y. Sun, J.Y. Xu: Thermal and nonlinear optical properties of Ca4YO(BO3)3. *Cryst. Res. Technol.* **36**(11), 1215–1221 (2001).
- **[10]** N. Umemura, H. Nakao, H. Furuya, M. Yoshimura, Y. Mori, T. Sasaki, K. Yoshida, K. Kato: 90° phase-matching properties of YCa4O(BO3)3 and GdxY1−xCa4O(BO3)3. *Jpn. J. Appl. Phys.* **40**(2A), 596–600 (2001).
- **[11]** H. Furuya, M. Yoshimura, T. Kobayashi, K. Murase, Y. Mori, T. Sasaki: Crystal growth and characterization of GdxY1−xCa4O(BO3)3 crystal. *J. Cryst. Growth* **198–199**, 560–563 (1999).
- **[12]** M. Yoshimura, T. Kobayashi, H. Furuya, K. Murase, Y. Mori, T. Sasaki: Crystal growth and optical properties of yttrium calcium oxyborate YCa4O(BO3)3. In: *Advanced Solid-State Lasers, OSA Trends in Optics and Photonics Series, Vol. 19*, ed. by W.R. Bosenberg, M.M. Fejer (OSA, Washington DC, 1998), pp. 561–564.
- **[13]** J. Liu, C. Wang, S. Zhang, C. Du, J. Lu, J. Wang, H. Chen, Z. Shao, M. Jiang: Investigation on intracavity second-harmonic generation at 1.06 µm in YCa4O(BO3)3 by using an end-pumped Nd:YVO4 laser. *Opt. Commun.* **182**(1–3), 187–191 (2000).
- **[14]** N. Umemura, K. Yoshida, H. Furuya, Y. Mori, T. Sasaki, E. Takaoka, K. Kato: New data on the phase-matching properties of YCa4O(BO3)3. In: *Advanced Solid-State Lasers, OSA Trends in Optics and Photonics Series, Vol. 34*, ed. by H. Injeyan, U. Keller, C. Marshall (OSA, Washington DC, 2000), pp. 501–505.
- **[15]** Z. Shao, J. Lu, Z. Wang, J. Wang, M. Jiang: Anisotropic properties of Nd:ReCOB (Re = Y, Gd): a low symmetry self-frequency doubling crystal. *Progr. Cryst. Growth Character. Mater.* **40**(1–4), 63–73 (2000).
- **[16]** G. Aka, A. Kahn-Harari, F. Mougel, D. Vivien, F. Salin, P. Coquelin, P. Colin, D. Pelenc, J.P. Damelet: Linear and nonlinear-optical properties of a new gadolinium calcium oxoborate crystal, Ca4GdO(BO3)3. *J. Opt. Soc. Am. B* **14**(9), 2238–2247 (1997).
- **[17]** Z.P. Wang, J.H. Liu, R.B. Song, H.D. Jiang, S.J. Zhang, K. Fu, C.Q. Wang, J.Y. Wang, Y.G. Liu, J.Q. Wei, H.C. Chen, Z.S. Shao: Anisotropy of nonlinear-optical property of RCOB (R = Gd, Y) crystal. *Chin. Phys. Lett.* **18**(3), 385–387 (2001).
- **[18]** C. Chen, Z. Shao, J. Jiang, J. Wei, J. Lin, J. Wang, N. Ye, L. Lu, B. Wu, M. Jiang, M. Yoshimura, Y. Mori, T. Sasaki: Determination of the nonlinear optical coefficients of YCa4O(BO3)3 crystal. *J. Opt. Soc. Am. B* **17**(4), 566–571 (2000).
- **[19]** G. Aka, F. Mougel, D. Vivien, R. Klein, G. Kugel, B. Ferrand, D. Pelenc: Conversion efficiency and absolute effective nonlinear optical coefficients of YCOB and GdCOB measured for different type I SHG phase matching configurations. In: *Advanced Solid-State Lasers, OSA Trends in Optics and Photonics Series, Vol. 50*, ed. by C. Marshall (OSA, Washington DC, 2001), pp. 548–553.
- **[20]** H. Nakao, S. Makio, H. Furuya, K. Kawamura, S. Yasuda, Y.K. Yap, M. Yoshimura, Y. Mori, T. Sasaki: Crystal growth of GdYCOB for non-critical phase-matched second-harmonic generation at 860 nm. *J. Cryst. Growth* **237–239**, 632–836 (2002).
- **[21]** Z. Wang, K. Fu, X. Xu, X. Sun, H. Jiang, R. Song, J. Liu, J. Wang, Y. Liu, J. Wei, Z. Shao: The optimum configuration for the third-harmonic generation of 1.064 µm in a YCOB crystal. *Appl. Phys. B* **72**(7), 839–842 (2001).
- **[22]** M. Yoshimura, H. Furuya, I. Yamada, K. Murase, H. Nakao, M. Yamazaki, Y. Mori, T. Sasaki: Noncritically phase-matched second-harmonic generation of a Nd:YAG laser in GdYCOB crystal. In: *Advanced Solid-State Lasers, OSA Trends in Optics and Photonics Series, Vol. 26*, ed. by M.M. Fejer, H. Injeyan, U. Keller (OSA, Washington DC, 1999), pp. 702–706.
- **[23]** M. Yoshimura, H. Furuya, T. Kobayashi, K. Murase, Y. Mori, T. Sasaki: Noncritically phase-matched frequency conversion in GdxY1−xCa4O(BO3)3 crystal. *Opt. Lett.* **24**(4) 193–197 (1999).
- **[24]** E. Reino, E. Verdier, G. Aka, J.M. Benitez, D. Vivien: Frequency conversion for blue laser emission in Gd1−xYxCOB. In: *Advanced Solid-State Lasers, OSA Trends in Optics and Photonics Series, Vol. 68*, ed. by M.E. Fermann, L.R. Marshall (OSA, Washington DC, 2002), pp. 32–36.
- **[25]** H. Furuya, H. Nakao, I. Yamada, Y.F. Ruan, Y.K. Yap, M. Yoshimura, Y. Mori, T. Sasaki: Alleviation of photoinduced damage in GdxY1−xCa4O(BO3)3 at elevated temperature for noncritically phase-matched 355-nm generation. *Opt. Lett.* **25**(21) 1588–1590 (2000).
- **[26]** X. Chen, M. Huang, Z. Luo, Y. Huang: Determination of the optimum phase-matching directions for the self-frequency conversion of Nd:GdCOB and Nd:YCOB crystals. *Opt. Commun.* **196**(1–6), 299–307 (2001).
- **[27]** C. Du, Z. Wang, J. Liu, X. Xu, K. Fu, J. Wang, Z. Shao: Investigation of intracavity third-harmonic generation at 1.06 µm in YCa4O(BO3)3 crystals. *Appl. Phys. B* **74**(2), 125–127 (2002).

---

## ۷. بازخوانی (Proofreading)
تمام مقادیر عددی، جدول‌ها، توان‌ها، فرمول‌های سلمایر، روابط مشتقات دمایی $dn/dT$ و ضرایب غیرخطی با تصاویر صفحات ۲۴۱ تا ۲۵۰ کتاب Nikogosyan (2005) خط به خط مقایسه و تطبیق داده شدند:
1. در روابط $dn/dT$ (ص ۲۳۵، تصویر ۲۴۳)، فرمول‌های خطی وابسته به طول موج برای هر سه محور $dn_X/dT$, $dn_Y/dT$, $dn_Z/dT$ با تصویر صفحه کاملاً تطبیق دارند.
2. در ضرایب سلمایر (ص ۲۳۵، تصویر ۲۴۳)، هر سه رابطهٔ $n_X^2, n_Y^2, n_Z^2$ و مقادیر مخرج‌ها و ضرایب $\lambda^2$ با تصویر صفحه به دقت تطبیق داده شدند.
3. در ضرایب غیرخطی $d_{il}$ (ص ۲۳۵، تصویر ۲۴۳)، علامت‌های منفی $d_{13}$ و $d_{33}$ و مقادیر متعدد گزارش‌شده از مراجع مختلف با تصویر مطابقت دارند.
4. جدول‌های زاویه تطبیق فاز، پهنای پذیرش زاویه‌ای، پهنای دمایی، ضریب غیرخطی مؤثر $d_{\text{eff}}$، بازده تبدیل THG و آستانه آسیب توده‌ای سطر به سطر بازخوانی شدند.
5. تعداد اختلافات تصحیح‌شده: ۰ مورد اختلاف حل‌نشده.
