# خلاصه اسکن جامع مقالات اپتیک غیرخطی (Task 3 Summary)

گزارش استخراج کاندیداها از مجموعه مقالات MatRAG (تعداد مقالات اسکن شده: 816).

## ۱. آمار قطعات کاندید به تفکیک بلورها

| نام بلور / رده ماده | مقالات اسکن‌شده | کاندیداهای d_ij | کاندیداهای dn/dT | کاندیداهای Sellmeier | مجموع گزیده‌ها |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `LiNbO3_LN_PPLN` | 71 | 147 | 79 | 95 | **321** |
| `KTP_KTiOPO4` | 53 | 114 | 44 | 96 | **254** |
| `BBO_beta-BaB2O4` | 65 | 130 | 24 | 48 | **202** |
| `AgGaS2` | 50 | 102 | 33 | 31 | **166** |
| `KDP_DKDP_KH2PO4` | 45 | 86 | 11 | 46 | **143** |
| `BiBO_BiB3O6` | 39 | 87 | 22 | 29 | **138** |
| `LiTaO3_LT_PPLT` | 48 | 49 | 35 | 39 | **123** |
| `KNbO3` | 49 | 65 | 29 | 27 | **121** |
| `AgGaSe2` | 43 | 77 | 20 | 22 | **119** |
| `CLBO_CsLiB6O10` | 35 | 48 | 19 | 26 | **93** |
| `LiIO3_alpha-HIO3` | 49 | 67 | 9 | 14 | **90** |
| `AgGaGeS4_HgGa2S4_others` | 37 | 46 | 17 | 23 | **86** |
| `RTP_RbTiOPO4` | 36 | 26 | 15 | 26 | **67** |
| `BaGa4Se7_BaGa4S7` | 20 | 30 | 7 | 26 | **63** |
| `KTA_RTA_arsenates` | 33 | 25 | 9 | 27 | **61** |
| `KBBF_KBe2BO3F2` | 20 | 42 | 0 | 17 | **59** |
| `CBO_CsB3O5` | 25 | 31 | 5 | 19 | **55** |
| `SBN_BaTiO3_ferroelectrics` | 48 | 19 | 11 | 20 | **50** |
| `petrov2015` | 1 | 26 | 13 | 4 | **43** |
| `dolev2009` | 1 | 7 | 5 | 10 | **22** |
| `ADP_NH4H2PO4` | 7 | 13 | 4 | 2 | **19** |
| `ghotbi2004` | 1 | 9 | 0 | 3 | **12** |
| `tzankov2005` | 1 | 11 | 0 | 0 | **11** |
| `kato2018` | 1 | 0 | 5 | 5 | **10** |
| `pack2005` | 1 | 8 | 0 | 2 | **10** |
| `pack2003` | 1 | 5 | 1 | 2 | **8** |
| `petrov2012` | 1 | 6 | 1 | 0 | **7** |
| `umemura2001` | 1 | 0 | 3 | 4 | **7** |
| `li2016` | 1 | 5 | 0 | 1 | **6** |
| `miyata2009` | 1 | 0 | 3 | 3 | **6** |
| `sugawara1998` | 1 | 3 | 0 | 3 | **6** |
| `zhai2013` | 1 | 0 | 4 | 2 | **6** |
| `ghosh1992` | 1 | 0 | 3 | 2 | **5** |
| `kato1994` | 1 | 0 | 3 | 2 | **5** |
| `fedrizzi2007` | 1 | 0 | 2 | 2 | **4** |
| `jerphagnon1970` | 1 | 4 | 0 | 0 | **4** |
| `petrov1998` | 1 | 1 | 0 | 3 | **4** |
| `shoji1999` | 1 | 4 | 0 | 0 | **4** |
| `hellwig1998` | 1 | 3 | 0 | 0 | **3** |
| `ljunggren2005` | 1 | 0 | 0 | 2 | **2** |
| `pack2004` | 1 | 2 | 0 | 0 | **2** |
| `CdSe_CdS_ZnS` | 11 | 0 | 1 | 1 | **2** |
| `bennink2010` | 1 | 1 | 0 | 0 | **1** |
| `gayer2010` | 1 | 0 | 0 | 1 | **1** |
| `evans2010` | 1 | 0 | 0 | 0 | **0** |
| `grice1997` | 1 | 0 | 0 | 0 | **0** |
| `hong1985` | 1 | 0 | 0 | 0 | **0** |
| `hong1987` | 1 | 0 | 0 | 0 | **0** |
| `komatsu1997` | 1 | 0 | 0 | 0 | **0** |
| `law2000` | 1 | 0 | 0 | 0 | **0** |
| `main` | 1 | 0 | 0 | 0 | **0** |
| `mosley2008` | 1 | 0 | 0 | 0 | **0** |

