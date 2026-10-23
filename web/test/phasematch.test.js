// The phase-matching engine against angles published for these crystals.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { entryIndex, thermoShift } from "../src/dispersion.client.js";
import { deltaK, eigenIndices, effectiveD, fieldVectors, ncpmTemperatures, solveAll, waves } from "../src/phasematch.client.js";

const A = JSON.parse(readFileSync(new URL("../public/ri/aniso.json", import.meta.url)));
const D = JSON.parse(readFileSync(new URL("../public/ri/dij.json", import.meta.url)));
const source = (mat, label) => A.find((c) => c.material === mat).sources.find((s) => !label || s.label === label);
const nAt = (s) => (s.kind === "uniaxial"
  ? (l) => { const o = entryIndex(s.axes.o, l); return [o, o, entryIndex(s.axes.e, l)]; }
  : (l) => ["x", "y", "z"].map((a) => entryIndex(s.axes[a], l)));
const angle = (mat, label, proc, a, b, plane, type) => {
  const s = source(mat, label);
  return solveAll(nAt(s), s.kind, proc, a, b).find((r) => r.plane === plane && r.type === type)?.angle;
};

test("Fresnel equation: uniaxial limits", () => {
  const [s, f] = eigenIndices([1.66, 1.66, 1.55], [Math.sin(0.5), 0, Math.cos(0.5)]);
  assert.ok(Math.abs(s - 1.66) < 1e-12);
  const ne = 1 / Math.sqrt(Math.cos(0.5) ** 2 / 1.66 ** 2 + Math.sin(0.5) ** 2 / 1.55 ** 2);
  assert.ok(Math.abs(f - ne) < 1e-12);
});

test("published phase-matching angles", () => {
  // CdSiP2, Kato et al. 2011: type-1 SHG of 4.7846 µm at 43.13°, type 2 of 5.2955 µm at 76.47°
  assert.ok(Math.abs(angle("CdSiP2", null, "shg", 4.7846, 0, "xz", "I") - 43.13) < 0.05);
  assert.ok(Math.abs(angle("CdSiP2", null, "shg", 5.2955, 0, "xz", "IIa") - 76.47) < 0.1);
  // GdCOB, Aka et al. 1997: SHG of 1.064 µm, type I, ZX plane θ = 19.68°, XY plane φ = 45.99°
  assert.ok(Math.abs(angle("GdCa4O(BO3)3", null, "shg", 1.064, 0, "xz", "I") - 19.68) < 0.05);
  assert.ok(Math.abs(angle("GdCa4O(BO3)3", null, "shg", 1.064, 0, "xy", "I") - 45.99) < 0.05);
  // BBO, type-I SHG of 1.064 µm: 22.8° (textbook)
  assert.ok(Math.abs(angle("BaB2O4", "Tamosauskas", "shg", 1.064, 0, "xz", "I") - 22.8) < 0.2);
});

test("no phase matching where there is none: SHG to 200 nm in BBO", () => {
  const s = source("BaB2O4", "Tamosauskas");
  assert.equal(solveAll(nAt(s), s.kind, "shg", 0.4, 0).length, 0);
});

const deff = (mat, label, proc, a, b, plane, type) => {
  const s = source(mat, label), sol = solveAll(nAt(s), s.kind, proc, a, b).find((r) => r.plane === plane && r.type === type);
  return effectiveD(nAt(s), s.kind, sol, D[mat].d);
};

test("field vectors: o-wave normal to the optic axis, e-wave in the plane", () => {
  const [o, e] = fieldVectors([1.66, 1.66, 1.55], [Math.sin(0.4), 0, Math.cos(0.4)]);
  assert.ok(Math.abs(Math.abs(o[1]) - 1) < 1e-9 && Math.abs(e[1]) < 1e-9);
});

test("d_eff against values measured or reported in the collection's papers", () => {
  const near = (v, ref, tol, what) => assert.ok(Math.abs(v - ref) <= tol * ref, `${what}: ${v} vs ${ref}`);
  // Eckardt et al. 1990: measured type-I d_eff(BBO) = 1.94 pm/V (KTP: see the next test)
  near(deff("BaB2O4", "Tamosauskas", "shg", 1.064, 0, "xz", "I").deff, 1.94, 0.06, "BBO");
  // LiIO3: d31·sin(θ + ρ) with Eckardt's θ = 30.2°, ρ = 4.26°, d31 = −4.1 pm/V
  near(deff("LiIO3", null, "shg", 1.064, 0, "xz", "I").deff, 4.1 * Math.sin((30.2 + 4.26) * Math.PI / 180), 0.01, "LiIO3");
  // Sarrouf et al. 2008 / Wang et al. 2002: d_eff(LBO) ≈ 0.82–0.83, d_eff(KDP, type I) = 0.26 pm/V
  near(deff("LiB3O5", null, "shg", 1.064, 0, "xy", "I").deff, 0.825, 0.03, "LBO");
  near(deff("KH2PO4", null, "shg", 1.064, 0, "xz", "I").deff, 0.26, 0.05, "KDP");
  // Liu et al. 2014, TmCOB: 1.11 pm/V at (32.5°, 180°) and 0.67 pm/V at (32.5°, 0°)
  const tm = deff("TmCa4O(BO3)3", null, "shg", 1.064, 0, "xz", "I");
  near(tm.deff, 1.11, 0.03, "TmCOB best"); near(tm.deff - tm.spread, 0.67, 0.03, "TmCOB other side");
});

test("d_eff of the crystals from Pack et al. and Hellwig et al. against measured values", () => {
  const near = (v, ref, tol, what) => assert.ok(Math.abs(v - ref) <= tol * ref, `${what}: ${v} vs ${ref}`);
  // Adams et al., as quoted by Pack et al. 2005: GdCOB 0.78 and 0.38 pm/V on the two sides of the xz plane
  const g = deff("GdCa4O(BO3)3", null, "shg", 1.064, 0, "xz", "I");
  near(g.deff, 0.78, 0.08, "GdCOB"); near(g.deff - g.spread, 0.38, 0.12, "GdCOB other side");
  // YCOB: 1.12 and 0.69 pm/V (Adams); the Segonds indices used here are ~0.03 low in nx
  const y = deff("YCa4O(BO3)3", null, "shg", 1.064, 0, "xz", "I");
  near(y.deff, 1.12, 0.15, "YCOB"); near(y.deff - y.spread, 0.69, 0.2, "YCOB other side");
  // Hellwig et al.: BiBO type-I SHG of 1.0795 µm with k normal to b, d_eff = 3.2 pm/V
  near(deff("BiB3O6", null, "shg", 1.0795, 0, "yz", "I").deff, 3.2, 0.06, "BiBO");
  // KTP with Pack et al.'s d against Eckardt's measured 3.18 pm/V
  near(deff("KTiOPO4", null, "shg", 1.064, 0, "xy", "IIa").deff, 3.18, 0.1, "KTP (Pack)");
  // Li et al. 2016: LCB type-I THG (1.064 + 0.532 µm) in the xz plane, 0.82 and 0.57 pm/V
  const l = deff("La2CaB10O19", null, "sfg", 1.064, 0.532, "xz", "I");
  near(l.deff, 0.82, 0.05, "LCB"); near(l.deff - l.spread, 0.57, 0.05, "LCB other side");
});

test("first-order QPM periods of the poled crystals match the published ones", () => {
  // Λ = 1 / (n(λ/2)/(λ/2) − 2 n(λ)/λ) for SHG with all waves along z
  const period = (m, la) => {
    const s = A.find((c) => c.material === m).sources[0], ax = s.axes.e || s.axes.z, n = (l) => entryIndex(ax, l);
    return 1 / (n(la / 2) / (la / 2) - 2 * n(la) / la);
  };
  assert.ok(Math.abs(period("LiNbO3", 1.064) - 6.8) < 0.15);   // PPLN, 1.064 µm SHG
  assert.ok(Math.abs(period("LiNbO3", 1.55) - 19.0) < 0.5);    // PPLN, 1.55 µm SHG
  assert.ok(Math.abs(period("KTiOPO4", 1.064) - 9.0) < 0.15);  // PPKTP, 1.064 µm SHG
});

test("every source id of dij.json is a string", () => {
  for (const [m, r] of Object.entries(D)) for (const s of r.sources) if ("doc_id" in s) assert.equal(typeof s.doc_id, "string", m);
});

