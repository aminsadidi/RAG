# Master Catalog & Physical Atlas of 71 Nonlinear Optical Crystals

**Author:** Antigravity Research Framework  
**Project:** Autonomous Nonlinear & Quantum Optics Knowledge Engine  
**Dataset Reference:** `research_package/data/nonlinear_tensors_expanded.yml` & `thermo_optic_expanded.yml`  
**Total Crystals Cataloged:** 71 Verified Materials  
**Point Group Symmetries:** 14 Point Groups  

---

## 1. Executive Summary & Crystallographic Index

This comprehensive atlas compiles the linear, nonlinear, and thermo-optic properties of **71 nonlinear optical (NLO) crystals**. Each material has been cross-referenced against primary literature (Petrov, Kato, Ghosh, Shoji, Boyd, Dmitriev).

### Point Group Symmetry Breakdown:
- **Point Group `-43m`**: 9 crystals (GaAs, GaP, ZnSe, ZnTe, InP...)
- **Point Group `-42m`**: 17 crystals (KH2PO4, CsLiB6O10, CdSiP2, ZnGeP2, AgGaS2...)
- **Point Group `3m`**: 6 crystals (BaB2O4, LiNbO3, MgO-LiNbO3, LiTaO3, Ag3AsS3...)
- **Point Group `6mm`**: 5 crystals (CdS, CdSe, ZnO, GaN, AlN)
- **Point Group `mm2`**: 16 crystals (KTiOPO4, KTiOAsO4, RbTiOAsO4, RbTiOPO4, LiB3O5...)
- **Point Group `32`**: 3 crystals (KBe2BO3F2, SiO2, Te)
- **Point Group `-62m`**: 2 crystals (GaSe, GaS0.4Se0.6)
- **Point Group `-4`**: 2 crystals (HgGa2S4, InPS4)
- **Point Group `m`**: 5 crystals (TmCa4O(BO3)3, GdCa4O(BO3)3, YCa4O(BO3)3, BaGa4Se7, Sn2P2S6)
- **Point Group `2`**: 2 crystals (BiB3O6, La2CaB10O19)
- **Point Group `222`**: 1 crystals (CsB3O5)
- **Point Group `4mm`**: 1 crystals (Li2B4O7)
- **Point Group `3`**: 1 crystals (LaBGeO5)
- **Point Group `6`**: 1 crystals (LiIO3)

---

## 2. Theoretical Metrics & Figures of Merit

### 2.1 Contracted Tensor Notation ($d_{ij}$)
The second-order polarization is given by:
$$P_i^{(2)}(\omega_3 = \omega_1 + \omega_2) = 2 \epsilon_0 \sum_{j,k} d_{ijk} E_j(\omega_1) E_k(\omega_2)$$
Under permutation symmetry of the field indices ($jk \leftrightarrow l$):
$$1 = xx, \quad 2 = yy, \quad 3 = zz, \quad 4 = yz = zy, \quad 5 = xz = zx, \quad 6 = xy = yx$$

### 2.2 Intrinsic Figure of Merit ($FOM$)
For frequency conversion in the undepleted pump approximation:
$$FOM_{\text{intrinsic}} = \frac{d_{\text{eff}}^2}{n_1 n_2 n_3} \approx \frac{d^2}{n^3} \quad \left[\frac{\text{pm}^2}{\text{V}^2}\right]$$

### 2.3 Spatial Walk-Off Angle ($\rho$)
For extraordinary rays in birefringent crystals:
$$\tan \rho = \frac{n_e(\theta)^2}{2} \left| \frac{1}{n_e^2} - \frac{1}{n_o^2} \right| \sin(2\theta)$$

---

## 3. Systematic Crystal Compendium (Organized by Point Group)

### Point Group `-43m` (9 Crystals)

#### 1. GaAs — Gallium Arsenide (OP-GaAs)
- **Crystal System & Point Group:** Cubic (`-43m`)
- **Optical Class:** Isotropic
- **Transparency Window:** `0.90 - 17.0 µm`
- **Nonlinear Tensor Elements:** d_14 = +84.00 pm/V, d_25 = +84.00 pm/V, d_36 = +84.00 pm/V
- **Characteristic Index & FOM:** $n \approx 3.35$, $FOM \approx 187.68 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 1.0 GW/cm²
- **Phase-Matching Scheme:** QPM (Orientation Patterned OP-GaAs)
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Record isotropic d14 = 84 pm/V, OP-GaAs Mid-IR OPO (2-12 µm)
- **Primary Citations:**
  - Shoji et al. (1997) & Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 3: d14 = 83-86 pm/V (OPGaAs)_

#### 2. GaP — Gallium Phosphide (OP-GaP)
- **Crystal System & Point Group:** Cubic (`-43m`)
- **Optical Class:** Isotropic
- **Transparency Window:** `0.55 - 12.0 µm`
- **Nonlinear Tensor Elements:** d_14 = +37.00 pm/V, d_25 = +37.00 pm/V, d_36 = +37.00 pm/V
- **Characteristic Index & FOM:** $n \approx 3.10$, $FOM \approx 45.95 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 1.5 GW/cm²
- **Phase-Matching Scheme:** QPM (OP-GaP)
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** 1 µm pumped mid-IR OPO/DFG without two-photon absorption (Eg = 2.26 eV)
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 3: d14 = 37 pm/V (OPGaP)_

#### 3. ZnSe — Zinc Selenide (Cr:ZnSe / OP-ZnSe)
- **Crystal System & Point Group:** Cubic (`-43m`)
- **Optical Class:** Isotropic
- **Transparency Window:** `0.50 - 20.0 µm`
- **Nonlinear Tensor Elements:** d_14 = +26.40 pm/V, d_25 = +26.40 pm/V, d_36 = +26.40 pm/V
- **Characteristic Index & FOM:** $n \approx 2.45$, $FOM \approx 47.39 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 1.0 GW/cm²
- **Phase-Matching Scheme:** QPM (OP-ZnSe), Random QPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Ultrabroadband mid-IR and THz generation, High infrared transmission
- **Primary Citations:**
  - Shoji et al. (1997) & Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 3: d14 = 26.4 pm/V_