---

## ۲. ۵ مقاله برتر و امیدوارکننده به تفکیک هر بلور (بیشترین چگالی مقادیر عددی)

### بلور `LiNbO3_LN_PPLN`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1ILy_LZ1o1WBh0uDxVZR2UR60y87S7IsA` | `10.1063-1.1656831.pdf` | ص 2, 5, 7, 20, 21, 22, 23, 26 | 67 |
| `18YtoJk9OELBl7PS3LSQecGeKUUazUcPR` | `2021_Zhu_Integrated_photonics_on_thin-film_lithium_niobate_62077d.pdf` | ص 4, 5, 15, 26, 36, 42, 43, 45 | 48 |
| `17L0L2LgJfHkc-q839Ipy3m7WslyMaCOW` | `10.1103-physreva.98.023820.pdf` | ص 2, 3, 4, 6, 9, 11, 12, 13 | 40 |
| `1Tfe1JWh854ovJmddVTVtL9I84Eht036C` | `10.1109-3.161322.pdf` | ص 1, 2, 3, 4, 5, 6, 7, 8 | 33 |
| `1zcM8Bq1HGcL-Be3uamjiHRxqWgYYmmD4` | `10.1007-s00340-006-2414-8.pdf` | ص 1, 2, 3, 4, 5 | 28 |

### بلور `KTP_KTiOPO4`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1nEoFBLjfbIYQvAoyvcEMCUG7XhatZ-YQ` | `10.1364-josab.14.002268.pdf` | ص 1, 2, 3, 4, 5, 6, 7, 8 | 127 |
| `18A1a5MyVFw9VNr4FogoCsMzT5SaO9IsC` | `10.1364-josab.11.002004.pdf` | ص 1, 2, 3, 4, 5, 6, 7, 8 | 45 |
| `1I0ps62wFB0LJUaAlojp5Q16CqsHOlUYO` | `10.1109-3.55534.pdf` | ص 1, 2, 3, 4, 6, 7, 8, 9 | 43 |
| `1-xRjHqUyHOuxG4BhEQYR4wEmcDzpNRVx` | `10.1364-josab.14.001380.pdf` | ص 1, 2, 3, 4, 5, 6 | 30 |
| `1pAJnyEp93vumqU-AZFH79weTx9C7KElN` | `10.1364-ao.36.006794.pdf` | ص 1, 2, 3 | 28 |

### بلور `BBO_beta-BaB2O4`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1HeJAU9v0bMRAad3ALeGKAj0WXXt6jugi` | `2013_Bache_The_anisotropic_Kerr_nonlinear_refractive_index_of_the_beta-barium_bor_34cc4e.pdf` | ص 1, 2, 3, 6, 7, 9, 10, 11 | 109 |
| `17vyTsqq0uOeSjdefOau15MmUksA-3XgR` | `10.1016-j.optcom.2003.10.046.pdf` | ص 2, 3, 4, 6, 8 | 67 |
| `18SU6XkKilCj53A03uYMkRQK9Oe5QXwn7` | `10.1080-01442358909353223.pdf` | ص 4, 6, 7, 8, 14, 16, 18, 19 | 65 |
| `1ECkTuyJ_ke4dfNaUvKqmr94vMjhg2jDH` | `10.1021-acs.chemmater.8b03310.pdf` | ص 1, 3, 5, 7 | 53 |
| `1MeAb3AF-xYHMqtz7r7RPdkPnL0cu8-ju` | `10.1021-acs.cgd.7b00677.pdf` | ص 3, 4, 7, 12, 13, 15 | 47 |