test("IR crystals: d_eff against the expressions of Petrov et al. 2004 and Kaindl et al. 2000", () => {
  const rad = Math.PI / 180;
  // The tensor's d_eff uses the field (not D) of the e-waves, so it is the paper's expression at θ ± ρ:
  // the walk-off of these crystals is a few degrees, hence the tolerances.
  const check = (mat, proc, a, b, type, f, tol, label) => {
    const s = source(mat, label), sol = solveAll(nAt(s), s.kind, proc, a, b).find((r) => r.type === type);
    const v = effectiveD(nAt(s), s.kind, sol, D[mat].d).deff, ref = f(sol.angle * rad);
    assert.ok(Math.abs(v - ref) <= tol * ref, `${mat}: ${v} vs ${ref}`);
  };
  // HgGa2S4 (−4): d_ooe = (d36 sin2φ + d31 cos2φ) sin θ, best φ: √(d36² + d31²) sin θ
  check("HgGa2S4", "shg", 4, 0, "I", (t) => Math.hypot(22.9, 7.6) * Math.sin(t), 0.03);
  // GaSe (−6m2): d_ooe = d22 cos θ sin3φ
  check("GaSe", "shg", 10.6, 0, "I", (t) => 57.7 * Math.cos(t), 0.03);
  // CdSe (6mm): d_oeo = d31 sin θ
  check("CdSe", "opo", 2.8, 4.0, "IIa", (t) => 18 * Math.sin(t), 0.01);
  // Te (32): d_eeo = d11 cos²θ sin3φ
  check("Te", "shg", 10.6, 0, "I", (t) => 670 * Math.cos(t) ** 2, 0.05, "Caldwell");
  // Ag3AsS3 (3m), Petrov 2012: d_ooe = d31 sin θ − d22 cos θ sin3φ, best φ: d31 sin θ + d22 cos θ
  check("Ag3AsS3", "shg", 4.0, 0, "I", (t) => 10.4 * Math.sin(t) + 16.6 * Math.cos(t), 0.03);
  // CdGeAs2 (−42m): d_eeo = d36 sin2θ cos2φ
  check("CdGeAs2", "shg", 10.6, 0, "I", (t) => 186 * Math.sin(2 * t), 0.03);
  // ZnSiAs2 (−42m), Boyd et al. 1972 on the GaAs scale of Petrov 2015
  check("ZnSiAs2", "shg", 8.0, 0, "I", (t) => 68.4 * Math.sin(2 * t), 0.03);
  // RBBF (32), Chen et al. 2009: d_ooe = d11 cos θ cos3φ; Li2B4O7 (4mm), Sugawara et al. 1998: d_ooe = d31 sin θ
  check("RbBe2BO3F2", "shg", 0.532, 0, "I", (t) => 0.45 * Math.cos(t), 0.06); // walk-off ≈ 3°
  check("Li2B4O7", "shg", 0.532, 0, "I", (t) => 0.15 * Math.sin(t), 0.03);
  // CTA, Cheng et al. 1993: type-II SHG of 1.32 µm in the x-y plane, φ = 62.8° calculated, 64.5° measured
  assert.ok(Math.abs(angle("CsTiOAsO4", "Feve-2000", "shg", 1.32, 0, "xy", "IIa") - 63.5) < 2);
});

test("LiInS2 and LiInSe2: the papers' calculated angles and d_eff", () => {
  // Fossier et al. 2004, Table IV ("Calculated"): YZ type-II SHG of 2.5527 µm at θ = 34.684°, X-Y DFG 0.77022 − 0.87224 µm at φ = 42.170°
  assert.ok(Math.abs(angle("LiInS2", "Fossier-2004", "shg", 2.5527, 0, "yz", "IIa") - 34.684) < 0.05);
  assert.ok(Math.abs(angle("LiInS2", "Fossier-2004", "opo", 0.77022, 0.87224, "xy", "IIa") - 42.17) < 0.1);
  // Petrov et al. 2010, Table 4: X-Y DFG 0.7754523 − 0.8856533 µm at φ = 54.4285°
  assert.ok(Math.abs(angle("LiInSe2", "Petrov-2010", "opo", 0.7754523, 0.8856533, "xy", "IIa") - 54.4285) < 0.1);
  // d_eff in the X-Y plane: 6.54 pm/V for LIS at φ = 42° and 9.35 pm/V for LISe at φ = 55° (Petrov et al. 2010, p. 18–19)
  const deffOf = (mat, a, b, label) => {
    const s = source(mat, label), sol = solveAll(nAt(s), s.kind, "opo", a, b).find((r) => r.plane === "xy" && r.type === "IIa");
    return effectiveD(nAt(s), s.kind, sol, D[mat].d).deff;
  };
  assert.ok(Math.abs(deffOf("LiInS2", 0.77022, 0.87224) - 6.54) < 0.15);
  assert.ok(Math.abs(deffOf("LiInSe2", 0.7754523, 0.8856533, "Petrov-2010") - 9.35) < 0.15);
});

test("LiInSe2: Katō et al. 2014 reproduce their angles, Petrov et al. 2010 the ones Katō quote for them", () => {
  // Table 1 (p. 2), "Calculated (K)": type-1 SHG in zx of 2.0520 µm at θ = 13.5°, of 10.5910 µm at 25.5°; type-2 SHG in xy of 5.2955 µm at φ = 41.0°
  assert.ok(Math.abs(angle("LiInSe2", "Kato-2014", "shg", 2.052, 0, "xz", "I") - 13.5) < 0.15);
  assert.ok(Math.abs(angle("LiInSe2", "Kato-2014", "shg", 10.591, 0, "xz", "I") - 25.5) < 0.15);
  assert.ok(Math.abs(angle("LiInSe2", "Kato-2014", "shg", 5.2955, 0, "xy", "IIa") - 41.0) < 0.15);
  // "Calculated (P)", the Petrov formula: 14.1° and 43.3° for the last two
  assert.ok(Math.abs(angle("LiInSe2", "Petrov-2010", "shg", 10.591, 0, "xz", "I") - 14.1) < 0.15);
  assert.ok(Math.abs(angle("LiInSe2", "Petrov-2010", "shg", 5.2955, 0, "xy", "IIa") - 43.3) < 0.15);
});

// Indices at T (°C) with the thermo-optic block of the source (thermo_optic.yml).
const nAtTemp = (s, T) => (lam) => (s.kind === "uniaxial" ? ["o", "o", "e"] : ["x", "y", "z"]).map((a) => {
  const e = s.axes[a], n0 = entryIndex(e, lam);
  return e.thermo ? n0 + thermoShift(s.thermo.form, e.thermo, s.thermo.t0_c, n0, lam, T) : n0;
});
const ncpm = (mat, label, proc, a, b) => {
  const s = source(mat, label);
  return ncpmTemperatures((T) => nAtTemp(s, T), s.kind, proc, a, b, D[mat]?.d, [-50, 300]);
};

test("thermo-optic formulas: the 90° phase-matching temperatures the papers calculate", () => {
  // KTP, Katō & Takaoka 2002, Table 2 "Cal": SHG of 1.0795 µm (y + z → y) at 63.8 °C, of 3.1842 µm at 77.6 °C,
  // and SFG 1.3188 + 0.6594 → 0.4396 µm at 59.8 °C. (Its OPO line, 1.0907 + 1.0390 → 0.5321 µm at 30.9 °C, is
  // not checked: the rounded wavelengths miss 1/λ1 + 1/λ2 = 1/λ3 by 1×10⁻⁵ µm⁻¹, which moves T by ~15 °C.)
  const at = (rows, pol) => rows.find((r) => r.pol.join("") === pol)?.T;
  assert.ok(Math.abs(at(ncpm("KTiOPO4", "Kato", "shg", 1.0795, 0), "yzy") - 63.8) < 0.3);
  assert.ok(Math.abs(at(ncpm("KTiOPO4", "Kato", "shg", 3.1842, 0), "yzy") - 77.6) < 0.3);
  assert.ok(Math.abs(at(ncpm("KTiOPO4", "Kato", "sfg", 1.3188, 0.6594), "yzy") - 59.8) < 0.3);
  // LiInSe2, Katō et al. 2014: type-2 SHG along y of 2.6216 µm at 25 °C, tuning by −0.128 nm/°C (Fig. 3)
  const t1 = at(ncpm("LiInSe2", "Kato-2014", "shg", 2.6216, 0), "xzx"), t2 = at(ncpm("LiInSe2", "Kato-2014", "shg", 2.6088, 0), "xzx");
  assert.ok(Math.abs(t1 - 25) < 3);
  assert.ok(Math.abs((t2 - t1) - 100) < 5);
  // LBO, Ghosh 1995: type-I SHG of 1.064 µm along x at 148.7 °C (measured 148.1–149.5); his model, as
  // implemented here, gives 153.7 °C (the paper states ±4 °C agreement for its NCPM temperatures)
  assert.ok(Math.abs(at(ncpm("LiB3O5", "Ghosh-1995", "shg", 1.064, 0), "zzy") - 148.7) < 6);
  // KNbO3, Ghosh 1994: 2n·dn/dT = G·R + H·R² with the G and H of Table II at 22 °C (n_c, n_a, n_b = x, y, z), and
  // Fig. 1 for the a axis at 3 µm, ≈ 100 (22 °C) and ≈ 170 ×10⁻⁶ /°C (140 °C)
  const kn = source("KNbO3", "Ghosh-1994");
  const twoNdn = (i, lam, T) => { const n = (t) => nAtTemp(kn, t)(lam)[i]; return 2 * n(T) * (n(T + 0.5) - n(T - 0.5)) * 1e6; };
  for (const [i, G, H, lig] of [[0, -5.04307, 264.82864, 0.2541], [1, -52.63636, 152.12376, 0.2846], [2, -152.5316, 26.6716, 0.3486]]) {
    const R = 1 / (1 - lig ** 2);
    assert.ok(Math.abs(twoNdn(i, 1, 22) - (G * R + H * R * R)) < 0.5, `KNbO3 axis ${i}: ${twoNdn(i, 1, 22)}`);
  }
  assert.ok(Math.abs(twoNdn(1, 3, 22) / 100 - 1) < 0.15 && Math.abs(twoNdn(1, 3, 140) / 170 - 1) < 0.15);
  // Congruent LiNbO3, Edwards & Lawrence 1984, Table II "T (calculated)": type-1 DFG of 488 nm and a dye laser
  const ln = source("LiNbO3", "Edwards-1984");
  for (const [ir, T] of [[2.159, 176.4], [2.249, 200.1], [2.337, 221.3], [2.432, 242.2], [2.541, 264.0], [2.643, 282.6],
    [2.771, 303.7], [2.901, 323.0], [3.049, 342.6], [3.235, 364.5]]) {
    const rows = ncpmTemperatures((t) => nAtTemp(ln, t), ln.kind, "opo", 0.488, 1 / (1 / 0.488 - 1 / ir), null, [0, 500]);
    assert.ok(Math.abs(at(rows, "yyz") - T) < 0.8, `LiNbO3 ${ir} µm: ${at(rows, "yyz")} vs ${T} °C`);
  }
});

