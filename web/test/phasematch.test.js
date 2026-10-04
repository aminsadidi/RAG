// The phase-matching engine against angles published for these crystals.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { entryIndex } from "../src/dispersion.client.js";
import { eigenIndices, effectiveD, fieldVectors, solveAll } from "../src/phasematch.client.js";

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