### بلور `AgGaS2`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1T7K2e0vFcLzpCgljgdIHbbVrdGa1_R8s` | `10.1364-josab.14.002481.pdf` | ص 1, 2, 3, 8, 9, 10, 11, 12 | 54 |
| `1tQd2na6aLcREaFKHGsmXhWmk-unPbFJC` | `10.1002-adom.201500038.pdf` | ص 2, 6, 7, 8 | 36 |
| `16NxEFwa7bImqWgeZkGf-6avAbWpVkkuC` | `10.1364-josab.14.001331.pdf` | ص 1, 2, 3, 4, 5, 6, 7 | 33 |
| `1LYVDflEYGZMzGfe41I4ZxwyVaR8uI1T_` | `10.1364-ao.57.002935.pdf` | ص 1, 2, 3, 4 | 32 |
| `1m4k4-VwK9g0ziY1MFGuUV4YAU2AH2ayR` | `10.1021-ja4074084.pdf` | ص 3, 5, 6 | 29 |

### بلور `KDP_DKDP_KH2PO4`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1_QCoEnDB3A-ga5MJZF-QeFFDSDRvJBrb` | `10.1364-josab.4.001072.pdf` | ص 1, 2, 3, 4, 5, 6, 7 | 35 |
| `19IAevukAlgigM-Rm6MWAJTp3GPmN9Bjj` | `10.1109-3.16261.pdf` | ص 3, 4, 5, 6, 8, 9, 10, 11 | 27 |
| `1LS1PXRPaGOx60XJY6X5NOdEMM922ygVb` | `10.1021-acs.chemmater.8b02223.pdf` | ص 3, 4, 5 | 25 |
| `1HzvwFTKiCA91pXNZfpKaKJpqbm9QUquS` | `10.1021-jacs.6b03734.pdf` | ص 3, 4, 5, 15 | 23 |
| `19izIZqpnE5BxWKbuT4HkEsYSVfeDm3Gl` | `10.1021-acs.chemmater.7b00167.pdf` | ص 1, 2, 5, 6, 7, 8 | 19 |

### بلور `BiBO_BiB3O6`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1oxHvq5zuzadLIYYg_TdfjehknD5vGIwD` | `10.1002-lpor.200810075.pdf` | ص 3, 4, 5, 6, 7, 8, 9, 10 | 58 |
| `1khSnYRvn8ZQLq1wXBdCuLPFGvN9znW-L` | `10.1103-physrevb.106.195126.pdf` | ص 5, 6, 7, 8, 9, 10 | 34 |
| `1wchuMBfMmGC8baaJFPjKB9mFo9TS00j3` | `10.1088-1464-4258-10-10-104011.pdf` | ص 2, 3, 5, 6, 7, 8, 10 | 34 |
| `1JdflJ83eJnWNJFPfO7iYMgtK4aN97R4I` | `10.1007-s00340-005-1898-y.pdf` | ص 1, 2, 3, 4, 5, 6, 7, 8 | 29 |
| `1ryBDflZIjowNyvDoeU1runnbE-sVZK6s` | `10.1007-s00339-005-3443-6.pdf` | ص 2, 3, 4, 6 | 20 |

### بلور `LiTaO3_LT_PPLT`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1bX6kk2WPbLi9oQMDO9hsaQvFWWCHMCIi` | `10.1007_s00340_009_3502_3.pdf` | ص 1, 2, 3, 4, 5, 6, 7, 8 | 59 |
| `1sX18f3k7idT4j0DEhnZEJI81UNUmcC0l` | `10.1063-1.2056593.pdf` | ص 1, 2, 3 | 34 |
| `1TwKHzeGY4Zfb-COFIeRKds8ti4wpx2OE` | `10.1364-josab.23.000276.pdf` | ص 1, 2, 3, 4, 5 | 33 |
| `1nBLa5htfzleld-jwVyB1ciCkFgLQuNE7` | `10.1364-ome.1.000458.pdf` | ص 1, 2, 3, 5, 6, 8 | 23 |
| `14oSjgxsImPbURYgp3O81YvMHpwfTlg_b` | `10.1063-1.1754695.pdf` | ص 2, 3, 4 | 17 |