test("thermo-optic formulas: BBO angle drift and the CdSiP2 isotropic point", () => {
  // BBO, Ghosh 1995 Table III: type-I SHG of 1.064 µm at 22.8°, dθ/dT = 12.8 µrad/°C (calculated)
  const s = source("BaB2O4", "Ghosh-1995");
  const ang = (T) => solveAll(nAtTemp(s, T), s.kind, "shg", 1.064, 0).find((r) => r.type === "I").angle;
  assert.ok(Math.abs(ang(20) - 22.8) < 0.1);
  assert.ok(Math.abs((ang(30) - ang(10)) / 20 * Math.PI / 180 * 1e6 - 12.8) < 0.5);
  // CdSiP2, Kato et al. 2011: no = ne at 0.5143 µm (300 K), 0.4998 µm (77 K) and 0.4950 µm (4.2 K)
  const c = source("CdSiP2", "Kato-2011"), wide = (e) => ({ ...e, range_um: [0.3, 7] });
  const iso = (K) => {
    const T = K - 273.15, n = (a, l) => { const e = wide(c.axes[a]), n0 = entryIndex(e, l); return n0 + thermoShift("kato", e.thermo, 25, n0, l, T); };
    let lo = 0.45, hi = 0.53; const f = (l) => n("o", l) - n("e", l);
    for (let i = 0; i < 60; i++) { const m = (lo + hi) / 2; if (Math.sign(f(m)) === Math.sign(f(lo))) lo = m; else hi = m; }
    return lo;
  };
  assert.ok(Math.abs(iso(300) - 0.5143) < 0.0005);
  assert.ok(Math.abs(iso(77) - 0.4998) < 0.001);
  assert.ok(Math.abs(iso(4.2) - 0.4950) < 0.001);
});

test("thermo-optic formulas: LBO (Kato 1994 & 2018) reproduces Table 1 90° temperatures", () => {
  const at = (rows, pol) => rows.find((r) => r.pol.join("") === pol)?.T;
  // Kato 2018 Table 1: SHG 1.0642 µm at 149 °C, 1.047 µm at 174.4 °C, 1.3188 µm at 43.0 °C, 1.206 µm at 23.6 °C
  const t_1064 = at(ncpm("LiB3O5", "Kato-1994", "shg", 1.0642, 0), "zzy");
  assert.ok(Math.abs(t_1064 - 149.0) < 0.2);
  const t_1047 = at(ncpm("LiB3O5", "Kato-1994", "shg", 1.0470, 0), "zzy");
  assert.ok(Math.abs(t_1047 - 174.4) < 0.2);
  const t_1318 = at(ncpm("LiB3O5", "Kato-1994", "shg", 1.3188, 0), "xyx");
  assert.ok(Math.abs(t_1318 - 43.0) < 0.2);
  const t_1206 = at(ncpm("LiB3O5", "Kato-1994", "shg", 1.2060, 0), "zzy");
  assert.ok(Math.abs(t_1206 - 23.6) < 0.6);
});

test("thermo-optic formulas: CLBO (Umemura et al. 1999) and RBBF (Zhai et al. 2013)", () => {
  const rad = Math.PI / 180;
  // CLBO, Table 1 "Calculated": type-1 SHG of 1.0642 µm at 29.2°, of 0.5321 µm at 61.4°
  const clbo = source("CsLiB6O10", "Umemura-1999");
  const typeI = (s, T, proc, a, b) => solveAll(nAtTemp(s, T), s.kind, proc, a, b).find((r) => r.type === "I").angle;
  assert.ok(Math.abs(typeI(clbo, 20, "shg", 1.0642, 0) - 29.2) < 0.06);
  assert.ok(Math.abs(typeI(clbo, 20, "shg", 0.5321, 0) - 61.4) < 0.06);
  // Table 2 "Calculated": temperature bandwidths ΔT·l (FWHM, °C·cm) of type-1 (o + o → e) processes, which fix
  // the signs of Eq. (2) that the PDF text loses
  const bandwidth = (l1, l2) => {
    const l3 = 1 / (1 / l1 + 1 / l2), th = typeI(clbo, 20, "sfg", l1, l2) * rad;
    const dk = (T) => {
      const n = nAtTemp(clbo, T), [o3, , e3] = n(l3);
      const ne = 1 / Math.sqrt(Math.cos(th) ** 2 / o3 ** 2 + Math.sin(th) ** 2 / e3 ** 2);
      return 2 * Math.PI * (ne / l3 - n(l1)[0] / l1 - n(l2)[0] / l2); // µm⁻¹
    };
    return 4 * 1.39156 / Math.abs((dk(21) - dk(19)) / 2) / 1e4; // sinc² FWHM, µm → cm
  };
  for (const [l1, l2, ref] of [[1.0642, 1.0642, 50.6], [1.0642, 0.5321, 17.7], [1.0642, 0.3547, 7.5], [0.5321, 0.5321, 6.0], [1.0642, 0.2660, 3.7]]) {
    const v = bandwidth(l1, l2);
    assert.ok(Math.abs(v - ref) < 0.03 * ref, `CLBO ${l1} + ${l2}: ${v} vs ${ref}`);
  }

  // RBBF, Zhai et al. 2013 Table 3 "Calculated": type-1 SHG of 532 nm at 39.97° (24 °C) and 40.09° (160 °C)
  const rbbf = source("RbBe2BO3F2", "Zhai-2013");
  assert.ok(Math.abs(typeI(rbbf, 24, "shg", 0.532, 0) - 39.97) < 0.05);
  assert.ok(Math.abs(typeI(rbbf, 160, "shg", 0.532, 0) - 40.09) < 0.05);
});

test("thermo-optic formulas: PPSLT (Dolev et al. 2009) and PPLN (Gayer et al. 2008) QPM", () => {
  // First-order period of a process from the indices of its three waves (no thermal expansion of the grating)
  const period = (mat, label, T, lf, pol) => {
    const s = source(mat, label), n = nAtTemp(s, T), ix = { o: 0, e: 2 };
    const [p1, p2, p3] = pol, f = n(lf), h = n(lf / 2);
    return 1 / (h[ix[p3]] / (lf / 2) - f[ix[p1]] / lf - f[ix[p2]] / lf);
  };
  // Dolev Table 2: 7.72 µm, SHG of 1.064 µm e-ee at 160 °C; 19.8 µm, o-eo at 25.3 °C for 1.5303 µm and e-oo at
  // 105 °C for 1.5403 µm (the last two check the ordinary index against the extraordinary one)
  assert.ok(Math.abs(period("Mg-LiTaO3", "Dolev-2009", 160, 1.064, "eee") - 7.72) < 0.03);
  assert.ok(Math.abs(period("Mg-LiTaO3", "Dolev-2009", 25.3, 1.5303, "oeo") - 19.8) < 0.1);
  assert.ok(Math.abs(period("Mg-LiTaO3", "Dolev-2009", 105, 1.5403, "ooe") - 19.8) < 0.1);
  // Gayer Fig. 4: the 19.48 µm grating of 5% MgO:CLN doubles 1530–1570 nm light (the EDFA band) from room
  // temperature to 200 °C; the paper tabulates no single point
  for (const T of [25, 200]) {
    let lo = 1.4, hi = 1.7;
    for (let i = 0; i < 60; i++) { const m = (lo + hi) / 2; (period("MgO-LiNbO3", "Gayer-5", T, m, "eee") < 19.48) ? (lo = m) : (hi = m); }
    assert.ok(lo > 1.52 && lo < 1.58, `Gayer ${T} °C: ${lo}`);
  }
});

test("Li2B4O7, AgGaGeS4 and LiGaSe2: the papers' angles and d_eff", () => {
  // Li2B4O7, Sugawara et al. 1998: type-1 SHG of 532 nm at 65.0° (calculated); 243.8 nm, the shortest SHG, at 90°
  assert.ok(Math.abs(angle("Li2B4O7", null, "shg", 0.532, 0, "xz", "I") - 65.0) < 0.3);
  assert.ok(angle("Li2B4O7", null, "shg", 0.4890, 0, "xz", "I") > 80);
  assert.equal(angle("Li2B4O7", null, "shg", 0.4860, 0, "xz", "I"), undefined);
  // LiGaSe2, Miyata, Petrov, Kato 2017, Table 1 "Calculated (K)", 20 °C
  const lgse = [["shg", 9.5525, 0, "xz", "I", 25.18], ["shg", 5.2955, 0, "xz", "I", 55.06], ["shg", 5.2955, 0, "xy", "IIa", 46.51],
    ["shg", 3.5303, 0, "xz", "I", 55.34], ["shg", 3.5303, 0, "xy", "IIa", 45.58], ["shg", 2.0520, 0, "xz", "I", 36.0],
    ["sfg", 10.591, 5.2955, "xy", "IIb", 59.09], ["sfg", 10.591, 3.5303, "xz", "I", 48.76],
    ["sfg", 5.2955, 3.5303, "xy", "IIb", 38.41], ["sfg", 5.2955, 3.5303, "xy", "IIa", 51.40]];
  for (const [p, a, b, plane, type, ref] of lgse) {
    const v = angle("LiGaSe2", null, p, a, b, plane, type);
    assert.ok(Math.abs(v - ref) < 0.1, `LiGaSe2 ${p} ${a} ${b} ${plane} ${type}: ${v} vs ${ref}`);
  }
  // Petrov 2012 Table 2: d_eff for 1.064 µm pumping to 6.45 µm with the Miller-corrected tensors. LiGaSe2:
  // 7.82 (x-z, oo-e) and 9.31 pm/V (x-y, eo-e); AgGaGeS4: 3.32 (x-z) and 5.43 pm/V (x-y), which fix its frame
  // (polar axis x; the other assignment gives ~5.2 pm/V in the x-z plane). The review used other Sellmeier
  // equations (AgGaGeS4 angles 54.0° and 35.7° against 56.2° and 37.2° here), hence the tolerances.
  const sig = 1 / (1 / 1.064 - 1 / 6.45);
  const deffWith = (mat, plane, type, d) => {
    const s = source(mat), sol = solveAll(nAt(s), s.kind, "opo", 1.064, sig).find((r) => r.plane === plane && r.type === type);
    return effectiveD(nAt(s), s.kind, sol, d).deff;
  };
  const scale = (mat, f) => Object.fromEntries(Object.entries(D[mat].d).map(([k, v]) => [k, v * f(k)]));
  const lg = scale("LiGaSe2", (k) => (["32", "24"].includes(k) ? 10 / 9.9 : 8.16 / 7.7));
  assert.ok(Math.abs(deffWith("LiGaSe2", "xz", "I", lg) - 7.82) < 0.05 * 7.82);
  assert.ok(Math.abs(deffWith("LiGaSe2", "xy", "IIa", lg) - 9.31) < 0.03 * 9.31);
  const ag = scale("AgGaGeS4", (k) => (["12", "26"].includes(k) ? 5.65 / 6.2 : 9.30 / 10.2));
  assert.ok(Math.abs(deffWith("AgGaGeS4", "xz", "I", ag) - 3.32) < 0.1 * 3.32);
  assert.ok(Math.abs(deffWith("AgGaGeS4", "xy", "I", ag) - 5.43) < 0.1 * 5.43);
});