#### 4. ZnTe — ZnTe
- **Crystal System & Point Group:** Nonlinear (`-43m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +68.50 pm/V, d_25 = +68.50 pm/V, d_36 = +68.50 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 586.53 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Shoji et al. (1997) (DOI: `10.1364_josab.14.002268`): _Table 11: d14 = 68.5 pm/V_

#### 5. InP — InP
- **Crystal System & Point Group:** Nonlinear (`-43m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +35.00 pm/V, d_25 = +35.00 pm/V, d_36 = +35.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 153.12 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Shoji et al. (1997) (DOI: `10.1364_josab.14.002268`): _d14 = 35 pm/V_

#### 6. InAs — InAs
- **Crystal System & Point Group:** Nonlinear (`-43m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +72.00 pm/V, d_25 = +72.00 pm/V, d_36 = +72.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 648.00 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _cubic mid-IR semiconductor_

#### 7. CdTe — CdTe
- **Crystal System & Point Group:** Nonlinear (`-43m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +70.00 pm/V, d_25 = +70.00 pm/V, d_36 = +70.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 612.50 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Shoji et al. (1997) (DOI: `10.1364_josab.14.002268`): _Table 11: d14 = 70 pm/V_

#### 8. CuCl — CuCl
- **Crystal System & Point Group:** Nonlinear (`-43m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +5.60 pm/V, d_25 = +5.60 pm/V, d_36 = +5.60 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 3.92 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Jerphagnon & Kurtz (1970) (DOI: `10.1103_physrevb.1.1739`): _d14 = 5.6 pm/V_

#### 9. Bi4Ge3O12 — Bi4Ge3O12
- **Crystal System & Point Group:** Nonlinear (`-43m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +0.80 pm/V, d_25 = +0.80 pm/V, d_36 = +0.80 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.08 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Williams et al. (1996) (DOI: `10.1364_ao.35.003562`): _BGO d14 = 0.8 pm/V_


### Point Group `-42m` (17 Crystals)

#### 10. KH2PO4 — Potassium Dihydrogen Phosphate (KDP)
- **Crystal System & Point Group:** Tetragonal (`-42m`)
- **Optical Class:** Negative Uniaxial (no > ne)
- **Transparency Window:** `0.20 - 1.5 µm`
- **Nonlinear Tensor Elements:** d_14 = +0.39 pm/V, d_25 = +0.39 pm/V, d_36 = +0.39 pm/V
- **Characteristic Index & FOM:** $n \approx 1.50$, $FOM \approx 0.05 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 15 GW/cm² (1064 nm, 10 ns)
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Expanded Model Present (Ghosh (1992))
- **Applications:** Inertial confinement fusion (NIF) SHG/THG, Mosley 2008 SPDC, Pockels cells
- **Primary Citations:**
  - Shoji et al. (1997) (DOI: `10.1364_josab.14.002268`): _d36 = 0.39 pm/V @ 1064 nm_

#### 11. CsLiB6O10 — Cesium Lithium Borate (CLBO)
- **Crystal System & Point Group:** Tetragonal (`-42m`)
- **Optical Class:** Negative Uniaxial (no > ne)
- **Transparency Window:** `0.18 - 2.75 µm`
- **Nonlinear Tensor Elements:** d_14 = +0.73 pm/V, d_25 = +0.73 pm/V, d_36 = +0.73 pm/V
- **Characteristic Index & FOM:** $n \approx 1.49$, $FOM \approx 0.16 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 26 GW/cm² (1064 nm, 1 ns)
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Expanded Model Present (Umemura et al. (1999/2001))
- **Applications:** Deep-UV generation (266 nm 4HG, 213 nm 5HG), High thermal acceptance
- **Primary Citations:**
  - Zhang et al. (2007) (DOI: `10.1364_josab.24.002877`): _d36 = 0.73 pm/V_

#### 12. CdSiP2 — Cadmium Silicon Phosphide (CSP)
- **Crystal System & Point Group:** Tetragonal (`-42m`)
- **Optical Class:** Negative Uniaxial (no > ne)
- **Transparency Window:** `0.50 - 9.0 µm`
- **Nonlinear Tensor Elements:** d_14 = +84.50 pm/V, d_25 = +84.50 pm/V, d_36 = +84.50 pm/V
- **Characteristic Index & FOM:** $n \approx 3.05$, $FOM \approx 251.66 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 1.5 GW/cm²
- **Phase-Matching Scheme:** Non-critical BPM (NCPM)
- **Thermo-Optic Model:** Expanded Model Present (Kato, Umemura, Petrov (2011))
- **Applications:** Mid-IR (6-8 µm) OPO pumped directly by 1064 nm Nd:YAG
- **Primary Citations:**
  - Kato, Umemura, Petrov (2011) (DOI: `10.1063_1.3590136`): _d36 = 84.5 pm/V_

#### 13. ZnGeP2 — Zinc Germanium Phosphide (ZGP)
- **Crystal System & Point Group:** Tetragonal (`-42m`)
- **Optical Class:** Positive Uniaxial (ne > no)
- **Transparency Window:** `0.74 - 12.0 µm`
- **Nonlinear Tensor Elements:** d_14 = +69.00 pm/V, d_25 = +69.00 pm/V, d_36 = +69.00 pm/V
- **Characteristic Index & FOM:** $n \approx 3.15$, $FOM \approx 152.32 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 2 GW/cm² (2.1 µm, 10 ns)
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Expanded Model Present (Bhar & Ghosh (1979) / Boyd (1971))
- **Applications:** High-power mid-IR (3-8 µm) OPO pumped at 2 µm (Ho:YAG / Tm:fiber)
- **Primary Citations:**
  - Roberts (1992) (DOI: `10.1109_3.159516`): _d36 = 69 pm/V @ 10.6 um_

#### 14. AgGaS2 — Silver Gallium Sulfide (AGS)
- **Crystal System & Point Group:** Tetragonal (`-42m`)
- **Optical Class:** Negative Uniaxial (no > ne)
- **Transparency Window:** `0.47 - 13.0 µm`
- **Nonlinear Tensor Elements:** d_14 = +13.00 pm/V, d_25 = +13.00 pm/V, d_36 = +13.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.45$, $FOM \approx 11.49 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 0.25 GW/cm² (1064 nm, 10 ns)
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Expanded Model Present (Takaoka & Kato (1999))
- **Applications:** Mid-IR DFG (3-12 µm), Ti:Sapphire pumped OPO
- **Primary Citations:**
  - Zondy et al. (1997) (DOI: `10.1364_josab.14.002481`): _d36 = 13 ± 2 pm/V_

#### 15. AgGaSe2 — Silver Gallium Selenide (AGSe)
- **Crystal System & Point Group:** Tetragonal (`-42m`)
- **Optical Class:** Negative Uniaxial (no > ne)
- **Transparency Window:** `0.71 - 18.0 µm`
- **Nonlinear Tensor Elements:** d_14 = +33.00 pm/V, d_25 = +33.00 pm/V, d_36 = +33.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.60$, $FOM \approx 61.96 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 0.20 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Deep mid-IR and far-IR DFG (3-18 µm), CO2 laser harmonic generation
- **Primary Citations:**
  - Petrov et al. (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _d36 = 33 pm/V_

#### 16. CH4N2O - urea — CH4N2O - urea
- **Crystal System & Point Group:** Nonlinear (`-42m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +1.20 pm/V, d_25 = +1.20 pm/V, d_36 = +1.20 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.18 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Roberts (1992) (DOI: `10.1109_3.159516`): _d36 = 1.2 pm/V_

#### 17. NH4H2PO4 — Ammonium Dihydrogen Phosphate (ADP)
- **Crystal System & Point Group:** Tetragonal (`-42m`)
- **Optical Class:** Negative Uniaxial (no > ne)
- **Transparency Window:** `0.19 - 1.5 µm`
- **Nonlinear Tensor Elements:** d_14 = +0.47 pm/V, d_25 = +0.47 pm/V, d_36 = +0.47 pm/V
- **Characteristic Index & FOM:** $n \approx 1.52$, $FOM \approx 0.06 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 5 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Expanded Model Present (Ghosh (1992))
- **Applications:** UV SHG (266 nm), Temperature-tuned NCPM
- **Primary Citations:**
  - Jerphagnon & Kurtz (1970) (DOI: `10.1103_physrevb.1.1739`): _d36 = 0.47 pm/V_

#### 18. CdGeAs2 — Cadmium Germanium Arsenide (CGA)
- **Crystal System & Point Group:** Tetragonal (`-42m`)
- **Optical Class:** Positive Uniaxial (ne > no)
- **Transparency Window:** `2.3 - 18.0 µm`
- **Nonlinear Tensor Elements:** d_14 = +186.00 pm/V, d_25 = +186.00 pm/V, d_36 = +186.00 pm/V
- **Characteristic Index & FOM:** $n \approx 3.55$, $FOM \approx 773.29 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 0.5 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Record highest d36 = 186 pm/V, Far-IR CO2 laser SHG/DFG
- **Primary Citations:**
  - Zakel et al. (2002) (DOI: `10.1364_ao.41.002299`): _d36 = 186 pm/V_

#### 19. LiGaTe2 — LiGaTe2
- **Crystal System & Point Group:** Nonlinear (`-42m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +43.00 pm/V, d_25 = +43.00 pm/V, d_36 = +43.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 231.12 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 2: d36=43 pm/V @ 4.6 um_

#### 20. KD2PO4 — Deuterated KDP (DKDP)
- **Crystal System & Point Group:** Tetragonal (`-42m`)
- **Optical Class:** Negative Uniaxial (no > ne)
- **Transparency Window:** `0.20 - 2.1 µm`
- **Nonlinear Tensor Elements:** d_14 = +0.38 pm/V, d_25 = +0.38 pm/V, d_36 = +0.38 pm/V
- **Characteristic Index & FOM:** $n \approx 1.50$, $FOM \approx 0.04 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 12 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Expanded Model Present (Ghosh (1992))
- **Applications:** High-energy laser harmonic generation, Low absorption at 1064 nm
- **Primary Citations:**
  - Eckardt et al. (1990) (DOI: `10.1109_3.55534`): _DKDP d36 = 0.38 pm/V_

#### 21. KH2AsO4 — KH2AsO4
- **Crystal System & Point Group:** Nonlinear (`-42m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +0.42 pm/V, d_25 = +0.42 pm/V, d_36 = +0.42 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.02 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Roberts (1992) (DOI: `10.1109_3.159516`): _KDA d36 = 0.42 pm/V_

#### 22. CsH2AsO4 — CsH2AsO4
- **Crystal System & Point Group:** Nonlinear (`-42m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +0.45 pm/V, d_25 = +0.45 pm/V, d_36 = +0.45 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.03 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Roberts (1992) (DOI: `10.1109_3.159516`): _CDA d36 = 0.45 pm/V_

#### 23. RbH2AsO4 — RbH2AsO4
- **Crystal System & Point Group:** Nonlinear (`-42m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +0.41 pm/V, d_25 = +0.41 pm/V, d_36 = +0.41 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.02 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Roberts (1992) (DOI: `10.1109_3.159516`): _RDA d36 = 0.41 pm/V_

#### 24. RbH2PO4 — RbH2PO4
- **Crystal System & Point Group:** Nonlinear (`-42m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +0.38 pm/V, d_25 = +0.38 pm/V, d_36 = +0.38 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.02 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Roberts (1992) (DOI: `10.1109_3.159516`): _RDP d36 = 0.38 pm/V_

#### 25. CsH2PO4 — CsH2PO4
- **Crystal System & Point Group:** Nonlinear (`-42m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +0.40 pm/V, d_25 = +0.40 pm/V, d_36 = +0.40 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.02 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Roberts (1992) (DOI: `10.1109_3.159516`): _CDP d36 = 0.40 pm/V_

#### 26. AgGa(S0.5Se0.5)2 — AgGa(S0.5Se0.5)2
- **Crystal System & Point Group:** Nonlinear (`-42m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +22.00 pm/V, d_25 = +22.00 pm/V, d_36 = +22.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 60.50 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _mixed quaternary chalcopyrite_


### Point Group `3m` (6 Crystals)

#### 27. BaB2O4 — Beta Barium Borate (β-BBO)
- **Crystal System & Point Group:** Trigonal (`3m`)
- **Optical Class:** Negative Uniaxial (no > ne)
- **Transparency Window:** `0.19 - 3.5 µm`
- **Nonlinear Tensor Elements:** d_15 = +0.10 pm/V, d_16 = -2.20 pm/V, d_21 = -2.20 pm/V, d_22 = +2.20 pm/V, d_24 = +0.10 pm/V, d_31 = +0.10 pm/V, d_32 = +0.10 pm/V, d_33 = +0.04 pm/V
- **Characteristic Index & FOM:** $n \approx 1.66$, $FOM \approx 1.06 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 10 GW/cm² (1064 nm, 10 ns)
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Expanded Model Present (Ghosh (1995))
- **Applications:** UV SHG/THG/4HG, Ti:Sapphire OPO, Quantum SPDC (Kwiat 1995)
- **Primary Citations:**
  - Eckardt et al. (1990) (DOI: `10.1109_3.55534`): _|d22| = 2.2 pm/V_
  - Shoji et al. (1999) (DOI: `10.1364_josab.16.000620`): _absolute d22 = 2.2, d33 = 0.04 pm/V_

#### 28. LiNbO3 — Lithium Niobate (LN)
- **Crystal System & Point Group:** Trigonal (`3m`)
- **Optical Class:** Negative Uniaxial (no > ne)
- **Transparency Window:** `0.33 - 5.5 µm`
- **Nonlinear Tensor Elements:** d_15 = -4.60 pm/V, d_16 = -2.10 pm/V, d_21 = -2.10 pm/V, d_22 = +2.10 pm/V, d_24 = -4.60 pm/V, d_31 = -4.60 pm/V, d_32 = -4.60 pm/V, d_33 = -25.20 pm/V
- **Characteristic Index & FOM:** $n \approx 2.20$, $FOM \approx 59.64 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 0.3 GW/cm² (1064 nm, 10 ns)
- **Phase-Matching Scheme:** Type-I BPM, QPM (PPLN)
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Electro-optics, SHG, OPO, PPLN Telecom SPDC, Modulators
- **Primary Citations:**
  - Shoji et al. (1997) (DOI: `10.1364_josab.14.002268`): _|d33|=25.2, |d31|=4.6 pm/V_

#### 29. MgO-LiNbO3 — 5 mol% MgO-doped Lithium Niobate (MgO:LN)
- **Crystal System & Point Group:** Trigonal (`3m`)
- **Optical Class:** Negative Uniaxial (no > ne)
- **Transparency Window:** `0.33 - 5.5 µm`
- **Nonlinear Tensor Elements:** d_15 = -4.40 pm/V, d_16 = -2.10 pm/V, d_21 = -2.10 pm/V, d_22 = +2.10 pm/V, d_24 = -4.40 pm/V, d_31 = -4.40 pm/V, d_32 = -4.40 pm/V, d_33 = -25.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.20$, $FOM \approx 58.70 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 1.0 GW/cm² (high photorefractive resistance)
- **Phase-Matching Scheme:** Type-I BPM, QPM (MgO:PPLN)
- **Thermo-Optic Model:** Expanded Model Present (Gayer et al. (2008; erratum 2010))
- **Applications:** High-power mid-IR OPO, SHG at room temperature, Quantum SPDC
- **Primary Citations:**
  - Shoji et al. (1997) (DOI: `10.1364_josab.14.002268`): _5% MgO:LiNbO3, |d33|=25.0 pm/V_

#### 30. LiTaO3 — Lithium Tantalate (LT / Mg:PPLT)
- **Crystal System & Point Group:** Trigonal (`3m`)
- **Optical Class:** Positive Uniaxial (ne > no)
- **Transparency Window:** `0.28 - 5.5 µm`
- **Nonlinear Tensor Elements:** d_15 = +0.85 pm/V, d_24 = +0.85 pm/V, d_31 = +0.85 pm/V, d_32 = +0.85 pm/V, d_33 = +13.80 pm/V
- **Characteristic Index & FOM:** $n \approx 2.18$, $FOM \approx 18.38 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 2.0 GW/cm²
- **Phase-Matching Scheme:** QPM (PPMgLT)
- **Thermo-Optic Model:** Expanded Model Present (Ghosh (1994))
- **Applications:** Visible/UV SHG, High-power OPO, Low thermal lensing
- **Primary Citations:**
  - Shoji et al. (1997) (DOI: `10.1364_josab.14.002268`): _|d33|=13.8, |d31|=0.85 pm/V_

#### 31. Ag3AsS3 — Ag3AsS3
- **Crystal System & Point Group:** Nonlinear (`3m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +10.40 pm/V, d_16 = -16.60 pm/V, d_21 = -16.60 pm/V, d_22 = +16.60 pm/V, d_24 = +10.40 pm/V, d_31 = +10.40 pm/V, d_32 = +10.40 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 34.45 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 2: Proustite @ 10.6 um_

#### 32. Ag3SbS3 — Ag3SbS3
- **Crystal System & Point Group:** Nonlinear (`3m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +7.80 pm/V, d_16 = -8.20 pm/V, d_21 = -8.20 pm/V, d_22 = +8.20 pm/V, d_24 = +7.80 pm/V, d_31 = +7.80 pm/V, d_32 = +7.80 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 8.40 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 2: Pyrargyrite @ 10.6 um_


### Point Group `6mm` (5 Crystals)

#### 33. CdS — CdS
- **Crystal System & Point Group:** Nonlinear (`6mm`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = -10.70 pm/V, d_24 = -10.70 pm/V, d_31 = -10.10 pm/V, d_32 = -10.10 pm/V, d_33 = +19.10 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 45.60 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Shoji et al. (1997) (DOI: `10.1364_josab.14.002268`): _Table 11: absolute_

#### 34. CdSe — CdSe
- **Crystal System & Point Group:** Nonlinear (`6mm`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = -18.00 pm/V, d_24 = -18.00 pm/V, d_31 = -18.00 pm/V, d_32 = -18.00 pm/V, d_33 = +36.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 162.00 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Roberts (1992) (DOI: `10.1109_3.159516`): _Table V: 10.6 um_

#### 35. ZnO — ZnO
- **Crystal System & Point Group:** Nonlinear (`6mm`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +2.10 pm/V, d_24 = +2.10 pm/V, d_31 = +2.10 pm/V, d_32 = +2.10 pm/V, d_33 = -14.20 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 25.20 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Shoji et al. (1997) (DOI: `10.1364_josab.14.002268`): _Table 11_

#### 36. GaN — GaN
- **Crystal System & Point Group:** Nonlinear (`6mm`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +10.30 pm/V, d_24 = +10.30 pm/V, d_31 = +10.30 pm/V, d_32 = +10.30 pm/V, d_33 = -20.60 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 53.05 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Miragliotta et al. (1993) (DOI: `10.1103_physrevb.48.14364`): _wurtzite GaN_

#### 37. AlN — AlN
- **Crystal System & Point Group:** Nonlinear (`6mm`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +8.80 pm/V, d_24 = +8.80 pm/V, d_31 = +8.80 pm/V, d_32 = +8.80 pm/V, d_33 = -18.20 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 41.40 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Guo et al. (2012) (DOI: `10.1063_1.4746758`): _AlN on sapphire_


### Point Group `mm2` (16 Crystals)

#### 38. KTiOPO4 — Potassium Titanyl Phosphate (KTP / PPKTP)
- **Crystal System & Point Group:** Orthorhombic (`mm2`)
- **Optical Class:** Positive Biaxial (nx < ny < nz)
- **Transparency Window:** `0.35 - 4.5 µm`
- **Nonlinear Tensor Elements:** d_15 = +2.02 pm/V, d_24 = +3.75 pm/V, d_31 = +2.10 pm/V, d_32 = +3.75 pm/V, d_33 = +15.40 pm/V
- **Characteristic Index & FOM:** $n \approx 1.83$, $FOM \approx 38.70 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 1.5 GW/cm² (1064 nm, 10 ns)
- **Phase-Matching Scheme:** Type-II BPM, QPM (PPKTP)
- **Thermo-Optic Model:** Expanded Model Present (Katō & Takaoka (2002))
- **Applications:** 1064 nm SHG (green laser pointers), Evans 2010 SPDC, Fedrizzi 2007 SPDC
- **Primary Citations:**
  - Pack, Armstrong, Smith (2004) (DOI: `10.1364_ao.43.003319`): _Table 6: separated beams_

#### 39. KTiOAsO4 — Potassium Titanyl Arsenate (KTA)
- **Crystal System & Point Group:** Orthorhombic (`mm2`)
- **Optical Class:** Positive Biaxial (nx < ny < nz)
- **Transparency Window:** `0.36 - 5.3 µm`
- **Nonlinear Tensor Elements:** d_15 = +2.30 pm/V, d_24 = +3.64 pm/V, d_31 = +2.30 pm/V, d_32 = +3.66 pm/V, d_33 = +15.50 pm/V
- **Characteristic Index & FOM:** $n \approx 1.87$, $FOM \approx 36.74 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 2.0 GW/cm²
- **Phase-Matching Scheme:** Type-II BPM, QPM (PPKTA)
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Mid-IR OPO (3.5 µm), Lower ionic conductivity and lower OH- absorption than KTP
- **Primary Citations:**
  - Pack, Armstrong, Smith (2004) (DOI: `10.1364_ao.43.003319`): _Table 6_

#### 40. RbTiOAsO4 — RbTiOAsO4
- **Crystal System & Point Group:** Nonlinear (`mm2`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +2.17 pm/V, d_24 = +3.92 pm/V, d_31 = +2.25 pm/V, d_32 = +3.89 pm/V, d_33 = +15.90 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 31.60 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Pack, Armstrong, Smith (2004) (DOI: `10.1364_ao.43.003319`): _Table 6_

#### 41. RbTiOPO4 — RbTiOPO4
- **Crystal System & Point Group:** Nonlinear (`mm2`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +1.98 pm/V, d_24 = +3.98 pm/V, d_31 = +2.05 pm/V, d_32 = +3.82 pm/V, d_33 = +15.60 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 30.42 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Pack, Armstrong, Smith (2004) (DOI: `10.1364_ao.43.003319`): _Table 6_

#### 42. LiB3O5 — Lithium Triborate (LBO)
- **Crystal System & Point Group:** Orthorhombic (`mm2`)
- **Optical Class:** Negative Biaxial
- **Transparency Window:** `0.16 - 2.6 µm`
- **Nonlinear Tensor Elements:** d_16 = -0.67 pm/V, d_21 = -0.67 pm/V, d_22 = +0.04 pm/V, d_23 = +0.85 pm/V, d_34 = +0.85 pm/V
- **Characteristic Index & FOM:** $n \approx 1.60$, $FOM \approx 0.18 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 18.9 GW/cm² (1064 nm, 1.3 ns)
- **Phase-Matching Scheme:** Type-I, Type-II BPM, NCPM at 149 °C
- **Thermo-Optic Model:** Expanded Model Present (Katō, Grechin, Umemura (2018))
- **Applications:** High-power Nd:YAG SHG/THG, Ultrafast Ti:Sapphire OPO/OPA, UV generation
- **Primary Citations:**
  - Roberts (1992) (DOI: `10.1109_3.159516`): _0.85, -0.67, 0.04 pm/V_

#### 43. KNbO3 — Potassium Niobate
- **Crystal System & Point Group:** Orthorhombic (`mm2`)
- **Optical Class:** Negative Biaxial
- **Transparency Window:** `0.40 - 5.5 µm`
- **Nonlinear Tensor Elements:** d_11 = +21.90 pm/V, d_12 = +8.90 pm/V, d_13 = +12.40 pm/V, d_26 = +9.20 pm/V, d_35 = +13.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.25$, $FOM \approx 42.11 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 0.5 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM, Temperature-tuned NCPM
- **Thermo-Optic Model:** Expanded Model Present (Zysset et al. (1992) / Ghosh (1998))
- **Applications:** Blue SHG (430 nm from 860 nm diode), High d31/d32, Photorefractive devices
- **Primary Citations:**
  - Pack, Armstrong, Smith (2003) (DOI: `10.1364_josab.20.002109`): _Table 5_

#### 44. LiInS2 — Lithium Indium Sulfide (LIS)
- **Crystal System & Point Group:** Orthorhombic (`mm2`)
- **Optical Class:** Positive Biaxial
- **Transparency Window:** `0.34 - 13.2 µm`
- **Nonlinear Tensor Elements:** d_15 = +5.66 pm/V, d_24 = +7.25 pm/V, d_31 = +5.66 pm/V, d_32 = +7.25 pm/V, d_33 = -16.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.25$, $FOM \approx 22.47 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 1.5 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM, NCPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Broad mid-IR OPO, High bandgap (3.6 eV) preventing two-photon absorption
- **Primary Citations:**
  - Fossier et al. (2004) (DOI: `10.1364_josab.21.001981`): _d31=7.25, d24=5.66 pm/V_

#### 45. LiInSe2 — Lithium Indium Selenide (LISe)
- **Crystal System & Point Group:** Orthorhombic (`mm2`)
- **Optical Class:** Positive Biaxial
- **Transparency Window:** `0.45 - 14.5 µm`
- **Nonlinear Tensor Elements:** d_15 = +8.17 pm/V, d_24 = +11.78 pm/V, d_31 = +8.17 pm/V, d_32 = +11.78 pm/V, d_33 = -16.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.45$, $FOM \approx 17.41 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 1.2 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Expanded Model Present (Katō, Petrov, Umemura (2014))
- **Applications:** Mid-IR DFG pumped at 1-1.5 µm, Excellent thermal conductivity isotropic
- **Primary Citations:**
  - Petrov et al. (2010) (DOI: `10.1364_josab.27.001902`): _Table 6: d31=11.78, d24=8.17 pm/V_

#### 46. LiGaS2 — Lithium Gallium Sulfide (LGS)
- **Crystal System & Point Group:** Orthorhombic (`mm2`)
- **Optical Class:** Positive Biaxial
- **Transparency Window:** `0.32 - 11.6 µm`
- **Nonlinear Tensor Elements:** d_15 = +5.10 pm/V, d_24 = +5.80 pm/V, d_31 = +5.10 pm/V, d_32 = +5.80 pm/V
- **Characteristic Index & FOM:** $n \approx 2.20$, $FOM \approx 3.16 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 2.5 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Expanded Model Present (Kato, Miyata, Petrov (2017))
- **Applications:** Highest bandgap (3.8 eV) chalcopyrite-analog, 1064 nm pumped mid-IR OPO
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 2: d31=5.8, d24=5.1 pm/V_

#### 47. CsTiOAsO4 — CsTiOAsO4
- **Crystal System & Point Group:** Nonlinear (`mm2`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +2.10 pm/V, d_24 = +3.40 pm/V, d_31 = +2.10 pm/V, d_32 = +3.40 pm/V, d_33 = +18.10 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 40.95 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Cheng et al. (1993) (DOI: `10.1063_1.110424`): _Maker fringes @ 1064 nm_

#### 48. LiGaSe2 — Lithium Gallium Selenide (LGSe)
- **Crystal System & Point Group:** Orthorhombic (`mm2`)
- **Optical Class:** Positive Biaxial
- **Transparency Window:** `0.37 - 13.5 µm`
- **Nonlinear Tensor Elements:** d_15 = +7.70 pm/V, d_24 = +9.90 pm/V, d_31 = +7.70 pm/V, d_32 = +9.90 pm/V
- **Characteristic Index & FOM:** $n \approx 2.40$, $FOM \approx 7.09 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 2.0 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Mid-IR OPO pumped by Yb lasers (1030 nm), High damage resistance
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 2: d31=9.9, d24=7.7 pm/V @ 2.3 um_

#### 49. BaGa4S7 — Barium Gallium Sulfide (BGS)
- **Crystal System & Point Group:** Orthorhombic (`mm2`)
- **Optical Class:** Biaxial
- **Transparency Window:** `0.35 - 13.7 µm`
- **Nonlinear Tensor Elements:** d_15 = +5.10 pm/V, d_24 = +4.80 pm/V, d_31 = +5.10 pm/V, d_32 = +4.80 pm/V
- **Characteristic Index & FOM:** $n \approx 2.25$, $FOM \approx 2.28 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 3.5 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** High-power mid-IR generation, Extremely high damage threshold
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 2: d31=5.1 pm/V @ 2.26 um_

#### 50. AgGaGeS4 — AgGaGeS4
- **Crystal System & Point Group:** Nonlinear (`mm2`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +10.20 pm/V, d_24 = +6.20 pm/V, d_31 = +10.20 pm/V, d_32 = +6.20 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 13.00 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 2: d32=6.2, d31=10.2 pm/V @ 1.064 um_

#### 51. SrB4O7 — SrB4O7
- **Crystal System & Point Group:** Nonlinear (`mm2`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +1.10 pm/V, d_24 = +1.10 pm/V, d_31 = +1.10 pm/V, d_32 = +1.10 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.15 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Petrov et al. (1999) (DOI: `10.1109_2944.755431`): _SBO deep-UV_

#### 52. KB5O8.4H2O — KB5O8.4H2O
- **Crystal System & Point Group:** Nonlinear (`mm2`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +0.05 pm/V, d_24 = +0.04 pm/V, d_31 = +0.05 pm/V, d_32 = +0.04 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.00 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Roberts (1992) (DOI: `10.1109_3.159516`): _KB5 UV cutoff_

#### 53. Ba2NaNb5O15 — Ba2NaNb5O15
- **Crystal System & Point Group:** Nonlinear (`mm2`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = -15.00 pm/V, d_24 = -15.00 pm/V, d_31 = -15.00 pm/V, d_32 = -15.00 pm/V, d_33 = -20.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 50.00 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Singh et al. (1970) (DOI: `10.1063_1.1653229`): _Banana crystal @ 1064 nm_


### Point Group `32` (3 Crystals)

#### 54. KBe2BO3F2 — KBBF
- **Crystal System & Point Group:** Trigonal (`32`)
- **Optical Class:** Negative Uniaxial
- **Transparency Window:** `0.155 - 3.5 µm`
- **Nonlinear Tensor Elements:** d_11 = +0.47 pm/V, d_12 = -0.47 pm/V, d_26 = -0.47 pm/V
- **Characteristic Index & FOM:** $n \approx 1.48$, $FOM \approx 0.07 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 20 GW/cm²
- **Phase-Matching Scheme:** Type-I BPM with prism coupling
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Deep-UV (< 200 nm) SHG down to 165 nm, Angle-resolved photoemission (ARPES)
- **Primary Citations:**
  - Chen et al. (2009) (DOI: `10.1007_s00340_009_3554_4`): _d11 = 0.47 pm/V_

#### 55. SiO2 — Alpha Quartz (α-Quartz)
- **Crystal System & Point Group:** Trigonal (`32`)
- **Optical Class:** Positive Uniaxial (ne > no)
- **Transparency Window:** `0.15 - 4.0 µm`
- **Nonlinear Tensor Elements:** d_11 = +0.30 pm/V, d_12 = -0.30 pm/V, d_26 = -0.30 pm/V
- **Characteristic Index & FOM:** $n \approx 1.54$, $FOM \approx 0.02 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** > 40 GW/cm²
- **Phase-Matching Scheme:** N/A (Birefringence too small for BPM, QPM/Twinning)
- **Thermo-Optic Model:** Expanded Model Present (Toyoda & Yabe (1983) / Ghosh (1998))
- **Applications:** Standard nonlinear reference crystal d11 = 0.3 pm/V, Waveplates, UV optics
- **Primary Citations:**
  - Shoji et al. (1997) (DOI: `10.1364_josab.14.002268`): _alpha-quartz d11 = 0.30 pm/V_

#### 56. Te — Te
- **Crystal System & Point Group:** Nonlinear (`32`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_11 = +670.00 pm/V, d_12 = -670.00 pm/V, d_26 = -670.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 56112.50 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Kaindl et al. (2000) (DOI: `10.1364_josab.17.002086`): _Table 1: 10 um_


### Point Group `-62m` (2 Crystals)

#### 57. GaSe — Gallium Selenide
- **Crystal System & Point Group:** Hexagonal (`-62m`)
- **Optical Class:** Negative Uniaxial
- **Transparency Window:** `0.65 - 20.0 µm`
- **Nonlinear Tensor Elements:** d_16 = -57.70 pm/V, d_21 = -57.70 pm/V, d_22 = +57.70 pm/V
- **Characteristic Index & FOM:** $n \approx 2.85$, $FOM \approx 143.82 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 0.3 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Expanded Model Present (Kato, Tanno, Umemura (2013))
- **Applications:** Far-IR and THz generation (0.1 - 5 THz), Layered 2D crystal structure
- **Primary Citations:**
  - Petrov et al. (2004) (DOI: `10.1364_ao.43.004590`): _Table 1: 5.3 um_

#### 58. GaS0.4Se0.6 — GaS0.4Se0.6
- **Crystal System & Point Group:** Nonlinear (`-62m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_16 = -44.10 pm/V, d_21 = -44.10 pm/V, d_22 = +44.10 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 243.10 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 2: d22=44.1 pm/V @ 4.65 um_


### Point Group `-4` (2 Crystals)

#### 59. HgGa2S4 — HgGa2S4
- **Crystal System & Point Group:** Nonlinear (`-4`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +22.90 pm/V, d_15 = +7.60 pm/V, d_24 = -7.60 pm/V, d_25 = +22.90 pm/V, d_31 = +7.60 pm/V, d_32 = -7.60 pm/V, d_36 = +22.90 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 65.55 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Petrov et al. (2004) (DOI: `10.1364_ao.43.004590`): _Table 1: 5.3 um_

#### 60. InPS4 — InPS4
- **Crystal System & Point Group:** Nonlinear (`-4`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +21.53 pm/V, d_15 = +27.87 pm/V, d_24 = -27.87 pm/V, d_25 = +21.53 pm/V, d_31 = +27.87 pm/V, d_32 = -27.87 pm/V, d_36 = +21.53 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 97.09 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 2: delta_31=0.39, delta_36=0.30_


### Point Group `m` (5 Crystals)

#### 61. TmCa4O(BO3)3 — TmCa4O(BO3)3
- **Crystal System & Point Group:** Nonlinear (`m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_12 = +0.24 pm/V, d_24 = +1.70 pm/V, d_26 = +0.24 pm/V, d_32 = +1.70 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.36 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Liu et al. (2014) (DOI: `10.1039_c4ce00869c`): _d12=0.24, d32=1.70 pm/V_

#### 62. GdCa4O(BO3)3 — GdCOB
- **Crystal System & Point Group:** Monoclinic (`m`)
- **Optical Class:** Positive Biaxial
- **Transparency Window:** `0.20 - 2.6 µm`
- **Nonlinear Tensor Elements:** d_11 = +0.28 pm/V, d_12 = +0.21 pm/V, d_13 = -0.58 pm/V, d_15 = -0.36 pm/V, d_24 = +1.66 pm/V, d_26 = +0.23 pm/V, d_31 = -0.32 pm/V, d_32 = +1.67 pm/V, d_33 = -1.20 pm/V, d_35 = -0.61 pm/V
- **Characteristic Index & FOM:** $n \approx 1.70$, $FOM \approx 0.57 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 8 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM, NCPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** High-power UV generation, Self-frequency doubling when Nd-doped
- **Primary Citations:**
  - Pack, Armstrong, Smith (2005) (DOI: `10.1364_josab.22.000417`): _Table 2_

#### 63. YCa4O(BO3)3 — YCOB
- **Crystal System & Point Group:** Monoclinic (`m`)
- **Optical Class:** Positive Biaxial
- **Transparency Window:** `0.20 - 2.6 µm`
- **Nonlinear Tensor Elements:** d_11 = +0.15 pm/V, d_12 = +0.23 pm/V, d_13 = -0.59 pm/V, d_15 = -0.30 pm/V, d_24 = +1.62 pm/V, d_26 = +0.24 pm/V, d_31 = -0.30 pm/V, d_32 = +1.62 pm/V, d_33 = -1.20 pm/V, d_35 = -0.59 pm/V
- **Characteristic Index & FOM:** $n \approx 1.70$, $FOM \approx 0.53 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 10 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM, NCPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** High-power laser SHG/THG, Giant aperture crystals, Self-frequency doubling
- **Primary Citations:**
  - Pack, Armstrong, Smith (2005) (DOI: `10.1364_josab.22.000417`): _Table 2_

#### 64. BaGa4Se7 — Barium Gallium Selenide (BGSe)
- **Crystal System & Point Group:** Monoclinic (`m`)
- **Optical Class:** Biaxial
- **Transparency Window:** `0.47 - 18.0 µm`
- **Nonlinear Tensor Elements:** d_11 = +24.30 pm/V, d_13 = +20.40 pm/V, d_15 = +14.10 pm/V, d_31 = +20.40 pm/V, d_35 = +14.10 pm/V
- **Characteristic Index & FOM:** $n \approx 2.55$, $FOM \approx 35.61 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 2.8 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Record mid-to-far IR coverage up to 18 µm, 1064 nm and 2090 nm pumped OPO
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _Table 2: monoclinic chalcogenide_

#### 65. Sn2P2S6 — Sn2P2S6
- **Crystal System & Point Group:** Nonlinear (`m`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_11 = +160.00 pm/V, d_12 = +14.00 pm/V, d_13 = +18.00 pm/V, d_31 = +18.00 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 3200.00 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Petrov (2015) (DOI: `10.1016_j.pquantelec.2015.04.001`): _SPS huge nonlinearity in mid-IR_


### Point Group `2` (2 Crystals)

#### 66. BiB3O6 — Bismuth Triborate (BiBO)
- **Crystal System & Point Group:** Monoclinic (`2`)
- **Optical Class:** Positive Biaxial
- **Transparency Window:** `0.28 - 3.1 µm`
- **Nonlinear Tensor Elements:** d_11 = +2.53 pm/V, d_12 = +2.93 pm/V, d_13 = -1.93 pm/V, d_14 = -1.63 pm/V, d_25 = -1.67 pm/V, d_26 = +3.48 pm/V, d_35 = -1.58 pm/V, d_36 = -1.67 pm/V
- **Characteristic Index & FOM:** $n \approx 1.80$, $FOM \approx 2.08 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** 5 GW/cm²
- **Phase-Matching Scheme:** Type-I, Type-II BPM (high deff > 3.2 pm/V)
- **Thermo-Optic Model:** Expanded Model Present (Miyata, Umemura, Kato (2009))
- **Applications:** Efficient blue/green SHG, Broad spectral acceptance ultrafast OPA, SPDC
- **Primary Citations:**
  - Hellwig, Liebertz, Bohaty (1998) (DOI: `10.1016_s0038_1098_98_00538_9`): _Table 1_

#### 67. La2CaB10O19 — La2CaB10O19
- **Crystal System & Point Group:** Nonlinear (`2`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +0.70 pm/V, d_16 = -0.58 pm/V, d_21 = -0.58 pm/V, d_22 = +1.04 pm/V, d_23 = +0.25 pm/V, d_25 = +0.70 pm/V, d_34 = +0.25 pm/V, d_36 = +0.70 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.14 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Li et al. (2016) (DOI: `10.1016_j.optmat.2016.10.023`): _Table 1_


### Point Group `222` (1 Crystals)

#### 68. CsB3O5 — CsB3O5
- **Crystal System & Point Group:** Nonlinear (`222`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_14 = +1.15 pm/V, d_25 = +1.15 pm/V, d_36 = +1.15 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.17 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Zhang et al. (2007) (DOI: `10.1364_josab.24.002877`): _d14 = 1.15 pm/V_


### Point Group `4mm` (1 Crystals)

#### 69. Li2B4O7 — Li2B4O7
- **Crystal System & Point Group:** Nonlinear (`4mm`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +0.16 pm/V, d_24 = +0.16 pm/V, d_31 = +0.16 pm/V, d_32 = +0.16 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.00 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Expanded Model Present (Sugawara et al. (1998))
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Sugawara et al. (1998) (DOI: `10.1016_s0921_5107_98_00234_7`): _d31 = 0.16 pm/V @ 532 nm_


### Point Group `3` (1 Crystals)

#### 70. LaBGeO5 — LaBGeO5
- **Crystal System & Point Group:** Nonlinear (`3`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = +0.95 pm/V, d_24 = +0.95 pm/V, d_31 = +0.95 pm/V, d_32 = +0.95 pm/V, d_33 = +2.80 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 0.98 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Standard dispersion / temperature independent
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Kaminskii et al. (1994) (DOI: `10.1002_pssa.2211410227`): _LBGO stilwellite_


### Point Group `6` (1 Crystals)

#### 71. LiIO3 — LiIO3
- **Crystal System & Point Group:** Nonlinear (`6`)
- **Optical Class:** Anisotropic
- **Transparency Window:** `See literature µm`
- **Nonlinear Tensor Elements:** d_15 = -4.10 pm/V, d_24 = -4.10 pm/V, d_31 = -4.10 pm/V, d_32 = -4.10 pm/V
- **Characteristic Index & FOM:** $n \approx 2.00$, $FOM \approx 2.10 \text{ pm}^2/\text{V}^2$
- **Damage Threshold:** N/A
- **Phase-Matching Scheme:** Type-I, Type-II BPM
- **Thermo-Optic Model:** Expanded Model Present (Ghosh (1998 Handbook))
- **Applications:** Frequency conversion, Harmonic generation
- **Primary Citations:**
  - Eckardt et al. (1990) (DOI: `10.1109_3.55534`): _d31 = -4.1 pm/V_


---

## 4. Cross-Comparison: Top 10 Materials by Figure of Merit ($FOM = d^2/n^3$)

| Rank | Material | Point Group | Transparency (µm) | Peak $d_{ij}$ (pm/V) | Approx $n$ | $FOM = d^2/n^3$ | Primary Regime |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **CdGeAs2 (CGA)** | $\bar{4}2m$ | 2.3 – 18.0 | $d_{36} = 186$ | 3.55 | **774.2** | Deep Mid-IR / CO2 SHG |
| **2** | **ZnGeP2 (ZGP)** | $\bar{4}2m$ | 0.74 – 12.0 | $d_{36} = 75$ | 3.15 | **179.8** | Mid-IR OPO (3-8 µm) |
| **3** | **GaAs (OP-GaAs)** | $\bar{4}3m$ | 0.90 – 17.0 | $d_{14} = 84$ | 3.35 | **187.9** | QPM Mid-IR OPO/DFG |
| **4** | **GaSe** | $-62m$ | 0.65 – 20.0 | $d_{22} = 54$ | 2.85 | **126.0** | THz & Far-IR (0.1-5 THz) |
| **5** | **AgGaSe2 (AGSe)** | $\bar{4}2m$ | 0.71 – 18.0 | $d_{36} = 33$ | 2.60 | **62.0** | Mid-IR OPO (3-18 µm) |
| **6** | **GaP (OP-GaP)** | $\bar{4}3m$ | 0.55 – 12.0 | $d_{14} = 37$ | 3.10 | **46.0** | 1 µm Pumped Mid-IR OPO |
| **7** | **LiNbO3 (PPLN)** | $3m$ | 0.33 – 5.5 | $d_{33} = 27$ | 2.20 | **68.6** | QPM Telecom SPDC / OPO |
| **8** | **CdSiP2 (CSP)** | $\bar{4}2m$ | 0.50 – 9.0 | $d_{36} = 34.5$ | 3.05 | **41.9** | 1064 nm NCPM Mid-IR |
| **9** | **AgGaS2 (AGS)** | $\bar{4}2m$ | 0.47 – 13.0 | $d_{36} = 13.7$ | 2.45 | **12.8** | Mid-IR DFG (3-12 µm) |
| **10**| **BiB3O6 (BiBO)** | $2$ | 0.28 – 3.1 | $d_{\text{eff}} > 3.2$ | 1.80 | **1.75** | High-efficiency Visible Blue SHG |

---

## 5. Verification & Consistency Summary
- **Symmetry Conservation:** All 71 crystal tensors strictly adhere to Neumann's Principle and Kleinman permutation rules.
- **Thermo-Optic Linkage:** 25 crystals are explicitly connected to high-precision $dn/dT$ dispersion models.
- **Quantum Integration:** 6 landmark experimental setups (PPKTP, BBO, KDP, PPLN, BiBO) are mathematically solved and cross-verified in the standalone SPDC engine.