### بلور `KNbO3`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1HynBK34ytzf5KNCnOs3kBydD5FZ5A2wC` | `10.1364_josab.20.002109.pdf` | ص 1, 2, 3, 4, 5, 6, 8 | 33 |
| `1hlhpmZPTjln6tvfDSLSagBLqVb9qFjsh` | `10.1364-josab.9.000507.pdf` | ص 1, 2, 3, 4, 5, 6, 7, 8 | 32 |
| `1SINuZURFEx9Lw7v9DrfhM0L6qVIFKxvN` | `10.1016-0030-4018(74)90183-7.pdf` | ص 1, 2 | 26 |
| `1PB7Qy-rDiHM9pytntv4_YZmmQiIUxs1-` | `10.1016-0030-4018(83)90089-5.pdf` | ص 1, 2, 4, 5 | 23 |
| `1-DHcdFTxhJ-LhAHaNqLzjGDb-AApayZJ` | `10.1063-1.91169.pdf` | ص 2, 3, 4 | 23 |

### بلور `AgGaSe2`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `110WhPU6oHRXBND_u423fpSufjmc55EDk` | `2018_Jia_Research_progress_of_mid-and_far-infrared_nonlinear_optical_crystals_7be9c9.pdf` | ص 3, 4, 5, 6, 8, 9, 10 | 64 |
| `1IcwmOrX_1fpVtvHKx_Et8zhYfXMq-JwO` | `2021_He_Giant_NonResonant_Infrared_Second_Order_Nonlinearity_in_γ_NaAsSe2_67303a.pdf` | ص 1, 2, 3, 9, 10, 11, 12, 13 | 40 |
| `1fFubzbgzx7Alg1VZz1AkZWLDtzQysEtX` | `10.1021-acs.chemmater.2c01011.pdf` | ص 1, 4, 5 | 37 |
| `1Yk5Rpdt1JOkvOVSrPRvX6ojwuJOr2LDM` | `10.1039-c5dt01635e.pdf` | ص 2, 3, 5, 8, 10 | 34 |
| `1wAGgUIRO3hyuGlQb_XhjpVZxa7dV0lLa` | `10.1063-1.347507.pdf` | ص 2, 3 | 25 |

### بلور `CLBO_CsLiB6O10`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1mS-hd0r1Q7SczoyR1ESAXqN8SZAhB01H` | `10.1364-josab.18.000302.pdf` | ص 1, 2, 3, 4, 5 | 32 |
| `1eXZg-mc5D0_IlL1NpkF-oo6eoB4povYX` | `10.1080-10584580490458801.pdf` | ص 5, 6 | 29 |
| `1Rkm1-p2UzAVpiVVGPxCzwJF0ivciGZY8` | `1999_Deki_193nm_Generation_by_Optical_Frequency_Conversion_Using_CsLiB6O10_Cryst_90b13f.pdf` | ص 1, 4, 5, 6 | 25 |
| `1MLNWK0OUSD67-jQPiKVjM8udnEVy56xh` | `10.1021-cg1010743.pdf` | ص 1, 2 | 22 |
| `1jHnLZgu5Tc7NUv8wXmHAwPzKInkW8dNN` | `10.1364-ao.39.005505.pdf` | ص 2, 3, 4, 5 | 22 |

### بلور `LiIO3_alpha-HIO3`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1EQbunwcScrgnALPfHYnZ8273qdoQwZJN` | `10.1063-1.1657376.pdf` | ص 1, 2, 3, 5, 6 | 32 |
| `1q9OQkgltnkD2mJ9KrZIahldbgG_97Dqj` | `10.1364-josab.15.002298.pdf` | ص 1, 2, 4, 5, 6, 7, 8, 9 | 31 |
| `1-cG_1MNHpTqukbP2Z6SIwnFX4xpLNfDl` | `10.1063-1.1654430.pdf` | ص 2, 3, 4 | 21 |
| `1_pKwgAg3qXWf1pITfZ2InlHXAg5lAtLE` | `10.1002-ange.201908935.pdf` | ص 4 | 16 |
| `1TrCaIPijiTlk2aasqOmhhRVg13D2kas-` | `10.1002-anie.201908935.pdf` | ص 4 | 16 |

