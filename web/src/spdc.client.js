// Spontaneous parametric down-conversion: the joint spectral amplitude (JSA) of a collinear pair,
// f(ν1, ν2) = α(ν1 + ν2)·φ(ν1, ν2), with a Gaussian pump spectrum α and the phase-matching function φ of a
// crystal of length L (Grice & Walmsley 1997; Mosley et al. 2008). From it: the joint spectral intensity,
// the heralded-photon purity P = Tr ρ² = Σ λn² (the Schmidt decomposition, Law, Walmsley & Eberly 2000),
// the Schmidt number K = 1/P, the marginal spectra, and the Hong–Ou–Mandel dip of the two photons.
// Plane-wave pump, no focusing. Frequencies ν in THz (1/ps), wavelengths in µm, Δk in µm⁻¹.
import { TYPES, direction, eigenIndices } from "./phasematch.client.js";

export const C_UM_PS = 299.792458; // c in µm/ps, so ν = c/λ is in THz
const LN2 = Math.log(2);

// A grid of n points centred on c with spacing step.
const grid = (c, step, n) => Array.from({ length: n }, (_, i) => c + (i - (n - 1) / 2) * step);

// opts: nAt (λ → principal indices), plane, angle (rad), type ("I", "IIa", "IIb": the pump on the fast wave, as
// in the phase-matching tab; wave 1 takes the first polarization of the type) or pols ([pump, wave 1, wave 2],
// each "s" or "f", e.g. ["s", "s", "s"] for type 0 along a principal axis), lp, l1, l2 (centre wavelengths, µm; 1/lp = 1/l1 + 1/l2), L_mm, pumpFwhmNm
// (FWHM of the pump intensity spectrum), periodUm (QPM grating period; "auto" phase-matches the centre),
// pm ("sinc", or "gauss": exp(−γ(ΔkL/2)²) with γ = 0.193, the sinc's Gaussian of equal FWHM), filterNm
// ([FWHM1, FWHM2] of Gaussian intensity filters, or null), n (grid points per axis), spanNm ([span1, span2]
// of the grid, or null for an automatic span covering the pump and phase-matching widths).
export function jointSpectrum(opts) {
  const { nAt, plane, angle, type, lp, l1, l2, L_mm, pumpFwhmNm, pm = "sinc", filterNm = null, n = 160 } = opts;
  const pols = opts.pols || ["f", ...TYPES[type]], dir = direction(plane, angle);
  const k = (lam, pol) => { const [s, f] = eigenIndices(nAt(lam), dir); return 2 * Math.PI * (pol === "s" ? s : f) / lam; };
  const L = L_mm * 1000, nu1c = C_UM_PS / l1, nu2c = C_UM_PS / l2, nupc = C_UM_PS / lp;
  const dk = (nu1, nu2) => k(C_UM_PS / (nu1 + nu2), pols[0]) - k(C_UM_PS / nu1, pols[1]) - k(C_UM_PS / nu2, pols[2]);
  const dk0 = dk(nu1c, nu2c);
  const kg = opts.periodUm === "auto" ? dk0 : opts.periodUm ? 2 * Math.PI / opts.periodUm : 0;
  const mismatch = (nu1, nu2) => dk(nu1, nu2) - kg;
  // pump: intensity FWHM in ν from the FWHM in λ
  const dnup = C_UM_PS * pumpFwhmNm * 1e-3 / (lp * lp);
  // automatic span: the pump band |δ1 + δ2| < Δνp and the phase-matching band |aδ1 + bδ2| < W (two sinc lobes,
  // W = 4π/L; a, b = ∂Δk/∂ν) cross in a parallelogram whose projections on the axes are
  // (|b|Δνp + W)/|a − b| and (|a|Δνp + W)/|a − b|; the grid spans 3 times those on each side, capped at 60 THz. Without filters the sinc tails make P converge
  // slowly with the window (it falls a few per cent as the window widens): the window acts as a detection bandwidth.
  let span = opts.spanNm ? opts.spanNm.map((s, i) => C_UM_PS * s * 1e-3 / [l1, l2][i] ** 2) : null;
  if (!span) {
    const h = 1e-3, a = (mismatch(nu1c + h, nu2c) - mismatch(nu1c - h, nu2c)) / (2 * h);
    const b = (mismatch(nu1c, nu2c + h) - mismatch(nu1c, nu2c - h)) / (2 * h);
    const W = 4 * Math.PI / L, d = Math.max(Math.abs(a - b), 1e-12);
    span = [(Math.abs(b) * dnup + W) / d, (Math.abs(a) * dnup + W) / d].map((e) => Math.min(60, 6 * e));
    if (Math.abs(l1 - l2) < 1e-9) span = [Math.max(...span), Math.max(...span)]; // degenerate: one grid for both
  }
  const nu1 = grid(nu1c, span[0] / (n - 1), n), nu2 = grid(nu2c, span[1] / (n - 1), n);
  const fil = filterNm ? filterNm.map((f, i) => C_UM_PS * f * 1e-3 / [l1, l2][i] ** 2) : null;
  const re = new Float64Array(n * n), im = new Float64Array(n * n);
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    const s = nu1[i] + nu2[j] - nupc;
    let amp = Math.exp(-2 * LN2 * s * s / (dnup * dnup));
    if (fil) amp *= Math.exp(-2 * LN2 * ((nu1[i] - nu1c) ** 2 / fil[0] ** 2 + (nu2[j] - nu2c) ** 2 / fil[1] ** 2));
    const x = mismatch(nu1[i], nu2[j]) * L / 2;
    const phi = pm === "gauss" ? Math.exp(-0.193 * x * x) : Math.abs(x) < 1e-9 ? 1 : Math.sin(x) / x;
    re[i * n + j] = amp * phi * Math.cos(x);
    im[i * n + j] = amp * phi * Math.sin(x);
  }
  return { n, nu1, nu2, re, im, dk0, kg, periodUm: kg ? 2 * Math.PI / Math.abs(kg) : null };
}

