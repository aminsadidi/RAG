You are a scientific assistant for physics and materials science.
Answer the question using ONLY the numbered sources below.

Rules:
- Cite every statement with the number of its source, e.g. [2].
- Report numerical values exactly as written, with their units, uncertainties
  and measurement conditions (temperature, pressure, broadening gas, spectral band).
- Distinguish experimental from theoretical/computed values when the source does.
- If the sources do not contain the answer, reply exactly: "Not found in the provided sources."
- Write citations as plain text with the page, e.g. (Source 2, p. 5), not as links or footnotes.

Sources:
[1] (Tan et al. (2019), p. 10)
2.4 CH4
In general, the measured water-vapor broadening Lorentz half widths of methane were found to be about 20% larger than their air-broadening parameters as shown in Fig. 5. Since the rotational dependence of the water-vapor broadening effects for methane is still not quite clear based on our analysis of the available measurements, the water-vapor broadening coefficients at room temperature were then generated from the scaled value of their corresponding airbroadening parameters. The scaling factor of 1.36 (with a standard deviation of 0.10) was used based on the measurements from (Delahaye et al., 2016c), (Lübken et al., 1991) and (Gharavi & Buckley, 2005) to their corresponding air-broadening parameters in HITRAN. As for their temperature-dependence exponents, the scaling factor of 1.26 to the air-broadening temperature dependence exponents was used as well which also came from the experimental measurement of the 2ν3 R(3) and R(4) manifolds in (Gharavi & Buckley, 2005) .

[2] (Tan et al. (2019), p. 9,10)
2.4 CH4
Before that, only the 2ν3 R(3) and R(4) manifolds located at 1.6-μm region were studied from 316 to 580 K by diode laser absorption spectroscopy in (Gharavi & Buckley, 2005), and the ν4 P(5), P(9) and P(10) manifolds located at the 8-μm region were measured by TDLAS at room temperature in (Lübken et al., 1991).
Figure 5. The pressure-broadening coefficients of methane perturbed by water vapor. (a) black circles represent the water-vapor broadening Lorentz half widths of CH4 in the mid- and nearinfrared region by (Delahaye et al., 2016c) with the red line for the 4 th order polynomial fitting, and blue triangles from the ν4 P(5), P(9) and P(10) manifolds by (Lübken et al., 1991), the 2ν3 R(3) and R(4) manifolds in green diamond by (Gharavi & Buckley, 2005); (b) the ratio of the water-vapor broadening half widths of methane transitions to their corresponding air- broadening half widths in HITRAN, as well as the average value of the those ratios plotted here.

[3] (Tan et al. (2019), p. 15)
2.7 H2S
Figure 8. The ratio of water-vapor broadening coefficients from calculation (Starikov & Protasevich, 2006) to their corresponding self- and air-broadening values of H2S from HITRAN (Gordon et al., 2017).
While for H2S-H2O, there were no experimental data available in literature, some calculations were available from (Starikov & Protasevich, 2006). The ratio of water-vapor broadening coefficients from calculation to that of self- and air-broadening of H2S is shown in Fig. 8. The derived scaling factor of 1.48 was used to scale the self-broadening coefficients from the HITRAN database. The uncertainty would be larger than 20% (error code 3).

Question: What is the scaling factor for water-vapor broadening of CH4?
Answer:

---
About this file (for the reader; not part of the sources):
- question: What is the scaling factor for water-vapor broadening of CH4?
- corpus: hitran
- retrieval: hybrid, top 3
- embedding model: BAAI/bge-base-en-v1.5
- created: 2026-09-27 15:34 UTC

Papers the sources come from:
- Tan, Kochanov, Rothman, Gordon. (2019). Introduction of Water‐Vapor Broadening Parameters and Their Temperature‐Dependent Exponents Into the HITRAN Database: Part I—CO2, N2O, CO, CH4, O2, NH3, and H2S. Journal of Geophysical Research: Atmospheres. doi:10.1029/2019jd030929. arXiv:1906.01475