### بلور `AgGaGeS4_HgGa2S4_others`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1KEmu-3LnyLB8b6ewCM8kCV66qrYyBWf2` | `10.1063-1.2734923.pdf` | ص 1, 2, 3, 4 | 21 |
| `1JKONNBaYD98p0TdkpcAxXRR62ExHmrfw` | `10.1109-jqe.1974.1068091.pdf` | ص 1, 2, 3, 4, 5, 8, 9, 10 | 19 |
| `1375QlQULctDnPNUj4baNRowTq3rbhrjK` | `10.1364-josab.26.001702.pdf` | ص 1, 2, 3, 4, 5, 6, 7, 8 | 19 |
| `1w6f4YJEvjkuNBwWegg7Lz5s1nhf8Hsbc` | `10.1016-j.optmat.2004.04.007.pdf` | ص 3, 4, 5, 6 | 17 |
| `1mH1wqj8D8nhCTMXBl9ECFgLa_mfMx1Fq` | `10.1143-jjap.40.3195.pdf` | ص 2, 3, 4, 5 | 17 |

### بلور `RTP_RbTiOPO4`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1ptKHfJlW9DRT0mqr7qzQmi9k70tubb0C` | `10.1364-josab.28.000873.pdf` | ص 1, 2, 3, 4, 5, 6, 7, 8 | 38 |
| `1momGceBN4eNAhvhNpKQ-OPy36lvaH0lT` | `10.1016-0925-3467(94)90035-3.pdf` | ص 1, 2, 3, 4, 5 | 25 |
| `18_iKSh2gzJjKiWHuuPAqySo4WlggWsnI` | `10.1007-s00340-004-1498-2.pdf` | ص 1, 3, 4, 5 | 17 |
| `1olToN44a8psUD42b17tnGCG0hJHG4Mfk` | `10.1016-j.optmat.2009.03.012.pdf` | ص 1, 2, 3 | 11 |
| `1hmk3TWcHv6gtPptgfBmOQjLmqL8Ecqzc` | `10.1016-s0925-3467(02)00359-2.pdf` | ص 1, 2, 4, 5, 6, 7 | 11 |

### بلور `BaGa4Se7_BaGa4S7`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1veqzDqRED9Dea7J7zUIK5KNbwYwtT0CC` | `10.1016-j.ijleo.2019.163004.pdf` | ص 2, 3, 4, 5, 6, 7, 8, 9 | 42 |
| `1fnHDmAsybfmqxyP8poSiHOSkk2RE4RU5` | `2022_Heiner_Efficient_generation_of_few-cycle_pulses_beyond_10_μm_from_an_optical_50983e.pdf` | ص 2, 3, 6 | 37 |
| `1Qf3M_O9oOAAjMCS2RB7VDmsUyqUKS3dw` | `10.1364-ol.40.004591.pdf` | ص 1, 2, 3, 4 | 28 |
| `1a2JnUFRKm5kNWuMl8O7ZklaPnrJWSHIi` | `2023_Ye_Widely_tunable_and_high_resolution_mid-infrared_laser_based_on_BaGa4Se_83649b.pdf` | ص 1, 3, 4, 6 | 26 |
| `1pUgeFQJE6U6E6IPNNa8f_C-SXVKO2Pxj` | `10.1016-j.optmat.2019.109564.pdf` | ص 7 | 14 |

### بلور `KTA_RTA_arsenates`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `141CZU5oGIswKVKT8nrhTA89DjkzV5HMq` | `10.1007-s003400100733.pdf` | ص 1, 2, 3, 4, 5, 6, 7 | 24 |
| `1GkWg0dm_HiN3z6sBxJZXm8lTpjdCvDzs` | `10.1364-josab.16.001499.pdf` | ص 5, 8, 9, 10, 11, 12 | 22 |
| `1CSVQDmNfuadXVYypI_FQwuMwCo6Vph3T` | `10.1109-3.554854.pdf` | ص 3, 5, 6, 8, 9 | 15 |
| `1hvOptbFYOhvcG7FC2E2qkndVCQdYTnfc` | `10.1063-1.101552.pdf` | ص 2, 3, 4 | 11 |
| `1dGpZMSvMxJnXykhCEc_MTvO7vc6p3Izm` | `10.1364-josab.17.000775.pdf` | ص 1, 3, 4, 5, 6 | 11 |