test("thermo-optic formulas: CBO, Zhang et al. 2013", () => {
  // Type-II THG 1.064 + 0.532 → 0.355 µm in the x-y plane, φ calculated at six temperatures (p. 2)
  const s = source("CsB3O5", "Zhang-2013");
  for (const [T, phi] of [[27.8, 43.26], [40, 43.34], [90, 43.69], [140, 44.05], [160, 44.20], [190, 44.41]]) {
    const v = solveAll(nAtTemp(s, T), s.kind, "sfg", 1.064, 0.532).find((r) => r.plane === "xy" && r.type === "IIb").angle;
    assert.ok(Math.abs(v - phi) < 0.02, `CBO ${T} °C: ${v} vs ${phi}`);
  }
});

test("thermo-optic formulas: BiBO, Umemura, Miyata, Kato 2007", () => {
  // Table 1, x-z plane: calculated temperature bandwidths ΔT·l (FWHM, °C·cm) at the calculated angles; they fix
  // the signs of Eq. (2) that the PDF text loses
  const s = source("BiB3O6", "Umemura"), rad = Math.PI / 180;
  const rows = [["shg", 1.3320, 0, 8.7, 4.2], ["shg", 1.2120, 0, 38.1, 16.6], ["shg", 1.0642, 0, 53.9, 12.2],
    ["shg", 1.3422, 0, 46.4, 83.4], ["sfg", 1.6208, 1.0642, 8.2, 4.0], ["sfg", 1.6201, 1.0642, 37.0, 13.6],
    ["sfg", 1.6201, 1.0642, 43.7, 34.4], ["sfg", 1.6201, 1.0642, 52.2, 60.5], ["sfg", 1.5333, 1.0642, 7.3, 3.8]];
  for (const [p, a, b, ang, ref] of rows) {
    const sol = solveAll(nAtTemp(s, 20), s.kind, p, a, b).filter((r) => r.plane === "xz")
      .reduce((m, r) => (Math.abs(r.angle - ang) < Math.abs(m.angle - ang) ? r : m));
    assert.ok(Math.abs(sol.angle - ang) < 0.25, `BiBO ${p} ${a}: angle ${sol.angle} vs ${ang}`);
    const w = waves(p, a, b), dk = (T) => deltaK(nAtTemp(s, T), "xz", sol.angle * rad, w, sol.type);
    const v = 2 * 2.78312 / Math.abs((dk(21) - dk(19)) / 2) / 1e4;
    assert.ok(Math.abs(v - ref) < 0.03 * ref, `BiBO ${p} ${a} ${b}: ${v} vs ${ref}`);
  }
});

test("cubic semiconductors for QPM: Petrov 2015 Table 3", () => {
  // Isotropic sources: no angle phase matching at all
  const gaas = source("GaAs");
  assert.ok(gaas.isotropic);
  assert.equal(solveAll(nAt(gaas), gaas.kind, "opo", 2.09, 3.0).length, 0);
  // FM = (2·d14/π)²/n³ at 10.6 µm: 78–83 (GaAs), 20.6 (GaP), 20 pm²/V² (ZnSe)
  const fm = (mat) => { const s = source(mat), n = entryIndex(s.axes.o, 10.6); return (2 * D[mat].d["14"] / Math.PI) ** 2 / n ** 3; };
  assert.ok(fm("GaAs") > 78 && fm("GaAs") < 84, `GaAs FM ${fm("GaAs")}`);
  assert.ok(Math.abs(fm("ZnSe") - 20) < 1.5, `ZnSe FM ${fm("ZnSe")}`);
  assert.ok(Math.abs(fm("GaP") - 20.6) < 0.12 * 20.6, `GaP FM ${fm("GaP")}`);
  // "GaP and ZnSe ... will require larger grating periods in QPM structures compared to GaAs": OPO 2.09 → 3.5 µm
  const period = (mat) => { const s = source(mat), w = waves("opo", 2.09, 3.5), n = (l) => entryIndex(s.axes.o, l);
    return 1 / (n(w.l3) / w.l3 - n(w.l1) / w.l1 - n(w.l2) / w.l2); };
  assert.ok(period("GaP") > period("GaAs") && period("ZnSe") > period("GaAs"));
});

