// SPDC joint spectra against the numbers the papers give (plane-wave pump, collinear).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { entryIndex } from "../src/dispersion.client.js";
import { solveAll } from "../src/phasematch.client.js";
import { benninkF, focusing, jointSpectrum, purity, intensity, hom, transformLimitedNm } from "../src/spdc.client.js";

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

test("Bennink 2010: focused Gaussian modes", () => {
  const abs = ([a, b]) => Math.hypot(a, b);
  // the peak of |F(ξ, Φ)| is 2.06… at ξ = 2.84…, Φ = −(1.04…)π (Eqs. 27, 29, 30)
  let best = [0, 0, 0];
  for (let xi = 2; xi <= 4; xi += 0.02) for (let ph = -1.3; ph <= -0.8; ph += 0.005) {
    const v = abs(benninkF(xi, ph * Math.PI)); if (v > best[0]) best = [v, xi, ph];
  }
  assert.ok(Math.abs(best[0] - 2.06) < 0.01 && Math.abs(best[1] - 2.84) < 0.03 && Math.abs(best[2] + 1.04) < 0.01, `${best}`);
  // weak focusing: F → 2√ξ sinc(Φ/2), whose |F|² has a FWHM in Φ of 0.886·2π (Fig. 3); it grows with ξ
  const width = (xi) => { const ph = Array.from({ length: 2001 }, (_, k) => -40 + k * 0.04), y = ph.map((p) => abs(benninkF(xi, p)) ** 2);
    const m = Math.max(...y), ins = ph.filter((p, k) => y[k] > m / 2); return (ins[ins.length - 1] - ins[0]) / (2 * Math.PI); };
  assert.ok(Math.abs(width(0.02) - 0.886) < 0.01);
  assert.ok(width(10) > 1.2 && width(10) < 2 && width(1) < width(10));
  // heralding ratio 0.75 for degenerate SPDC with ξs = ξi = ξp (Eq. 55)
  const f = focusing({ xi: 2.84, L_mm: 10, kp: 2, ks: 1, ki: 1 });
  assert.ok(Math.abs(f.etaS - 0.75) < 1e-12 && Math.abs(f.etaI - 0.75) < 1e-12);
  // Evans et al. 2010: the pump (776 nm) and signal (1552 nm) divergences of 13.1 and 18.4 mrad in their 20 mm
  // PPKTP give equal focal parameters ξp ≈ ξs, Bennink's optimum (w = λ/(π θ), ξ = L/(k w²), k = 2πn/λ)
  const s = source("KTiOPO4", "Kato"), n = nAtOf(s);
  const xiOf = (lam, theta, nIdx) => { const w = lam / (Math.PI * theta); return 20000 / (2 * Math.PI * nIdx / lam * w * w); };
  const xp = xiOf(0.776, 0.0131, n(0.776)[1]), xs = xiOf(1.552, 0.0184, n(1.552)[1]);
  assert.ok(Math.abs(xp / xs - 1) < 0.05 && xp > 2 && xp < 6, `ξp = ${xp}, ξs = ${xs}`);
  // with that focus the Schmidt number comes much closer to their predicted K = 1.06 than the plane-wave sinc
  // (1.24–1.27): 1.12 here; the remainder may come from their (unstated) Sellmeier equations and pump model
  const j = jointSpectrum({ nAt: n, plane: "xy", angle: 0, type: "IIb", lp: 0.776, l1: 1.552, l2: 1.552, L_mm: 20,
    pumpFwhmNm: transformLimitedNm(0.776, 1.3), periodUm: "auto", xi: xp, n: 100 });
  const K = purity(j).schmidt;
  assert.ok(K > 1.06 && K < 1.15, `K = ${K}`);
});

test("focused JSA: the QPM period sets Φ = −1.04π at the centre, and purity stays converged", () => {
  const s = source("KTiOPO4", "Kato"), lp = 0.776;
  const run = (xi, n) => jointSpectrum({ nAt: nAtOf(s), plane: "xy", angle: 0, type: "IIb", lp, l1: 2 * lp, l2: 2 * lp, L_mm: 20,
    pumpFwhmNm: transformLimitedNm(lp, 1.3), periodUm: "auto", xi, n });
  const a = purity(run(2.84, 100)).purity, b = purity(run(2.84, 140)).purity;
  assert.ok(Math.abs(a - b) < 5e-3 && a > 0.8 && a <= 1, `P = ${a}, ${b}`);
  // weak focusing approaches the plane-wave sinc result
  const pw = purity(run(0, 120)).purity, weak = purity(run(0.01, 120)).purity;
  assert.ok(Math.abs(pw - weak) < 0.01, `${pw} vs ${weak}`);
  // the HOM dip stays at the same delay with and without focusing (both referred to the entrance face)
  const taus = Array.from({ length: 25 }, (_, k) => k * 0.25), dip = (j) => { const c = hom(j, taus); return taus[c.indexOf(Math.min(...c))]; };
  assert.ok(Math.abs(dip(run(2.84, 120)) - dip(run(0, 120))) <= 0.5);
});