### بلور `KBBF_KBe2BO3F2`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1ackG0DNbWtHX1uZCDSV8a1_nxhZ6WRFj` | `10.1007-s00340-009-3554-4.pdf` | ص 1, 2, 3, 7, 8, 9, 10 | 33 |
| `13mgPhajs3OJ2Ze-S-ghlq7fYB4YWpGTL` | `10.1002-(sici)1521-4095(199909)11-13<1071--aid-adma1071>3.0.co;2-g.pdf` | ص 1, 2, 3, 4, 5, 7, 8 | 26 |
| `1dfkanuqzurHrzyff5xbscXvNln_kYHA2` | `10.1002-chem.201802787.pdf` | ص 2, 6, 8 | 23 |
| `1hKViH_dffJZuvtDawQGT0a64Evizkulu` | `10.1002-ange.201612236.pdf` | ص 1, 3, 4 | 17 |
| `18w80f-DPNnFeiGuisPxflCheWy0fs8ZS` | `10.1002-ange.201803721.pdf` | ص 2, 4, 5 | 15 |

### بلور `CBO_CsB3O5`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `17OXqMWePKwFrLjZSiaY01xIuybmQHKh-` | `2020_Hamze_Design_rules_for_strong_electro-optic_materials_f4c1a7.pdf` | ص 1, 2, 4, 5, 8 | 75 |
| `11Mps65G0_cUM5JGYzAyy3b8_ynpeC7-Q` | `10.1364-ol.22.001840.pdf` | ص 1, 2 | 18 |
| `1iIS_Hs0W50DX-F8rPg0lL7-L-3klArsn` | `2022_Buryy_Optimal_Vector_Phase_Matching_for_Second_Harmonic_Generation_in_Orthor_957aaf.pdf` | ص 1, 2, 3 | 14 |
| `1on3w_E5Nk95TweZgq_lADJFE3VYBKQPs` | `10.1016-j.optcom.2013.02.028.pdf` | ص 1, 2, 3, 4, 5 | 13 |
| `1likVZc6kE_BkBGm0EXQIG8Nyy3dWxGYu` | `2024_Buryy_Optimal_vector_phase-matching_conditions_in_biaxial_crystalline_materi_b2063d.pdf` | ص 1, 3, 4, 6, 7, 8, 12 | 10 |

### بلور `SBN_BaTiO3_ferroelectrics`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `13sBftege1i0G2NLtDWbg1pJ3heuBC_Pw` | `10.1117-12.7974088.pdf` | ص 2, 3, 7, 11, 12 | 29 |
| `1IQpCuVRYnvTK9MzLE0lgkN8Xd-rqWmCO` | `10.1103-physrevb.37.2074.pdf` | ص 4 | 21 |
| `1P8DRKfz7kSpHBc5CHZBMla2IuSMcMsJj` | `10.1016-j.jeurceramsoc.2021.04.044.pdf` | ص 2, 4, 6, 7 | 17 |
| `14iUf6G8MQWoCJBPZ1XC00NC6Q4NKSJjZ` | `2019_Ortmann_Ultra-Low-Power_Tuning_in_Hybrid_Barium_TitanateSilicon_Nitride_Electr_a34a82.pdf` | ص 1, 2, 4, 5, 7, 8 | 13 |
| `1X3EZdCfMy4G61Pxzkue6A5pnLuBoGEvE` | `10.1021-acsami.5b05344.pdf` | ص 4, 11 | 9 |

### بلور `petrov2015`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `petrov2015` | `petrov2015.pdf` | ص 5, 6, 7, 8, 10, 11, 13, 14 | 127 |

### بلور `dolev2009`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `dolev2009` | `dolev2009.pdf` | ص 1, 2, 3, 4, 5, 6, 7, 8 | 59 |

### بلور `ADP_NH4H2PO4`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1UdZSb5ePg6ElMmRKT-uWzaG2VV2MBueE` | `2021_Müller_Modeling_of_Random_Quasi-Phase-Matching_in_Birefringent_Disordered_Med_84beb3.pdf` | ص 1, 2, 3, 5, 6, 7, 9, 12 | 34 |
| `13dYRCr5xdudHnSvIwCG-e3iI7YCojhxm` | `2017_Joshi_Effect_of_l-threonine_on_growth_and_properties_of_ammonium_dihydrogen_0eb8b4.pdf` | ص 17 | 19 |
| `1ah100Vs1Lt6JSalyGyFJnstFdXufU6k0` | `2013_Ji_Non-critical_phase-matching_fourth_harmonic_generation_of_a_1053-nm_la_865079.pdf` | ص 1, 2, 3, 4, 5 | 8 |
| `1s3Pjva6RKhF5V7Y9ADGM7Uoy7Wts9lqt` | `10.1364-ol.38.001679.pdf` | ص 2 | 3 |
| `11HUkOe_D7tGnWytN_lr72ma17h4t2j1m` | `10.1364-ol.41.005823.pdf` | ص 3 | 1 |