test("thermo-optic formulas of Katō et al.: AgGaS2 (1999), LiInS2 (2014), RTP (2009), BGSe (2018), GaSe (2013)", () => {
  const rad = Math.PI / 180;
  // Calculated temperature bandwidths ΔT·l (FWHM, °C·cm) at 20 °C; a row gives process, wavelengths, plane, the
  // paper's angle (or null: the solution of the plane closest in bandwidth), ΔT·l and the tolerance
  const check = (mat, label, rows) => {
    const s = source(mat, label);
    for (const [p, a, b, plane, ang, ref, tol] of rows) {
      const w = waves(p, a, b);
      const bw = (r) => { const dk = (T) => deltaK(nAtTemp(s, T), plane, r.angle * rad, w, r.type); return 2 * 2.78312 / Math.abs((dk(21) - dk(19)) / 2) / 1e4; };
      const sols = solveAll(nAtTemp(s, 20), s.kind, p, a, b).filter((r) => r.plane === plane);
      const sol = sols.reduce((m, r) => (ang !== null ? Math.abs(r.angle - ang) < Math.abs(m.angle - ang) : Math.abs(bw(r) / ref - 1) < Math.abs(bw(m) / ref - 1)) ? r : m);
      if (ang !== null) assert.ok(Math.abs(sol.angle - ang) < 0.05, `${mat} ${p} ${a} ${b}: angle ${sol.angle} vs ${ang}`);
      assert.ok(Math.abs(bw(sol) - ref) < tol * ref, `${mat} ${p} ${a} ${b}: ΔT·l ${bw(sol)} vs ${ref}`);
    }
  };
  // AgGaS2, Takaoka & Katō 1999, Table 1, column (T/K)
  check("AgGaS2", "Takaoka", [["shg", 10.2466, 0, "xz", 64.3, 131, 0.02], ["shg", 9.5525, 0, "xz", 57.4, 121, 0.02],
    ["shg", 9.2714, 0, "xz", 55.0, 118, 0.02], ["shg", 5.2955, 0, "xz", 33.2, 57.6, 0.02], ["shg", 3.5303, 0, "xz", 33.7, 22.7, 0.02]]);
  // LiInS2, Katō & Umemura 2014, Tables 1 (angles, "Calculated (K)") and 2 (ΔT·l, column K)
  check("LiInS2", "Kato-2014", [["shg", 5.2955, 0, "xy", 60.98, 233, 0.02], ["shg", 3.5303, 0, "xy", 49.95, 87.3, 0.06],
    ["sfg", 10.591, 5.2955, "xz", 16.28, 103, 0.02], ["sfg", 10.591, 3.5303, "xy", 55.60, 547, 0.02],
    ["sfg", 5.2955, 3.5303, "xy", 43.29, 102, 0.02], ["sfg", 5.2955, 3.5303, "xy", 65.30, 144, 0.02],
    ["sfg", 5.2955, 3.5303, "yz", 10.43, 332, 0.02]]);
  // RTP, Mikami, Okamoto, Katō 2009, Table 1 "Cal" (the two SFG rows at 0.4461 µm, which the paper says it does
  // not reproduce, are left out)
  check("RbTiOPO4", "Mikami-2009", [["shg", 1.0642, 0, "xy", null, 153, 0.05], ["shg", 1.0642, 0, "yz", null, 70.9, 0.02],
    ["shg", 1.3382, 0, "xz", null, 52.5, 0.02], ["shg", 3.1842, 0, "yz", null, 79.9, 0.02], ["shg", 3.1842, 0, "xy", null, 154, 0.02],
    ["sfg", 1.5710, 1.0642, "xz", null, 35.5, 0.02], ["sfg", 1.9079, 1.0642, "yz", null, 89.3, 0.02]]);
  // BaGa4Se7, Katō, Miyata, Badikov, Petrov 2018, Table 1 (angles and ΔT·l, column K)
  check("BaGa4Se7", "Kato", [["shg", 10.591, 0, "xz", 52.01, 42.6, 0.02], ["shg", 10.591, 0, "yz", 57.04, 82.2, 0.02],
    ["shg", 5.2955, 0, "xz", 39.34, 17.0, 0.02], ["shg", 5.2955, 0, "xz", 49.04, 20.4, 0.02], ["shg", 5.2955, 0, "yz", 21.85, 33.4, 0.02],
    ["shg", 3.5303, 0, "xz", 43.30, 11.5, 0.02], ["shg", 3.5303, 0, "xz", 57.10, 13.9, 0.02], ["shg", 3.5303, 0, "yz", 34.33, 21.9, 0.02]]);
  // Hg1−xCdxGa2S4, Katō, Umemura, Petrov 2017, Table 1 "cal": Eqs. (1)–(5) (the mixed-crystal formula of HgGa2S4
  // and CdGa2S4 Sellmeier and thermo-optic equations), angles and ΔT·l at 20 °C
  // (SHG of 5.2955 µm phase-matches near 90°, where the angle is most sensitive: 78.63° here, 78.73° in the paper)
  check("Hg0.35Cd0.65Ga2S4", "Kato-2017", [["shg", 5.2955, 0, "xz", null, 110, 0.02], ["sfg", 5.2955, 3.5303, "xz", 65.96, 84.0, 0.02],
    ["shg", 3.5303, 0, "xz", 66.41, 59.1, 0.02]]);
  const hc = source("Hg0.35Cd0.65Ga2S4", "Kato-2017");
  assert.ok(Math.abs(solveAll(nAtTemp(hc, 20), hc.kind, "shg", 5.2955, 0).find((r) => r.type === "I").angle - 78.73) < 0.15);
  check("Hg0.51Cd0.49Ga2S4", "Kato-2017", [["sfg", 10.591, 2.6478, "xz", 72.29, 84.4, 0.02], ["shg", 2.6478, 0, "xz", 68.71, 27.4, 0.02]]);
  // AgGaSe2, Tanaka & Katō 1998, Table 1 "Calculated" ΔT·l (angles rounded to 0.1° in the paper)
  check("AgGaSe2", "Harasaki", [["shg", 10.591, 0, "xz", 55.5, 351, 0.03], ["shg", 5.2955, 0, "xz", 41.3, 225, 0.03],
    ["sfg", 10.591, 5.2955, "xz", 42.4, 390, 0.03], ["sfg", 10.591, 3.5303, "xz", 41.3, 225, 0.03]].map((r) => [...r.slice(0, 4), null, ...r.slice(5)]));
  // CsTiOAsO4, Mikami, Okamoto, Katō 2011, Tables I and II ("Calculated"); type-2 SHG and SFG
  check("CsTiOAsO4", "Mikami-2011", [["shg", 1.3188, 0, "yz", 77.4, 8.9, 0.03], ["shg", 1.3188, 0, "xy", null, 8.9, 0.03],
    ["shg", 1.5556, 0, "xy", null, 10.4, 0.03], ["sfg", 1.9059, 0.7382, "xy", null, 8.6, 0.03], ["sfg", 1.3408, 1.0642, "xy", null, 7.5, 0.03]]);
  { // the remaining calculated loci of Table I, to 0.3° (66.01° vs 66.2°, 12.74° vs 13.0°, 72.49° vs 72.5°)
    const s = source("CsTiOAsO4", "Mikami-2011"), at = (p, a, b, plane) => solveAll(nAtTemp(s, 20), s.kind, p, a, b).find((x) => x.plane === plane && x.type !== "I").angle;
    for (const [p, a, b, plane, ref] of [["shg", 1.3188, 0, "xy", 66.2], ["sfg", 1.9059, 0.7382, "xy", 13.0], ["sfg", 1.8645, 1.0642, "xz", 72.5]]) {
      assert.ok(Math.abs(at(p, a, b, plane) - ref) < 0.3, `CTA ${p} ${a} ${b}: ${at(p, a, b, plane)} vs ${ref}`);
    }
  }
  // AgGaS2, Katō, Okamoto, Grechin, Umemura 2019, Table 1 "Calculated" (angles rounded to 0.1° in the paper),
  // and the type-1 90° SHG of 1.7718 µm at 20 °C (p. 2)
  check("AgGaS2", "Kato-2019", [["shg", 10.591, 0, "xz", null, 35.5, 0.02], ["shg", 5.2955, 0, "xz", null, 20.8, 0.02],
    ["shg", 3.5303, 0, "xz", null, 15.2, 0.02], ["sfg", 10.591, 5.2955, "xz", null, 28.5, 0.02]]);
  { const s = source("AgGaS2", "Kato-2019"), T = ncpmTemperatures((t) => nAtTemp(s, t), s.kind, "shg", 1.7718, 0, null, [-50, 200])[0].T;
    assert.ok(Math.abs(T - 20) < 1, `AgGaS2 90° SHG of 1.7718 µm at ${T} °C`); }
  // GaS0.4Se0.6, Katō & Mikami 2014, Table 1: type-1 SHG, calculated external angles from the c axis at 20 °C
  // (sin θext = no(λ1) sin θint). The SFG rows are not checked: their two inputs, collinear outside, refract to
  // different internal angles (non-collinear inside), which this collinear engine does not model.
  const gs = source("GaS0.4Se0.6");
  for (const [lam, ext] of [[10.591, 56.21], [5.2955, 31.12], [3.5303, 35.06]]) {
    const th = solveAll(nAtTemp(gs, 20), gs.kind, "shg", lam, 0).find((r) => r.type === "I").angle * rad;
    const v = Math.asin(nAtTemp(gs, 20)(lam)[0] * Math.sin(th)) / rad;
    assert.ok(Math.abs(v - ext) < 0.03, `GaS0.4Se0.6 SHG ${lam} µm: ${v}° vs ${ext}°`);
  }
  // GaSe, Katō, Tanno, Umemura 2013, p. 3: type-1 SHG of 9.5862 µm at θint = 13.61° (20 °C), 13.51° (225 °C), 13.71° (−165 °C)
  const g = source("GaSe", "Kato");
  for (const [T, th] of [[20, 13.61], [225, 13.51], [-165, 13.71]]) {
    const v = solveAll(nAtTemp(g, T), g.kind, "shg", 9.5862, 0).find((r) => r.type === "I").angle;
    assert.ok(Math.abs(v - th) < 0.03, `GaSe ${T} °C: ${v} vs ${th}`);
  }
});

test("thermo-optic formulas of Bhar & Ghosh (1979): Table II reproduces the high-temperature Sellmeier rows of Table I", () => {
  for (const [mat, lo, hi, T] of [["ZnGeP2", "Boyd-20C", "Boyd-70C", 70], ["CdGeP2", "Boyd-20", "Boyd-118", 118], ["CuGaS2", "Boyd-20", "Boyd-120", 120]]) {
    const s = source(mat, lo), h = source(mat, hi);
    for (const ax of ["o", "e"]) for (const lam of [1, 2, 4, 8, 10.6]) {
      const n0 = entryIndex(s.axes[ax], lam), d = thermoShift(s.thermo.form, s.axes[ax].thermo, s.thermo.t0_c, n0, lam, T);
      const ref = entryIndex(h.axes[ax], lam) - n0;
      assert.ok(Math.abs(d - ref) < 0.02 * ref, `${mat} ${ax} ${lam} µm: Δn ${d} vs ${ref}`);
    }
  }
});

test("thermo-optic formula of ADP, Ghosh & Bhar (1982): Table III, 'Our calculated'", () => {
  const s = source("NH4H2PO4", "Ghosh-1982");
  const T = (p, a, b) => ncpmTemperatures((t) => nAtTemp(s, t), s.kind, p, a, b, null, [-200, 200]).find((r) => r.pol.join("") === "yyz")?.T;
  // 90° type-I SHG and SFG, within the paper's ΔT' (±4 °C); "1.06 FHG" is SHG of 0.532 µm
  for (const [p, a, b, ref] of [["shg", 0.532, 0, 48], ["shg", 0.4965, 0, -96], ["shg", 0.5017, 0, -70], ["shg", 0.5145, 0, -13],
    ["sfg", 0.347, 0.78, -21], ["sfg", 0.347, 0.86, 66], ["sfg", 1.064, 0.302, 96]]) {
    assert.ok(Math.abs(T(p, a, b) - ref) < 4, `ADP ${p} ${a} ${b}: ${T(p, a, b)} vs ${ref} °C`);
  }
  // type-I SHG at 20 °C: 70° at 0.56 µm to 58° at 0.63 µm
  for (const [lam, ang] of [[0.56, 70], [0.63, 58]]) {
    const v = solveAll(nAtTemp(s, 20), s.kind, "shg", lam, 0).find((r) => r.type === "I").angle;
    assert.ok(Math.abs(v - ang) < 1.5, `ADP SHG ${lam} µm: ${v}° vs ${ang}°`);
  }
});

test("thermo-optic formula of HgGa2S4, Mangin et al. (2009): Table 1 and the OPO tuning of Figs. 4 and 6", () => {
  const s = source("HgGa2S4", "Mangin-2009"), rad = Math.PI / 180;
  // β = (1/n)dn/dT = a0 + a1·T (Table 1), o and e
  for (const [lam, o0, o1, e0, e1] of [[0.6328, 3.43, 4.45, 3.46, 4.44], [1.064, 2.37, 2.80, 2.49, 2.56], [3.39, 2.05, 2.26, 2.11, 2.29], [10.6, 2.03, 1.69, 2.07, 2.13]]) {
    for (const T of [0, 100]) {
      const b = (i) => { const n = (t) => nAtTemp(s, t)(lam)[i]; return (n(T + 0.5) - n(T - 0.5)) / n(T) * 1e5; };
      assert.ok(Math.abs(b(0) - (o0 + o1 * T / 1000)) < 0.02 && Math.abs(b(2) - (e0 + e1 * T / 1000)) < 0.02, `HGS β at ${lam} µm, ${T} °C`);
    }
  }
  // type-I OPO pumped at 1.0642 µm: signal at 20 °C (Fig. 4a) and idler slope from 20 to 80 °C (Fig. 6, "this work")
  const opo = (th, T) => { let lo = 1.2, hi = 2.1; const f = (sg) => deltaK(nAtTemp(s, T), "xz", th * rad, waves("opo", 1.0642, sg), "I");
    for (let i = 0; i < 60; i++) { const m = (lo + hi) / 2; if (Math.sign(f(m)) === Math.sign(f(lo))) lo = m; else hi = m; } return 1 / (1 / 1.0642 - 2 / (lo + hi)); };
  for (const [th, slope] of [[50.94, 1.99], [51.48, 1.96], [51.95, 1.935], [52.51, 1.905], [53.05, 1.88], [53.69, 1.86], [54.27, 1.84], [55.30, 1.815]]) {
    const v = (opo(th, 80) - opo(th, 20)) / 60 * 1000;
    assert.ok(Math.abs(v - slope) < 0.015, `HGS ${th}°: ${v} vs ${slope} nm/K`);
  }
  for (const [th, sig] of [[50.94, 1388], [55.30, 1489]]) {
    const v = 1 / (1 / 1.0642 - 1 / opo(th, 20)) * 1000;
    assert.ok(Math.abs(v - sig) < 3, `HGS ${th}°: signal ${v} vs ${sig} nm`);
  }
});

