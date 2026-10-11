# Prompt for Gemini: extracting nonlinear-crystal data

**How to use it:** paste the text below (from "You are extracting…" to the end) into Gemini and give it access to the
RAG-Optics folder in Drive. Run each crystal group in a separate chat, so the answers stay short and checkable.
Send the YAML Gemini returns to Claude to test and add to the site.

---

You are extracting numerical optical data for nonlinear crystals from the PDF papers in my Google Drive folder
"RAG-Optics" (subfolder `01_Papers_by_Category`). The data goes into a scientific database, so accuracy matters more
than coverage.

## Hard rules
1. Use ONLY the PDFs in that folder. Never use your memory, the web, or another database. If a value is not in a PDF
   there, write `not_found` — an empty answer is far better than a guessed one.
2. For every value give: the PDF file name, the PDF page number (the page of the file, not the journal page), and the
   exact place (e.g. "Table 2, row KTA z-axis", "Eq. (4)").
3. Copy numbers digit by digit with their sign and power of ten. Check the sign of every coefficient twice: PDF text
   often loses minus signs, so read the page image, not only the text layer.
4. Write the units and what the formula's variables mean (λ in µm or nm, T in °C or K, the reference temperature t0).
5. If the paper reports a check value (a phase-matching angle or temperature, a tuning rate, an index at one
   wavelength), copy it too: we use it to test the formula.
6. If two papers disagree, give both; do not choose.

## Tasks (one group per chat)

### Group A: thermo-optic dispersion (dn/dT) for crystals that have refractive-index data but no temperature data
KTiOAsO4 (x axis especially: the y and z axes are already in), KBe2BO3F2 (KBBF), SiO2 (crystal quartz), LiGaS2, LiGaSe2,
BaGa4S7, AgGaGeS4, CdGeAs2, GaN, ZnTe, CdS, Ag3AsS3, Ag3SbS3, Te, Se, DAST, DSTMS.
For each one: the formula of dn/dT (or of n(λ, T)) for every principal axis (o/e, or x/y/z), its wavelength and
temperature range, and the paper's own check values.

### Group B: second-order nonlinear coefficients d_ij (pm/V) for crystals that have none
BaTiO3, ZnO, GaS, AlN, SiC, Tl3AsSe3, CdGa2S4, TeO2, BaGa2GeSe6, CuGaS2, ZnS, and the missing elements of BaGa4S7 and
BaGa4Se7 (complete tensor).
For each one: the point group, every d_ij with its sign and the wavelength of the measurement, the reference value it
was scaled to (e.g. "relative to d36 of KDP = 0.39 pm/V"), and whether Kleinman symmetry was assumed.

### Group C: crystals that are missing completely
Sr2Be2B2O7 (SBBO), K2Al2B2O7 (KABO), YAl3(BO3)4 (YAB), BPO4, SrxBa1-xNb2O6 (SBN), CsH2AsO4 (CDA), β-Ga2O3,
La3Ga5SiO14 (langasite), OH1, HMQ-TMS.
For each one: (1) the Sellmeier equation for each axis with its range and temperature, (2) the d_ij as in group B,
(3) dn/dT as in group A, if present.

### Group D: data for a new row on the crystal card (the 50 most-used crystals)
For each crystal: the transparency range (UV and IR edges, µm, and the absorption criterion used), the laser damage
threshold (value, unit, pulse duration, wavelength, repetition rate), the thermal conductivity (W/m·K per axis), and the
band gap (eV).

## Output format
Answer only in YAML, one block per value, exactly like this:

```yaml
- material: KTiOAsO4
  quantity: dn/dT            # dn/dT | d_ij | sellmeier | transparency | damage | conductivity | band_gap
  axis: x                    # o, e, x, y, z, or "-" for scalars
  file: 10.1364-ao.42.006661.pdf
  pdf_page: 3
  where: "Table 2, KTA y-axis column n1"
  formula: "Δn(λ,T) = n1(λ)(T − 25 °C) + n2(λ)(T − 25 °C)²,  n1 = Σ a_m/λ^m"
  values: {a0: -4.1053, a1: 44.261, a2: -38.012, a3: 11.302}
  units: "n1 in 1e-6 /°C, λ in µm"
  range: {wavelength_um: [0.532, 1.585], temperature_c: [25, 200]}
  check: "Fig. 4: n1(y) ≈ 1.37e-5 /°C at 1.064 µm"
  note: ""
```

At the end of each answer, list the papers you searched that had nothing useful, and give the DOIs of papers cited
there that would have the missing data (DOI only, so we can look for them).
