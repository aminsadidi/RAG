// SPDC joint spectra against the numbers the papers give (plane-wave pump, collinear).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { entryIndex } from "../src/dispersion.client.js";
import { solveAll } from "../src/phasematch.client.js";
import { jointSpectrum, purity, intensity, hom, transformLimitedNm } from "../src/spdc.client.js";

const A = JSON.parse(readFileSync(new URL("../public/ri/aniso.json", import.meta.url)));
const source = (mat, label) => A.find((c) => c.material === mat).sources.find((s) => !label || s.label === label);
const nAtOf = (s) => (lam) => (s.kind === "uniaxial" ? ["o", "o", "e"] : ["x", "y", "z"]).map((a) => entryIndex(s.axes[a], lam));
// Type-II degenerate pair of a birefringently phase-matched crystal
const birefringent = (mat, lp, L_mm, pumpFwhmNm, extra = {}) => {
  const s = source(mat), nAt = nAtOf(s), sol = solveAll(nAt, s.kind, "opo", lp, 2 * lp).find((r) => r.type === "IIa");
  return jointSpectrum({ nAt, plane: sol.plane, angle: sol.angle * Math.PI / 180, type: "IIa", lp, l1: 2 * lp, l2: 2 * lp, L_mm, pumpFwhmNm, n: 140, ...extra });
};

test("Mosley et al. 2008, Fig. 1: purity of the heralded photon against the filter bandwidth", () => {
  // 2 mm BBO pumped at 400 nm and 5 mm KDP at 415 nm, plane-wave pump of 4 nm FWHM; purity read from Fig. 1(c), (d)
  for (const [f, ref] of [[5, 0.93], [10, 0.75], [25, 0.44]]) {
    const P = purity(birefringent("BaB2O4", 0.4, 2, 4, { filterNm: [f, f] })).purity;
    assert.ok(Math.abs(P - ref) < 0.05, `BBO, ${f} nm filters: P = ${P} vs ${ref}`);
  }
  const P = purity(birefringent("KH2PO4", 0.415, 5, 4, { filterNm: [25, 25] })).purity;
  assert.ok(Math.abs(P - 0.97) < 0.02, `KDP, 25 nm filters: P = ${P}`);
  // KDP: the e photon (wave 2, group-velocity matched to the pump) is narrow, the o photon broad (Fig. 1b)
  const j = birefringent("KH2PO4", 0.415, 5, 4), { m1, m2 } = intensity(j);
  const width = (m) => m.filter((v) => v > Math.max(...m) / 2).length;
  assert.ok(width(m1) > 3 * width(m2));
});

test("Evans et al. 2010: 20 mm type-II PPKTP, 776 → 1552 nm, 1.3 ps transform-limited pump, K = 1.06", () => {
  const s = source("KTiOPO4", "Kato"), lp = 0.776;
  const run = (pm) => jointSpectrum({ nAt: nAtOf(s), plane: "xy", angle: 0, type: "IIb", lp, l1: 2 * lp, l2: 2 * lp, L_mm: 20,
    pumpFwhmNm: transformLimitedNm(lp, 1.3), periodUm: "auto", pm, n: 140 });
  const g = run("gauss"), K = purity(g).schmidt;
  // the paper's K = 1.06 lies between the Gaussian approximation of the phase-matching function and the full sinc
  assert.ok(K > 1 && K < 1.06, `K (Gaussian) = ${K}`);
  const Ks = purity(run("sinc")).schmidt;
  assert.ok(Ks > 1.06 && Ks < 1.35, `K (sinc) = ${Ks}`);
  assert.ok(Math.abs(g.periodUm - 45.0) < 1.5, `grating period ${g.periodUm} µm`);
  // HOM of the two photons: C = ½ away from the dip (τ within the grid's period 1/δν ≈ 45 ps), and the dip
  // sits at half the group delay between the y and z photons, L(1/vg,z − 1/vg,y)/2 ≈ 2.5 ps
  const c = hom(g, [15, ...Array.from({ length: 13 }, (_, k) => k * 0.5)]);
  assert.ok(Math.abs(c[0] - 0.5) < 1e-3);
  const k = c.slice(1).indexOf(Math.min(...c.slice(1)));
  assert.ok(c[k + 1] < 0.3 && Math.abs(k * 0.5 - 2.5) <= 1, `dip ${c[k + 1]} at ${k * 0.5} ps`);
});

test("purity is 1 for a factorable amplitude and the grid is converged", () => {
  const a = purity(birefringent("BaB2O4", 0.4, 2, 4, { n: 100 })).purity, b = purity(birefringent("BaB2O4", 0.4, 2, 4, { n: 180 })).purity;
  assert.ok(Math.abs(a - b) < 1e-3);
  const n = 50, re = new Float64Array(n * n), im = new Float64Array(n * n);
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) re[i * n + j] = Math.exp(-(((i - 25) / 6) ** 2)) * Math.exp(-(((j - 20) / 9) ** 2));
  assert.ok(Math.abs(purity({ n, re, im }).purity - 1) < 1e-12);
});