test("GaAs, Skauli et al. 2003: temperature-dependent Sellmeier (Table II) against their QPM SHG data and dn/dT", () => {
  const s = source("GaAs", "Skauli"), n = (lam, T) => nAtTemp(s, T)(lam)[0];
  // Table I: equivalent first-order periods and SHG wavelengths at 21 °C, Λ = λω / (2(n2ω − nω))
  for (const [per, l2] of [[61.2, 2.0659], [38.6, 1.7575], [26.3, 1.5468], [20.40, 1.4273], [12.24, 1.2203], [6.80, 1.0314], [5.56, 0.9791]]) {
    const v = 2 * l2 / (2 * (n(l2, 21) - n(2 * l2, 21)));
    assert.ok(Math.abs(v / per - 1) < 0.007, `GaAs Λ ${v} vs ${per} µm`);
  }
  // Fig. 5 at 22 °C: dn/dT ≈ 2.92e-4 at 1.064 µm and ≈ 1.97e-4 at 10 µm; d²n/dT² ≈ 3.4e-7 at 1.064 µm
  const d1 = (l) => (n(l, 23) - n(l, 21)) / 2, d2 = (l) => (n(l, 32) - 2 * n(l, 22) + n(l, 12)) / 100;
  assert.ok(Math.abs(d1(1.064) / 2.92e-4 - 1) < 0.02 && Math.abs(d1(10) / 1.97e-4 - 1) < 0.03 && Math.abs(d2(1.064) / 3.4e-7 - 1) < 0.1);
});

test("CdSe, Bhar & Ghosh 1980: the straight-line fit reproduces the Sellmeier rows of Table I", () => {
  const s = source("CdSe", "Lisitsa"), E = 1800;
  const row = { o: { 300: [3.9090, 2.1605, 0.2129, 1.4533], [-200]: [4.1428, 1.7785, 0.2129, 1.4540] },
    e: { 300: [3.8585, 2.3128, 0.2033, 1.5663], [-200]: [4.0374, 1.9738, 0.1977, 1.5670] } };
  const nr = ([A, B, C, D], l) => Math.sqrt(A + B / (1 - C / (l * l)) + D / (1 - E / (l * l)));
  for (const [i, ax] of [[0, "o"], [2, "e"]]) for (const l of [2, 5, 10]) {
    const shift = nAtTemp(s, 300)(l)[i] - nAtTemp(s, -200)(l)[i], ref = nr(row[ax][300], l) - nr(row[ax][-200], l);
    assert.ok(Math.abs(shift - ref) < 1e-4, `CdSe ${ax} ${l} µm: ${shift} vs ${ref}`);
  }
});

test("GaP, Wei et al. 2018: temperature-dependent Sellmeier against the OP-GaP grating periods of Table 1", () => {
  const s = source("GaP", "Wei-2018"), n = (l) => nAtTemp(s, 20)(l)[0];
  // first-order QPM: 1/Λ = n_p/λp − n_s/λs − n_i/λi; Table 1 "Λ Exp." with the measured wavelengths. The table's
  // third row prints signal 8.236 µm (the idler of row 2; 1/2.09 ≠ 1/8.236 + 1/5.1): the text (p. 2) gives (3.54, 5.1)
  // (the idler follows from 1/λi = 1/λp − 1/λs; its rounded printed value moves Λ by several per cent)
  for (const [p, sg, per] of [[1.064, 1.385, 20.8], [1.559, 1.923, 61.1], [2.09, 3.54, 92.7]]) {
    const id = 1 / (1 / p - 1 / sg), v = 1 / (n(p) / p - n(sg) / sg - n(id) / id);
    assert.ok(Math.abs(v / per - 1) < 0.01, `GaP Λ ${v} vs ${per} µm`);
  }
  // n increases with temperature (Fig. 3)
  assert.ok(nAtTemp(s, 150)(5)[0] > nAtTemp(s, 20)(5)[0]);
});

test("YCOB and GdCOB, Loiko et al. 2015: Eq. (2) gives the thermo-optic coefficients of Table 3 near 1 µm", () => {
  for (const [mat, label, ref] of [["YCa4O(BO3)3", "Segonds-2004", [-1.2, -3.7, -2.5]], ["GdCa4O(BO3)3", "Aka-1997", [-3.8, -4.8, -3.7]]]) {
    const s = source(mat, label);
    for (let i = 0; i < 3; i++) {
      const v = (nAtTemp(s, 21)(1.03)[i] - nAtTemp(s, 19)(1.03)[i]) / 2 * 1e6;
      assert.ok(Math.abs(v - ref[i]) < 0.15, `${mat} axis ${i}: ${v} vs ${ref[i]}`);
    }
  }
});

test("handbook data (Dmitriev et al. 1999) checked against the book's and Petrov's own numbers", () => {
  // Ag3SbS3: the book's Sellmeier equations give its θtheor = 23.34° (SHG 10.59 µm) and Petrov 2015's Table 2
  // angles for 1.064 µm → 6.45 µm, 47.14° (oo-e) and 52.84° (eo-e)
  const s = source("Ag3SbS3"), nAt = nAtTemp(s, 20);
  assert.ok(Math.abs(solveAll(nAt, s.kind, "shg", 10.59, 0).find((r) => r.type === "I").angle - 23.34) < 0.02);
  const opo = solveAll(nAt, s.kind, "opo", 1.064, 1 / (1 / 1.064 - 1 / 6.45));
  assert.ok(Math.abs(opo.find((r) => r.type === "I").angle - 47.14) < 0.02 && Math.abs(opo.find((r) => r.type === "IIa").angle - 52.84) < 0.02);
  for (const m of ["HgS", "Se", "Ag3SbS3"]) assert.ok(D[m], m);
});

test("DKDP (Kirby & DeShazer 1987 with the dn/dT of Barnes et al. 1982): noncritical SHG of 532 nm near the measured 42–49 °C, tuning near the measured 0.068 nm/K", async () => {
  const fs = await import("node:fs");
  const { refractiveIndex, thermoShift } = await import("../src/dispersion.client.js");
  const A = JSON.parse(fs.readFileSync(new URL("../public/ri/aniso.json", import.meta.url)));
  const s = A.find((x) => x.material === "KD2PO4").sources.find((x) => x.label === "Kirby-1987");
  const n = (ax, lam, T) => {
    const n0 = refractiveIndex(s.axes[ax].type, s.axes[ax].coefficients, lam);
    return n0 + thermoShift(s.thermo.form, s.axes[ax].thermo, s.thermo.t0_c, n0, lam, T);
  };
  const D = (lam, T) => n("e", lam / 2, T) - n("o", lam, T);
  const bis = (f, lo, hi) => { for (let i = 0; i < 90; i++) { const m = (lo + hi) / 2; (Math.sign(f(m)) === Math.sign(f(lo))) ? lo = m : hi = m; } return (lo + hi) / 2; };
  const T = bis((t) => D(0.5321, t), -50, 200);
  assert.ok(T > 40 && T < 61, `T = ${T}`);
  const rate = (bis((l) => D(l, 43), 0.48, 0.56) - bis((l) => D(l, 33), 0.48, 0.56)) / 10 * 1000;
  assert.ok(Math.abs(rate - 0.068) < 0.015, `rate = ${rate}`);
});

test("ZnSe and CdTe dn/dT (Johnston 1977, Fig. 2): 2n·dn/dT read off the figure", async () => {
  const A = JSON.parse(readFileSync(new URL("../public/ri/aniso.json", import.meta.url)));
  const twoNdndT = (m, label, lam) => {
    const s = A.find((x) => x.material === m).sources.find((x) => x.label === label), e = s.axes.o, n0 = entryIndex(e, lam);
    return 2 * n0 * thermoShift(s.thermo.form, e.thermo, s.thermo.t0_c, n0, lam, s.thermo.t0_c + 1) * 1e4;
  };
  for (const [lam, v] of [[0.633, 4.7], [1.15, 2.95], [3.39, 2.6], [10.6, 2.45]]) assert.ok(Math.abs(twoNdndT("ZnSe", "Connolly", lam) - v) < 0.2, `ZnSe ${lam}`);
  assert.ok(Math.abs(twoNdndT("CdTe", "Marple", 1.15) - 8.2) < 0.3);
});

test("BGSe (Kato et al. 2023): measured 90° type-2 DFG temperatures 112 and 149 °C, calculated OPO angles 4.83° and 6.94°", () => {
  const A = JSON.parse(readFileSync(new URL("../public/ri/aniso.json", import.meta.url)));
  const s = A.find((x) => x.material === "BaGa4Se7").sources.find((x) => x.label === "Kato-2023");
  const n = (ax, lam, T) => { const n0 = entryIndex(s.axes[ax], lam); return n0 + thermoShift(s.thermo.form, s.axes[ax].thermo, s.thermo.t0_c, n0, lam, T); };
  const ne = (lam, th, T) => 1 / Math.sqrt(Math.cos(th) ** 2 / n("y", lam, T) ** 2 + Math.sin(th) ** 2 / n("z", lam, T) ** 2);
  const dk = (lp, li, T, th) => { const ls = 1 / (1 / lp - 1 / li); return n("x", lp, T) / lp - ne(ls, th, T) / ls - n("x", li, T) / li; };
  const bis = (f, lo, hi) => { for (let i = 0; i < 90; i++) { const m = (lo + hi) / 2; (Math.sign(f(m)) === Math.sign(f(lo))) ? lo = m : hi = m; } return (lo + hi) / 2; };
  assert.ok(Math.abs(bis((T) => dk(1.9, 8.853, T, 0), 20, 300) - 112) < 1);
  assert.ok(Math.abs(bis((T) => dk(1.98, 14.201, T, 0), 20, 300) - 149) < 1);
  for (const [li, deg] of [[8.9257, 4.83], [8.244, 6.94]]) assert.ok(Math.abs(bis((t) => dk(2.0907, li, 20, t), 0, 0.5) * 180 / Math.PI - deg) < 0.02);
});

