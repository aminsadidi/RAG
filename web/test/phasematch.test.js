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
  // RBBF (32), Chen et al. 2009: d_ooe = d11 cos θ cos3φ; Li2B4O7 (4mm), Sugawara et al. 1998: d_ooe = d31 sin θ
  check("RbBe2BO3F2", "shg", 0.532, 0, "I", (t) => 0.45 * Math.cos(t), 0.06); // walk-off ≈ 3°
  check("Li2B4O7", "shg", 0.532, 0, "I", (t) => 0.15 * Math.sin(t), 0.03);
  // CTA, Cheng et al. 1993: type-II SHG of 1.32 µm in the x-y plane, φ = 62.8° calculated, 64.5° measured
  assert.ok(Math.abs(angle("CsTiOAsO4", null, "shg", 1.32, 0, "xy", "IIa") - 63.5) < 2);
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

test("thermo-optic formulas of Katō et al.: AgGaS2 (1999), LiInS2 (2014), RTP (2009), GaSe (2013)", () => {
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
  // GaSe, Katō, Tanno, Umemura 2013, p. 3: type-1 SHG of 9.5862 µm at θint = 13.61° (20 °C), 13.51° (225 °C), 13.71° (−165 °C)
  const g = source("GaSe", "Kato");
  for (const [T, th] of [[20, 13.61], [225, 13.51], [-165, 13.71]]) {
    const v = solveAll(nAtTemp(g, T), g.kind, "shg", 9.5862, 0).find((r) => r.type === "I").angle;
    assert.ok(Math.abs(v - th) < 0.03, `GaSe ${T} °C: ${v} vs ${th}`);
  }
});