### بلور `ghotbi2004`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `ghotbi2004` | `ghotbi2004.pdf` | ص 1, 2, 3, 4, 5, 6, 7, 10 | 12 |

### بلور `tzankov2005`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `tzankov2005` | `tzankov2005.pdf` | ص 1, 2, 3, 4, 5, 8, 9, 10 | 51 |

### بلور `kato2018`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `kato2018` | `kato2018.pdf` | ص 1, 2, 3, 4, 5 | 30 |

### بلور `pack2005`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `pack2005` | `pack2005.pdf` | ص 1, 2, 3, 4, 5, 6, 7, 8 | 26 |

### بلور `pack2003`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `pack2003` | `pack2003.pdf` | ص 1, 2, 3, 4, 5, 6, 8 | 33 |

### بلور `petrov2012`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `petrov2012` | `petrov2012.pdf` | ص 2, 4, 5, 6, 8, 9, 10 | 25 |

### بلور `umemura2001`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `umemura2001` | `umemura2001.pdf` | ص 1, 2, 4, 5 | 14 |

### بلور `li2016`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `li2016` | `li2016.pdf` | ص 1, 2, 3, 4, 5 | 32 |

### بلور `miyata2009`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `miyata2009` | `miyata2009.pdf` | ص 1, 2, 3 | 13 |

### بلور `sugawara1998`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `sugawara1998` | `sugawara1998.pdf` | ص 1, 3, 4, 5 | 7 |

### بلور `zhai2013`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `zhai2013` | `zhai2013.pdf` | ص 1, 2, 3, 4 | 9 |

### بلور `ghosh1992`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `ghosh1992` | `ghosh1992.pdf` | ص 1, 2, 3 | 4 |

### بلور `kato1994`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `kato1994` | `kato1994.pdf` | ص 1, 2, 3 | 7 |

### بلور `fedrizzi2007`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `fedrizzi2007` | `fedrizzi2007.pdf` | ص 2, 10 | 20 |

### بلور `jerphagnon1970`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `jerphagnon1970` | `jerphagnon1970.pdf` | ص 1, 2, 4, 5 | 8 |

### بلور `petrov1998`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `petrov1998` | `petrov1998.pdf` | ص 3, 5, 6, 7 | 10 |

### بلور `shoji1999`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `shoji1999` | `shoji1999.pdf` | ص 1, 2, 3, 4 | 31 |

### بلور `hellwig1998`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `hellwig1998` | `hellwig1998.pdf` | ص 1, 2, 3 | 10 |

### بلور `ljunggren2005`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `ljunggren2005` | `ljunggren2005.pdf` | ص 3, 7 | 6 |

### بلور `pack2004`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `pack2004` | `pack2004.pdf` | ص 3, 5 | 4 |

### بلور `CdSe_CdS_ZnS`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `1xnyYaq2i96KVPPV5noxKDY5wn7vWGUv5` | `10.1002-pssb.2220900108.pdf` | ص 6 | 3 |
| `1MAuAxv9eyaAje07ZKL2E239GXIjRyVQi` | `10.1002-pssb.2220700139.pdf` | ص 4 | 1 |

### بلور `bennink2010`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `bennink2010` | `bennink2010.pdf` | ص 2 | 2 |

### بلور `gayer2010`
| شناسه مقاله (doc_id) | نام فایل PDF | صفحات حاوی کاندیدا | امتیاز تراکم مقادیر عددی |
| :--- | :--- | :--- | :---: |
| `gayer2010` | `gayer2010.pdf` | ص 1 | 6 |


---
*ثبت لحظه‌ای در فایل‌های `scan_dij.jsonl`، `scan_thermo.jsonl` و `scan_sellmeier.jsonl` تکمیل شد.*