test("thermo-optic: KDP (Phillips 1966) tuning rate and KTA (Emanueli & Arie 2003) n1", () => {
  const kdp = source("KH2PO4", "Zernike");
  const n = (s, ax, l, T) => entryIndex(s.axes[ax], l) + thermoShift(s.thermo.form, s.axes[ax].thermo, s.thermo.t0_c, entryIndex(s.axes[ax], l), l, T);
  // 90° type-I SHG, no(λ) = ne(λ/2): 0.045 nm/K at 0.517 µm (measured 0.048 nm/K)
  const f = (l, T) => n(kdp, "e", l / 2, T) - n(kdp, "o", l, T);
  let lo = 0.49, hi = 0.55; for (let i = 0; i < 60; i++) { const m = (lo + hi) / 2; f(lo, 24.85) * f(m, 24.85) <= 0 ? hi = m : lo = m; }
  const rate = -((f(lo, 25.85) - f(lo, 23.85)) / 2) / ((f(lo + 1e-5, 24.85) - f(lo - 1e-5, 24.85)) / 2e-5) * 1000;
  assert.ok(Math.abs(rate - 0.048) < 0.006, `KDP tuning rate ${rate}`);
  // KTA n1 = dn/dT at 25 °C, Fig. 4: z 3.0e-5 at 0.532 µm, y 1.37e-5 at 1.064 µm
  const kta = source("KTiOAsO4", "Feve-2000"), d = (ax, l) => (n(kta, ax, l, 26) - n(kta, ax, l, 24)) / 2;
  assert.ok(Math.abs(d("z", 0.532) - 2.97e-5) < 0.1e-5 && Math.abs(d("y", 1.064) - 1.33e-5) < 0.1e-5);
  assert.equal(kta.thermo.partial, true);
});

test("KABO (Umemura et al. 2003): type-I SHG angles of Table 1 and temperature bandwidths of Table 2", () => {
  const s = source("K2Al2B2O7", "Umemura-2003");
  const n = (ax, l, T) => entryIndex(s.axes[ax], l) + thermoShift(s.thermo.form, s.axes[ax].thermo, s.thermo.t0_c, entryIndex(s.axes[ax], l), l, T);
  const nth = (l, th, T) => 1 / Math.sqrt(Math.cos(th) ** 2 / n("o", l, T) ** 2 + Math.sin(th) ** 2 / n("e", l, T) ** 2);
  for (const [l1, angle, bw] of [[1.0642, 27.3, 41.9], [0.5321, 57.2, 4.1]]) {
    const f = (th, T) => nth(l1 / 2, th, T) - n("o", l1, T);
    let lo = 0.01, hi = 1.57; for (let i = 0; i < 80; i++) { const m = (lo + hi) / 2; f(lo, 20) * f(m, 20) <= 0 ? hi = m : lo = m; }
    assert.ok(Math.abs(lo * 180 / Math.PI - angle) < 0.3, `angle at ${l1}`);
    const dk = 4 * Math.PI / (l1 * 1e-4) * (f(lo, 21) - f(lo, 19)) / 2; // cm⁻¹ per °C
    assert.ok(Math.abs(5.566 / Math.abs(dk) / bw - 1) < 0.05, `ΔT·l at ${l1}: ${5.566 / Math.abs(dk)}`);
  }
});

test("BaGa4Se7 d_ij (Guo et al. 2022): d_eff in the three principal planes, Eqs. (3)–(5)", () => {
  // Monoclinic: θ on the two sides of an axis are different directions. The paper's sphere gives one of them
  // (Eqs. 3–5, e.g. |d21 cosθ − d31 sinθ| in yz); the other has the + sign. The site reports the larger as deff
  // and their difference as spread. Walk-off neglected.
  const s = source("BaGa4Se7"), n = nAt(s);
  for (const [l, plane, type, A, B] of [[3.3, "yz", "IIa", 5.3, 1.5], [2.3, "yz", "IIa", 5.3, 1.5],
    [2.5, "xz", "I", 5.3, 14.2], [2.4, "xy", "IIa", -5.0, -1.5]]) {
    const sol = solveAll(n, s.kind, "shg", l, 0).find((r) => r.plane === plane && r.type === type);
    const sq = plane !== "yz", t = sol.angle * Math.PI / 180, [c, si] = sq ? [Math.cos(t) ** 2, Math.sin(t) ** 2] : [Math.cos(t), Math.sin(t)];
    // xz (Eq. 4, d21 cos²θ + d23 sin²θ) and xy (Eq. 5, d31 sin²φ + d32 cos²φ) are the same on both sides
    const r = effectiveD(n, s.kind, sol, D.BaGa4Se7.d);
    const hi = sq ? Math.abs(A * c - B * si) : Math.abs(A * c) + Math.abs(B * si);
    const lo = sq ? hi : Math.abs(Math.abs(A * c) - Math.abs(B * si));
    assert.ok(Math.abs(r.deff - hi) < 0.12 * hi + 0.2, `${plane} ${type} at ${l} µm: ${r.deff} vs ${hi}`);
    assert.ok(Math.abs(r.deff - r.spread - lo) < 0.12 * hi + 0.2, `${plane} ${type} at ${l} µm, other side: ${r.deff - r.spread} vs ${lo}`);
  }
});

test("thermo-optic formulas of SiC, GaN, AlN and YVO4 reproduce the papers' values", () => {
  const dndt = (mat, label, ax, lam, T) => {
    const s = source(mat, label), e = s.axes[ax], n0 = entryIndex(e, lam);
    return (thermoShift(s.thermo.form, e.thermo, s.thermo.t0_c, n0, lam, T + 0.5) - thermoShift(s.thermo.form, e.thermo, s.thermo.t0_c, n0, lam, T - 0.5));
  };
  const shift = (mat, label, ax, lam, T) => { const s = source(mat, label), e = s.axes[ax];
    return thermoShift(s.thermo.form, e.thermo, s.thermo.t0_c, entryIndex(e, lam), lam, T); };
  // Xu et al. 2014, p. 4: no of 4H-SiC at 450 nm and 493 K, 8.18e-5 /K; of 6H-SiC at 1523 nm and 493 K, 5.94e-5 /K
  assert.ok(Math.abs(dndt("SiC", "Wang-4H", "o", 0.45, 493 - 273.15) - 8.18e-5) < 0.35e-5);
  assert.ok(Math.abs(dndt("SiC", "Wang-6H", "o", 1.523, 493 - 273.15) - 5.94e-5) < 0.1e-5);
  // Watanabe et al. 2008, Fig. 2: no of GaN at 500 nm 2.415 -> 2.465, of AlN at 250 nm 2.33 -> 2.375, from about 20 to 515 °C
  assert.ok(Math.abs(shift("GaN", "Sanford-2003", "o", 0.5, 515) - 0.050) < 0.005);
  assert.ok(Math.abs(shift("AlN", "Pastrnak", "o", 0.25, 515) - 0.045) < 0.005);
  // Loiko et al. 2013, Table 2 (10^-6 /K): YVO4 dno/dT and dne/dT
  for (const [lam, o, e] of [[0.53, 7.5, 4.1], [0.63, 5.3, 2.3], [1.06, 3.1, 0.6], [1.54, 2.6, 0.2], [2.05, 2.4, 0.1]]) {
    assert.ok(Math.abs(dndt("YVO4", "Birnbaum", "o", lam, 25) * 1e6 - o) < 0.1, `YVO4 o ${lam}`);
    // beyond the 0.4–1.1 µm of the fit the formula's dne/dT is up to 0.11 below the table's
    assert.ok(Math.abs(dndt("YVO4", "Birnbaum", "e", lam, 25) * 1e6 - e) < (lam > 1.1 ? 0.15 : 0.1), `YVO4 e ${lam}`);
  }
});

test("Ba2NaNb5O15, Pomeroy (1971): noncritical SHG of 1.064 µm at 372.2 K (nb, nc) and 345.2 K (na, nc)", () => {
  const s = source("Ba2NaNb5O15", "Pomeroy-1971");
  const n = (ax, lam, T) => { const e = s.axes[ax], n0 = entryIndex(e, lam); return n0 + thermoShift(s.thermo.form, e.thermo, s.thermo.t0_c, n0, lam, T); };
  const root = (f) => { let lo = 0, hi = 200; for (let i = 0; i < 60; i++) { const m = (lo + hi) / 2; if ((f(lo) > 0) === (f(m) > 0)) lo = m; else hi = m; } return lo; };
  // here x = c, y = a, z = b
  assert.ok(Math.abs(root((T) => n("z", 1.064, T) - n("x", 0.532, T)) + 273.15 - 372.2) < 1);
  assert.ok(Math.abs(root((T) => n("y", 1.064, T) - n("x", 0.532, T)) + 273.15 - 345.2) < 1);
});

