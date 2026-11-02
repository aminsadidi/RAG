// The power tab's physics (src/power.client.js): the Boyd–Kleinman focusing function, the second-harmonic power and the
// damage margins, and the damage thresholds of props.json it reads.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { bkBestSigma, bkFocus, bkH, damageMargin, PEAK, pulseBandwidthNm, pulseSH, shg, thresholdAt } from "../src/power.client.js";

const near = (a, b, tol, what) => assert.ok(Math.abs(a - b) <= tol, `${what}: ${a} vs ${b}`);

// H as Boyd and Kleinman define it, by a plain double sum: the closed-form inner integral must give the same
function brute(s, B, xi, N = 600) {
  const h = 2 * xi / N, z = [];
  for (let i = 0; i <= N; i++) { const t = -xi + i * h, d = 1 + t * t; z.push([1 / d, -t / d]); }
  let re = 0;
  for (let i = 0; i <= N; i++) for (let j = 0; j <= N; j++) {
    const u = (i - j) * h, w = (i % N ? 1 : 0.5) * (j % N ? 1 : 0.5), a = z[i], b = [z[j][0], -z[j][1]];
    const p = [a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]];
    re += w * Math.exp(-B * B * u * u / xi) * (p[0] * Math.cos(s * u) - p[1] * Math.sin(s * u));
  }
  return re * h * h / (4 * xi);
}

test("Boyd–Kleinman: h_m = 1.068 at ξ = 2.84, σ = 0.57 without walk-off", () => {
  const f = bkFocus(0);
  near(f.h, 1.068, 0.001, "h_m"); near(f.xi, 2.84, 0.02, "ξ_m"); near(f.sigma, 0.57, 0.01, "σ_m");
});

test("the single-integral H equals the double integral, with and without walk-off", () => {
  for (const [s, B, xi] of [[0.57, 0, 2.84], [0.72, 1, 1.87], [0.3, 3, 0.5], [1.2, 0.5, 6]]) near(bkH(s, B, xi), brute(s, B, xi), 2e-3, `H(${s}, ${B}, ${xi})`);
});

test("weak focusing: h → ξ (the near-field, plane-wave limit)", () => {
  for (const xi of [0.01, 0.03]) near(bkBestSigma(0, xi).h, xi, xi * 0.01, `h(${xi})`);
});

test("walk-off lowers h_m and moves the best focus looser", () => {
  let prev = bkFocus(0);
  for (const B of [0.5, 1, 2, 4]) {
    const f = bkFocus(B);
    assert.ok(f.h < prev.h && f.xi < prev.xi, `B = ${B}`);
    prev = f;
  }
});

test("SHG power: the textbook formula, P₂ = 16π²d²Lh/(ε₀cλ³n₁n₂)·P₁²", () => {
  const inp = { lam_um: 1.064, n1: 2.156, n2: 2.234, deff_pm: 16, rho_mrad: 0, L_mm: 10, focus: { mode: "optimal" }, laser: { cw: true, P: 0.01 } };
  const r = shg(inp), lam = 1.064e-6, k = 16 * Math.PI ** 2 * (16e-12) ** 2 * 0.01 * r.h / (8.8541878128e-12 * 2.99792458e8 * lam ** 3 * 2.156 * 2.234);
  near(r.kappa / k, 1, 1e-9, "κ");
  near(r.P2, k * 1e-4, k * 1e-4 * 1e-3, "P₂ at 10 mW (no depletion)");
  // w₀ from ξ = L/(k₁w₀²)
  near(r.w0_um, Math.sqrt(0.01 / (r.xi * 2 * Math.PI * 2.156 / lam)) * 1e6, 1e-9, "w₀");
  // a given waist reproduces its ξ
  const g = shg({ ...inp, focus: { mode: "waist", w0_um: 40 } });
  near(g.w0_um, 40, 1e-9, "given waist");
});

test("depletion never lets the harmonic exceed the pump, and agrees with P² at low power", () => {
  const base = { lam_um: 1.064, n1: 1.65, n2: 1.67, deff_pm: 2, rho_mrad: 56, L_mm: 10, focus: { mode: "optimal" } };
  const hi = shg({ ...base, laser: { cw: true, P: 1e6 } });
  assert.ok(hi.P2 < 1e6 && hi.eta < 1 && hi.eta_und > 1);
  const lo = shg({ ...base, laser: { cw: true, P: 1e-3 } });
  near(lo.P2 / lo.P2_und, 1, 1e-6, "low power");
});