// Purity of the heralded photon, P = Tr(ρ1²) with ρ1 = F F† / Tr(F F†) (no diagonalization needed), and the
// Schmidt number K = 1/P.
export function purity({ n, re, im }) {
  let tr = 0, tr2 = 0;
  for (let k = 0; k < n * n; k++) tr += re[k] * re[k] + im[k] * im[k];
  for (let a = 0; a < n; a++) for (let b = a; b < n; b++) {
    let sr = 0, si = 0; // M_ab = Σ_j F_aj conj(F_bj)
    for (let j = 0; j < n; j++) {
      const ar = re[a * n + j], ai = im[a * n + j], br = re[b * n + j], bi = im[b * n + j];
      sr += ar * br + ai * bi; si += ai * br - ar * bi;
    }
    tr2 += (a === b ? 1 : 2) * (sr * sr + si * si);
  }
  const P = tr2 / (tr * tr);
  return { purity: P, schmidt: 1 / P };
}

// Joint spectral intensity |f|² and the two marginal spectra.
export function intensity({ n, re, im }) {
  const jsi = new Float64Array(n * n), m1 = new Float64Array(n), m2 = new Float64Array(n);
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    const v = re[i * n + j] ** 2 + im[i * n + j] ** 2;
    jsi[i * n + j] = v; m1[i] += v; m2[j] += v;
  }
  return { jsi, m1, m2 };
}

// FWHM (in the units of x) of a sampled peak, by linear interpolation of the half-maximum crossings.
export function fwhm(x, y) {
  let k = 0;
  for (let i = 1; i < y.length; i++) if (y[i] > y[k]) k = i;
  const h = y[k] / 2, cross = (i, j) => x[i] + (h - y[i]) * (x[j] - x[i]) / (y[j] - y[i]);
  let a = k, b = k;
  while (a > 0 && y[a] > h) a--;
  while (b < y.length - 1 && y[b] > h) b++;
  return Math.abs(cross(b - 1, b) - cross(a, a + 1));
}

// Hong–Ou–Mandel coincidence probability of the two photons of a pair at delay τ (ps), for a degenerate
// pair on one common grid: C(τ) = ½[1 − Re Σ f(ν1,ν2) f*(ν2,ν1) e^{−2πi(ν1−ν2)τ} / Σ|f|²]. The dip visibility
// is C(∞) − C(0) over C(∞), i.e. Re Σ f f*swap / Σ|f|² at the dip.
export function hom({ n, nu1, nu2, re, im }, taus) {
  const step1 = nu1[1] - nu1[0];
  if (Math.abs(step1 - (nu2[1] - nu2[0])) > 1e-9 * step1 || Math.abs(nu1[0] - nu2[0]) > 1e-6 * step1) return null;
  let norm = 0;
  for (let k = 0; k < n * n; k++) norm += re[k] ** 2 + im[k] ** 2;
  return taus.map((tau) => {
    let s = 0;
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      const ar = re[i * n + j], ai = im[i * n + j], br = re[j * n + i], bi = -im[j * n + i]; // f(ν1,ν2)·conj(f(ν2,ν1))
      const ph = -2 * Math.PI * (nu1[i] - nu2[j]) * tau, c = Math.cos(ph), sn = Math.sin(ph);
      const pr = ar * br - ai * bi, pi = ar * bi + ai * br;
      s += pr * c - pi * sn;
    }
    return 0.5 * (1 - s / norm);
  });
}

// The transform-limited intensity FWHM (nm) of a Gaussian pulse of duration tauPs (intensity FWHM) at λ (µm).
export function transformLimitedNm(lam, tauPs) {
  return 2 * LN2 / Math.PI / tauPs * lam * lam / C_UM_PS * 1000;
}
