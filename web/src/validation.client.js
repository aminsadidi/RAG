// The calculators against numbers the papers publish: each case recomputes a published value with the site's own
// data and code, so the table on the site and the test that guards it always show the current state. The functions
// come in as arguments (the browser and node load the modules from different places).

const near = (v, ref, tol) => Number.isFinite(v) && Math.abs(v - ref) <= tol;

export function validationCases(f) {
  const { A, D, entryIndex, thermoShift, refractiveIndex, solveAll, effectiveD, ncpmTemperatures, solveMixing, pairRate, jointSpectrum, purity } = f;
  const source = (mat, label) => A.find((c) => c.material === mat)?.sources.find((s) => !label || s.label === label);
  const axes = (s) => (s.kind === "uniaxial" ? ["o", "o", "e"] : ["x", "y", "z"]);
  const nAt = (s) => (lam) => axes(s).map((a) => entryIndex(s.axes[a], lam));
  const nAtT = (s, T) => (lam) => axes(s).map((a) => {
    const e = s.axes[a], n0 = entryIndex(e, lam);
    return e.thermo ? n0 + thermoShift(s.thermo.form, e.thermo, s.thermo.t0_c, n0, lam, T) : n0;
  });
  const angle = (mat, label, proc, a, b, plane, type) => {
    const s = source(mat, label);
    return solveAll(nAt(s), s.kind, proc, a, b).find((r) => r.plane === plane && r.type === type)?.angle;
  };
  const deff = (mat, label, proc, a, plane, type) => {
    const s = source(mat, label), sol = solveAll(nAt(s), s.kind, proc, a).find((r) => r.plane === plane && r.type === type);
    return sol ? effectiveD(nAt(s), s.kind, sol, D[mat].d).deff : NaN;
  };
  const ncpm = (mat, label, a, pol) => {
    const s = source(mat, label);
    return ncpmTemperatures((T) => nAtT(s, T), s.kind, "shg", a, 0, D[mat]?.d, [-50, 300]).find((r) => r.pol.join("") === pol)?.T;
  };
  const qpm = (mat, label, pol, lp, ls) => {
    const s = source(mat, label), model = { kind: "qpm", nAtT: (T) => nAtT(s, T), pol, expansion: s.thermo?.expansion };
    return solveMixing(model, { lp, ls, T: 25 }, { lam: [0.4, 5], T: [-50, 300] }).roots[0]?.x;
  };
  return [
    { group: "angle", crystal: "CdSiP2", what: "type-I SHG of 4.7846 µm, θ", cite: "Kato et al. (2011)", ref: 43.13, unit: "°", tol: 0.05,
      calc: () => angle("CdSiP2", null, "shg", 4.7846, 0, "xz", "I") },
    { group: "angle", crystal: "CdSiP2", what: "type-II SHG of 5.2955 µm, θ", cite: "Kato et al. (2011)", ref: 76.47, unit: "°", tol: 0.1,
      calc: () => angle("CdSiP2", null, "shg", 5.2955, 0, "xz", "IIa") },
    { group: "angle", crystal: "GdCOB", what: "type-I SHG of 1.064 µm, xz plane, θ", cite: "Aka et al. (1997)", ref: 19.68, unit: "°", tol: 0.05,
      calc: () => angle("GdCa4O(BO3)3", null, "shg", 1.064, 0, "xz", "I") },
    { group: "angle", crystal: "GdCOB", what: "type-I SHG of 1.064 µm, xy plane, φ", cite: "Aka et al. (1997)", ref: 45.99, unit: "°", tol: 0.05,
      calc: () => angle("GdCa4O(BO3)3", null, "shg", 1.064, 0, "xy", "I") },
    { group: "angle", crystal: "ABF", what: "type-I SHG of 318.3 nm (SH 159 nm), xy plane, φ", cite: "Zhang et al., Nature (2026), Fig. 2c", ref: 88.8, unit: "°", tol: 0.5,
      note: "the site uses the 2017 equations; the paper's refined ones are not published", calc: () => angle("NH4B4O6F", "Shi-2017", "shg", 0.3183, 0, "xy", "I") },
    { group: "deff", crystal: "BBO", what: "type-I SHG of 1.064 µm, d_eff", cite: "Eckardt et al. (1990), measured", ref: 1.94, unit: "pm/V", tol: 0.12,
      calc: () => deff("BaB2O4", "Tamosauskas", "shg", 1.064, "xz", "I") },
    { group: "deff", crystal: "LBO", what: "type-I SHG of 1.064 µm, xy plane, d_eff", cite: "Sarrouf et al. (2008)", ref: 0.825, unit: "pm/V", tol: 0.025,
      calc: () => deff("LiB3O5", null, "shg", 1.064, "xy", "I") },
    { group: "deff", crystal: "KDP", what: "type-I SHG of 1.064 µm, d_eff", cite: "Wang et al. (2002)", ref: 0.26, unit: "pm/V", tol: 0.013,
      calc: () => deff("KH2PO4", null, "shg", 1.064, "xz", "I") },
    { group: "temp", crystal: "KTP", what: "noncritical SHG of 1.0795 µm (y + z → y), T", cite: "Katō & Takaoka (2002), Table 2", ref: 63.8, unit: "°C", tol: 0.3,
      calc: () => ncpm("KTiOPO4", "Kato", 1.0795, "yzy") },
    { group: "temp", crystal: "KTP", what: "noncritical SHG of 3.1842 µm (y + z → y), T", cite: "Katō & Takaoka (2002), Table 2", ref: 77.6, unit: "°C", tol: 0.3,
      calc: () => ncpm("KTiOPO4", "Kato", 3.1842, "yzy") },
    { group: "temp", crystal: "LBO", what: "noncritical type-I SHG of 1.064 µm along x, T", cite: "Ghosh (1995); measured 148.1–149.5 °C", ref: 148.7, unit: "°C", tol: 2,
      note: "the paper states ±4 °C for its own model", calc: () => ncpm("LiB3O5", "Ghosh-1995", 1.064, "zzy") },
    { group: "qpm", crystal: "PPKTP", what: "type-II SHG of 1.5822 µm, grating period", cite: "König & Wong (2004)", ref: 46.15, unit: "µm", tol: 0.05,
      calc: () => qpm("KTiOPO4", "Fradkin-König", [1, 2, 1], 0.7911, 1.5822) },
    { group: "qpm", crystal: "PPKTP", what: "DFG of 1064.4 and 1552.3 nm (all z), grating period", cite: "Fradkin et al. (1999)", ref: 35.7, unit: "µm", tol: 0.15,
      calc: () => qpm("KTiOPO4", "Fradkin-König", [2, 2, 2], 1.0644, 1.5523) },
    { group: "qpm", crystal: "PPLN", what: "SHG of 1.064 µm (e + e → e), grating period", cite: "Jundt (1997) index; the common 6.8 µm", ref: 6.8, unit: "µm", tol: 0.1,
      calc: () => qpm("LiNbO3", "Jundt-1997", [2, 2, 2], 0.532, 1.064) },
    { group: "spdc", crystal: "PPKTP", what: "type-II pairs 776 → 1552 nm, 20 mm, rate into the modes", cite: "Evans et al. (2010)", ref: 123000, unit: "pairs/s/mW", tol: 12300,
      calc: () => {
        const s = source("KTiOPO4", "Kato"), wide = (lam) => ["x", "y", "z"].map((a) => refractiveIndex(s.axes[a].type, s.axes[a].coefficients, lam));
        return pairRate({ nAt: wide, plane: "xy", angle: 0, pols: ["f", "f", "s"], lp: 0.776, l1: 1.552, L_mm: 20, dEff: 2 / Math.PI * 3.75,
          wp: 0.776 / (Math.PI * 0.0131), w1: 1.552 / (Math.PI * 0.0184), w2: 1.552 / (Math.PI * 0.0184) })?.perMw;
      } },
    { group: "spdc", crystal: "BBO", what: "type-II pairs from 400 nm, 2 mm, 4 nm pump, 5 nm filters: purity", cite: "Mosley et al. (2008), Fig. 1", ref: 0.93, unit: "", tol: 0.05,
      calc: () => {
        const s = source("BaB2O4"), n = nAt(s), sol = solveAll(n, s.kind, "opo", 0.4, 0.8).find((r) => r.type === "IIa");
        return purity(jointSpectrum({ nAt: n, plane: sol.plane, angle: sol.angle * Math.PI / 180, type: "IIa", lp: 0.4, l1: 0.8, l2: 0.8, L_mm: 2, pumpFwhmNm: 4, n: 140, filterNm: [5, 5] })).purity;
      } },
  ];
}

// Every case computed: { ...case, value, ok } (a case whose calculation fails gets value NaN).
export function runValidation(f) {
  return validationCases(f).map((c) => {
    let value = NaN;
    try { value = c.calc(); } catch { /* reported as not computed */ }
    return { ...c, value, ok: near(value, c.ref, c.tol) };
  });
}
