# Persian Optics RAG Evaluation Scorecard

**Execution Date:** 2026-10-07  
**Benchmark Suite:** `research_package/data/eval_dataset_persian.json`  
**Total Questions Evaluated:** 30  
**Overall Benchmark Pass Rate:** **100.0%** (30/30)  
**Mean Knowledge Quality Score:** **97.5%**  

---

## 1. Topic Breakdown

| Domain Topic | Total Questions | Passed | Pass Rate |
| :--- | :---: | :---: | :---: |
| **Thermo-Optics & Thermal Tuning** | 10 | 10 | 100.0% |
| **Nonlinear Tensors & Symmetries** | 10 | 10 | 100.0% |
| **Quantum SPDC & Entanglement** | 10 | 10 | 100.0% |

---

## 2. Evaluation Results Matrix

| ID | Topic | Crystal / System | Score | Status | Primary Reference |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `eval-01` | thermo-optics | LiB3O5 | 100% | ✅ PASS | Katō, Grechin, Umemura (2018), Laser Phys. 28, 095403 |
| `eval-02` | thermo-optics | BiB3O6 | 100% | ✅ PASS | Miyata, Umemura, Kato (2009), Opt. Lett. 34, 500 |
| `eval-03` | thermo-optics | MgO-LiNbO3 | 100% | ✅ PASS | Gayer et al. (2008; erratum 2010), Appl. Phys. B 91, 343 |
| `eval-04` | thermo-optics | KH2PO4 | 100% | ✅ PASS | Ghosh (1992), ACS Applied Optics; Zernike (1964) |
| `eval-05` | thermo-optics | CsLiB6O10 | 100% | ✅ PASS | Komatsu et al. (1997), Appl. Phys. Lett. 70, 3218; Umemura et al. (2001) |
| `eval-06` | thermo-optics | ZnGeP2 | 100% | ✅ PASS | Bhar & Ghosh (1979), IEEE J. Quantum Electron. QE-15, 680 |
| `eval-07` | thermo-optics | CaGdAlO4 | 100% | ✅ PASS | Loiko et al. (2017), Opt. Lett. 42, 1175 |
| `eval-08` | thermo-optics | Mg-LiTaO3 vs MgO-LiNbO3 | 100% | ✅ PASS | Dolev et al. (2009), Opt. Express 17, 13745; Gayer et al. (2008) |
| `eval-09` | thermo-optics | AgGaS2 | 100% | ✅ PASS | Takaoka & Kato (1999), Appl. Opt. 38, 4577 |
| `eval-10` | thermo-optics | Li2B4O7 | 100% | ✅ PASS | Sugawara et al. (1998), J. Appl. Phys. 84, 5323 |
| `eval-11` | nonlinear-tensors | GaAs, GaP, ZnSe, CdTe | 100% | ✅ PASS | Boyd (2020), Nonlinear Optics 4th Ed.; Petrov (2015) |
| `eval-12` | nonlinear-tensors | GaAs / GaP | 100% | ✅ PASS | Petrov (2015), Prog. Quantum Electron. 42, 1 |
| `eval-13` | nonlinear-tensors | CdGeAs2 | 100% | ✅ PASS | Zakel et al. (2002), Appl. Opt. 41, 2299 |
| `eval-14` | nonlinear-tensors | KDP, ADP, ZGP, AGS, CSP, CGA | 100% | ✅ PASS | Kleinman (1962), Phys. Rev. 126, 1977; Jerphagnon & Kurtz (1970) |
| `eval-15` | nonlinear-tensors | LiNbO3, LiTaO3 | 100% | ✅ PASS | Shoji et al. (1999), J. Opt. Soc. Am. B 16, 620 |
| `eval-16` | nonlinear-tensors | BaB2O4 | 100% | ✅ PASS | Eimerl et al. (1987), J. Appl. Phys. 62, 1968 |
| `eval-17` | nonlinear-tensors | BiB3O6 | 100% | ✅ PASS | Ghotbi & Ebrahim-Zadeh (2004), Opt. Express 12, 6002; Hellwig (1998) |
| `eval-18` | nonlinear-tensors | All NLO Crystals | 100% | ✅ PASS | Miller (1964), Appl. Phys. Lett. 5, 17; Jerphagnon (1970) |
| `eval-19` | nonlinear-tensors | NLO Materials Comparison | 100% | ✅ PASS | Dmitriev et al. (1999), Handbook of Nonlinear Optical Crystals |
| `eval-20` | nonlinear-tensors | KTiOPO4, LiB3O5, KNbO3 | 75% | ✅ PASS | Roberts (1992), IEEE J. Quantum Electron. 28, 1588 |
| `eval-21` | quantum-spdc | PPKTP / KDP | 75% | ✅ PASS | Evans et al. (2010), PRL 105, 253601; Mosley et al. (2008), PRL 100, 133601 |
| `eval-22` | quantum-spdc | PPKTP | 100% | ✅ PASS | Evans et al. (2010), PRL 105, 253601 |
| `eval-23` | quantum-spdc | All SPDC crystals | 100% | ✅ PASS | Bennink (2010), Phys. Rev. A 81, 053805 |
| `eval-24` | quantum-spdc | SPDC Theory | 100% | ✅ PASS | Grice & Walmsley (1997), Phys. Rev. A 56, 1627 |
| `eval-25` | quantum-spdc | Quantum Optics Math | 100% | ✅ PASS | Law, Walmsley, Eberly (2000), Phys. Rev. Lett. 84, 5304 |
| `eval-26` | quantum-spdc | SPDC Interference | 100% | ✅ PASS | Mosley et al. (2008), Phys. Rev. Lett. 100, 133601; Evans (2010) |
| `eval-27` | quantum-spdc | BaB2O4 | 75% | ✅ PASS | Kwiat et al. (1995), Phys. Rev. Lett. 75, 4337 |
| `eval-28` | quantum-spdc | PPKTP | 100% | ✅ PASS | Fedrizzi et al. (2007), Opt. Express 15, 15377 |
| `eval-29` | quantum-spdc | KH2PO4 | 100% | ✅ PASS | Mosley et al. (2008), Phys. Rev. Lett. 100, 133601 |
| `eval-30` | quantum-spdc | PPLN, PPKTP, PPMgLT | 100% | ✅ PASS | Hum & Fejer (2007), C. R. Physique 8, 180; Ljunggren & Tengner (2005) |

---

## 3. Scientific Fact Verification Criteria
Each question was evaluated across 4 rigorous dimensions:
1. **Domain Taxonomy:** Correct categorization in thermo-optics, tensor symmetries, or quantum SPDC.
2. **Bibliographic Linkage:** Direct pairing with primary peer-reviewed papers (Petrov, Kato, Ghosh, Evans, Mosley, Kwiat, Bennink).
3. **Knowledge Base Integrity:** Cross-referencing against the 25 expanded thermo-optic models, 71 nonlinear crystal tensors, or verified SPDC experiment configurations.
4. **Physical Quantitativeness:** Answers must contain verified physical numbers, tensor indices, group velocities, and exact mathematical relations.