test("pulses: the energy of κP(t)² over a Gaussian pulse is κ·P_peak·E/√2; sech² gives 2/3", () => {
  const k = 1e-6, E = 1e-3, tau = 1e-8;
  near(pulseSH(k, E, tau, "gauss").und / (k * PEAK.gauss * E / tau * E), 1 / Math.SQRT2, 1e-4, "Gaussian");
  near(pulseSH(k, E, tau, "sech2").und / (k * PEAK.sech2 * E / tau * E), 2 / 3, 1e-4, "sech²");
  near(PEAK.gauss, 0.9394, 1e-4, "Gaussian peak factor");
  // transform limit of a 100 fs Gaussian pulse at 800 nm: 9.4 nm
  near(pulseBandwidthNm(0.8, 100e-15, "gauss"), 9.42, 0.02, "Δλ");
});

test("damage threshold: F = I·τ, F ∝ √τ between 10 ps and long pulses, nothing below 10 ps", () => {
  const d = { value: 5, unit: "GW/cm2", tau_ns: 10 };
  const same = thresholdAt(d, 15e-9);
  assert.equal(same.how, "same"); near(same.I, 5e9, 1, "I"); near(same.F, 50, 1e-9, "F");
  const s = thresholdAt(d, 40e-9);
  assert.equal(s.how, "scaled"); near(s.F, 100, 1e-9, "F at 4τ"); near(s.I, 2.5e9, 1, "I at 4τ");
  assert.equal(thresholdAt(d, 1e-12).how, "short");
  assert.equal(thresholdAt(d, null).how, "cw");
  const nr = thresholdAt({ value: 2, unit: "J/cm2" }, 1e-8);
  assert.equal(nr.how, "noref"); assert.equal(nr.F, 2); assert.equal(nr.I, null);
});

test("damage margin: a Gaussian beam's peak is twice its mean, and the limits keep the margin", () => {
  const laser = { E: 1e-3, tau: 10e-9, rep: 1e3, shape: "gauss" }, d = { value: 5, unit: "GW/cm2", tau_ns: 10 };
  const m = damageMargin(laser, 100, d, 2);
  near(m.F, 2 * 1e-3 / (Math.PI * 0.01 ** 2), 1e-9, "peak fluence");
  near(m.ratio, m.F / 50, 1e-12, "the fluence decides (a Gaussian pulse's peak intensity is 0.94·F/τ)");
  assert.equal(m.verdict, "ok");
  near(damageMargin({ ...laser, E: m.Emax }, 100, d, 2).ratio * 2, 1, 1e-9, "Emax");
  near(damageMargin(laser, m.wmin_um, d, 2).ratio * 2, 1, 1e-9, "wmin");
  assert.equal(damageMargin({ ...laser, E: 0.1 }, 100, d, 2).verdict, "over");
  const top = damageMargin(laser, 100, d, 2, true);
  near(top.F * 2, m.F, 1e-9, "top-hat");
});

test("every damage threshold of props.json restates its own first number, in its unit", () => {
  const props = JSON.parse(readFileSync(new URL("../public/ri/props.json", import.meta.url)));
  let n = 0;
  for (const [mat, p] of Object.entries(props)) {
    const d = p.damage; if (!d) continue;
    assert.ok(d.value > 0 && ["GW/cm2", "J/cm2"].includes(d.unit), mat);
    // the first number of the sentence, in GW/cm² (MW/cm² ÷ 1000) or J/cm²
    const m = /([0-9.]+)\s*(?:[–-]\s*[0-9.]+\s*)?(?:±\s*[0-9.]+\s*)?(GW|MW|J)\/cm²/.exec(d.threshold);
    assert.ok(m, `${mat}: ${d.threshold}`);
    const v = +m[1] / (m[2] === "MW" ? 1000 : 1);
    near(d.value, v, 1e-12, `${mat}: ${d.threshold}`);
    assert.equal(d.unit, m[2] === "J" ? "J/cm2" : "GW/cm2", mat);
    if (d.tau_ns && d.pulse) assert.ok(/\d\s*(ns|ps|fs)/.test(d.pulse), `${mat}: a pulse length is read from "${d.pulse}"`);
    n++;
  }
  assert.ok(n >= 50);
});