test("papers from proDownloads: LCB and NLBO temperature-dependent THG angles, KBBF SHG angles", () => {
  const thg = (mat, label, T, plane, type) => {
    const s = source(mat, label);
    return solveAll(nAtTemp(s, T), s.kind, "sfg", 1.064, 0.532).find((r) => r.plane === plane && r.type === type)?.angle;
  };
  // LCB, Zhai et al. 2013, Table 4 "Calculated": type-I THG in the yz plane at 25, 40, 80, 110, 155, 170 °C
  for (const [T, a] of [[25, 48.8], [40, 48.9], [80, 49.1], [110, 49.3], [155, 49.6], [170, 49.7]]) {
    assert.ok(Math.abs(thg("La2CaB10O19", "Zhai-2013", T, "yz", "I") - a) < 0.06, `LCB ${T} °C`);
  }
  // NLBO, Shan et al. 2014, p. 4: THG at room temperature, 49.8° (ooe) and 65.3° (eoe)
  assert.ok(Math.abs(thg("Na3La9O3(BO3)8", "Shan-2014", 23.5, "xz", "I") - 49.8) < 0.05);
  assert.ok(Math.abs(thg("Na3La9O3(BO3)8", "Shan-2014", 23.5, "xz", "IIb") - 65.3) < 0.05);
  assert.ok(thg("Na3La9O3(BO3)8", "Shan-2014", 160, "xz", "I") > 50); // the angles grow with temperature (Fig. 4)
  // KBBF, Wu et al. 1996, Table 2 "Cal.": type-I SHG angles
  for (const [l, a] of [[1.342, 18.84], [1.064, 19.86], [0.532, 36.37], [0.41, 51.22], [0.3695, 61.02]]) {
    assert.ok(Math.abs(angle("KBe2BO3F2", "Wu-1996", "shg", l, 0, "xz", "I") - a) < 0.06, `KBBF ${l} µm`);
  }
});

test("thermo-optic: BaTiO3 (Buse et al. 1993) and sapphire (Thomas et al. 1998)", () => {
  // BaTiO3 Table 3: dne/dT (10⁻⁵ /K) at 488, 514, 532, 633 nm and 20–80 °C; no constant
  const b = source("BaTiO3", "Buse-1993");
  const dndt = (s, ax, lam, T) => thermoShift(s.thermo.form, s.axes[ax].thermo, s.thermo.t0_c, entryIndex(s.axes[ax], lam), lam, T + 0.5)
    - thermoShift(s.thermo.form, s.axes[ax].thermo, s.thermo.t0_c, entryIndex(s.axes[ax], lam), lam, T - 0.5);
  const table = { 20: [26, 25, 23, 18], 40: [28, 25, 23, 19], 60: [37, 34, 33, 30], 80: [56, 51, 49, 41] };
  for (const [T, row] of Object.entries(table)) {
    [0.488, 0.514, 0.532, 0.633].forEach((lam, i) => {
      const tol = lam === 0.633 && T >= 60 ? 4.5 : 1.5;
      assert.ok(Math.abs(dndt(b, "e", lam, +T) * 1e5 - row[i]) < tol, `BaTiO3 ${lam} µm ${T} °C`);
    });
  }
  assert.equal(dndt(b, "o", 0.6, 50), 0);
  // Sapphire: the model's electronic oscillators are close to Malitson's UV Sellmeier terms (0.0727 and
  // 0.117 µm against 0.0727 and 0.119 µm); it gives dn/dT ≈ 1.3–1.8×10⁻⁵ /K from 0.4 to 1 µm, the e ray larger than the o ray
  const sa = source("Al2O3", "Malitson");
  for (const ax of ["o", "e"]) for (const lam of [0.4, 0.6, 1]) {
    const d = dndt(sa, ax, lam, 21.85) * 1e6;
    assert.ok(d > 12 && d < 19, `sapphire ${ax} ${lam} µm: ${d}`);
  }
  assert.ok(dndt(sa, "e", 0.633, 21.85) > dndt(sa, "o", 0.633, 21.85));
  // the o-ray dn/dT falls toward the infrared edge (Fig. 9), the e ray stays near its near-infrared value (Fig. 10)
  assert.ok(dndt(sa, "o", 4, 21.85) < 0.5 * dndt(sa, "o", 1, 21.85) && dndt(sa, "e", 4, 21.85) > 0.8 * dndt(sa, "e", 1, 21.85));
});

test("thermo-optic: rutile (Rams et al. 1997), MgF2 (Tropf 1995), TeO2 (Uchida 1971)", () => {
  const shift = (s, ax, lam, T) => thermoShift(s.thermo.form, s.axes[ax].thermo, s.thermo.t0_c, entryIndex(s.axes[ax], lam), lam, T);
  // rutile, Table I: index changes from 30 °C (about −0.01 over 110 °C), within the 1.3×10⁻³ the fit reaches
  // (the paper gives ±0.003 for its high-temperature indices)
  for (const label of ["Devore", "Bond"]) {
    const s = source("TiO2", label);
    for (const [lam, T, dno, dne] of [[0.457, 100, 2.77780 - 2.78380, 3.10696 - 3.11497], [0.457, 140, 2.77547 - 2.78380, 3.10390 - 3.11497],
      [0.6328, 120, 2.57573 - 2.58047, 2.85234 - 2.86105], [1.047, 140, 2.47170 - 2.47808, 2.72616 - 2.73476]]) {
      assert.ok(Math.abs(shift(s, "o", lam, T) - shift(s, "o", lam, 30) - dno) < 1.3e-3, `TiO2 ${label} no ${lam} ${T}`);
      assert.ok(Math.abs(shift(s, "e", lam, T) - shift(s, "e", lam, 30) - dne) < 1.3e-3, `TiO2 ${label} ne ${lam} ${T}`);
      assert.ok(shift(s, "o", lam, T) < shift(s, "o", lam, 30) && shift(s, "e", lam, T) < shift(s, "e", lam, 30)); // dn/dT < 0
    }
  }
  // MgF2: at 292.2 K the temperature-dependent strengths are Dodge's, so the model is the Dodge equation there
  // (Tropf prints λ2 = 0.09078162 µm for the e ray where Dodge's equation has 0.09076162: 2.5×10⁻⁵ at 0.2 µm)
  const m = source("MgF2", "Dodge");
  for (const ax of ["o", "e"]) for (const lam of [0.2, 0.6328, 3.39, 7]) {
    const t = m.axes[ax].thermo, n2 = [1, 2, 3].reduce((acc, i) => acc + t.g[i][0] / (t.lam[i - 1][0] ** -2 - lam ** -2), t.g[0][0]);
    assert.ok(Math.abs(Math.sqrt(n2) - entryIndex(m.axes[ax], lam)) < (ax === "o" ? 1e-8 : 3e-5), `MgF2 ${ax} ${lam}`);
  }
  for (const ax of ["o", "e"]) for (const lam of [0.4579, 0.6328, 1.15, 3.39]) { // the wavelengths of the dn/dT data
    const d = (shift(m, ax, lam, 30) - shift(m, ax, lam, 10)) / 20; // MgF2 has a small dn/dT, about 10⁻⁶ /K
    assert.ok(Math.abs(d) < 3e-6, `MgF2 ${ax} ${lam}: ${d}`);
  }
  // TeO2, Fig. 8: (1/n)(dn/dT)·n²/(n² − 1) on the lines −Δ·x + Ω/2, e.g. 23.8 (no) and 16.7 (ne) ×10⁻⁶ /°C at x = 1.2
  const te = source("TeO2", "Uchida");
  for (const [ax, lam1, y] of [["o", 0.196, 23.8e-6], ["e", 0.2039, 16.7e-6]]) {
    const lam = lam1 * Math.sqrt(1.2 / 0.2), n = entryIndex(te.axes[ax], lam);
    const dndt = shift(te, ax, lam, 26) - shift(te, ax, lam, 25);
    assert.ok(Math.abs(dndt / n * n * n / (n * n - 1) - y) < 0.1e-6, `TeO2 ${ax}`);
  }
});

test("ABF (NH4B4O6F), Shi et al. 2017: birefringence at 1.064 µm and the shortest type-I SHG wavelength", () => {
  const s = source("NH4B4O6F", "Shi-2017"), n = nAt(s);
  assert.ok(Math.abs(n(1.064)[2] - n(1.064)[0] - 0.1171) < 1e-4); // "Δn = 0.1171@1064 nm"
  // "the shortest phase-matching second harmonic wavelength is down to 158 nm in XY plane", shorter than KBBF's 162 nm
  const shortest = (plane) => { let lo = null; for (let l = 0.4; l >= 0.312; l -= 0.0002) if (solveAll(n, s.kind, "shg", l, 0).some((r) => r.plane === plane && r.type === "I")) lo = l; return lo / 2; };
  assert.ok(Math.abs(shortest("xy") - 0.158) < 0.001);
});

test("gaps filled from the collection: CaYAlO4 and GaS dn/dT, ZnO d", () => {
  const shift = (s, ax, lam, T) => thermoShift(s.thermo.form, s.axes[ax].thermo, s.thermo.t0_c, entryIndex(s.axes[ax], lam), lam, T);
  // CaYAlO4, Loiko et al. 2017, Table 3: dno/dT = −7.8, dne/dT = −8.7 ×10⁻⁶ /K at 1.03 µm
  const c = source("CaYAlO4", "Loiko");
  for (const [ax, v] of [["o", -7.8e-6], ["e", -8.7e-6]]) {
    assert.ok(Math.abs(shift(c, ax, 1.03, 21) - shift(c, ax, 1.03, 20) - v) < 0.06e-6, `CaYAlO4 ${ax}`);
  }
  // GaS, Errandonea et al. 1999, Table III: ∂ln n/∂T = 3.5 (o) and 10.1 (e) ×10⁻⁵ /K at 1.4 µm
  const g = source("GaS", "Kato");
  for (const [ax, v] of [["o", 3.5e-5], ["e", 10.1e-5]]) {
    const dndt = (shift(g, ax, 1.4, 30) - shift(g, ax, 1.4, 20)) / 10;
    assert.ok(Math.abs(dndt / entryIndex(g.axes[ax], 1.4) - v) < 0.01e-5, `GaS ${ax}`);
  }
  // ZnO, Wang et al. 2001: χ33 = −14.31 pm/V, χ31/χ33 = −0.095, d = χ/2
  assert.ok(Math.abs(D.ZnO.d["33"] * 2 + 14.31) < 0.01 && Math.abs(D.ZnO.d["31"] / D.ZnO.d["33"] + 0.095) < 0.001);
});
