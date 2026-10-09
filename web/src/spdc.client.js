// Spontaneous parametric down-conversion: the joint spectral amplitude (JSA) of a collinear pair,
// f(ν1, ν2) = α(ν1 + ν2)·φ(ν1, ν2), with a Gaussian pump spectrum α and the phase-matching function φ of a
// crystal of length L (Grice & Walmsley 1997; Mosley et al. 2008). From it: the joint spectral intensity,
// the heralded-photon purity P = Tr ρ² = Σ λn² (the Schmidt decomposition, Law, Walmsley & Eberly 2000),
// the Schmidt number K = 1/P, the marginal spectra, and the Hong–Ou–Mandel dip of the two photons.
// The pump is a plane wave (sinc phase matching), or the pump and the two collection modes are collinear Gaussian
// beams focused at the crystal centre with equal focal parameters ξ = L/(k w²) (Bennink 2010, Eqs. 11, 25, 27).
// Frequencies ν in THz (1/ps), wavelengths in µm, Δk in µm⁻¹.
import { TYPES, direction, eigenIndices } from "./phasematch.client.js";

export const C_UM_PS = 299.792458; // c in µm/ps, so ν = c/λ is in THz
const LN2 = Math.log(2);

// A grid of n points centred on c with spacing step.
const grid = (c, step, n) => Array.from({ length: n }, (_, i) => c + (i - (n - 1) / 2) * step);

// opts: nAt (λ → principal indices), plane, angle (rad), type ("I", "IIa", "IIb": the pump on the fast wave, as
// in the phase-matching tab; wave 1 takes the first polarization of the type) or pols ([pump, wave 1, wave 2],
// each "s" or "f", e.g. ["s", "s", "s"] for type 0 along a principal axis), lp, l1, l2 (centre wavelengths, µm; 1/lp = 1/l1 + 1/l2), L_mm, pumpFwhmNm
// (FWHM of the pump intensity spectrum), periodUm (QPM grating period; "auto" phase-matches the centre),
// pm ("sinc", or "gauss": exp(−γ(ΔkL/2)²) with γ = 0.193, the sinc's Gaussian of equal FWHM), xi (focal parameter
// of Gaussian pump and collection modes, Bennink's F(ξ, Φ) instead of the sinc; Φ = ΔkL includes the Gouy shift,
// so "auto" QPM then sets Φ = −1.04π at the centre, the peak of |F| at ξ = 2.84), filterNm
// ([FWHM1, FWHM2] of Gaussian intensity filters, or null), n (grid points per axis), spanNm ([span1, span2]
// of the grid, or null for an automatic span covering the pump and phase-matching widths).
export function jointSpectrum(opts) {
  const { nAt, plane, angle, type, lp, l1, l2, L_mm, pumpFwhmNm, pm = "sinc", filterNm = null, n = 160 } = opts;
  const pols = opts.pols || ["f", ...TYPES[type]], dir = direction(plane, angle);
  const k = (lam, pol) => { const [s, f] = eigenIndices(nAt(lam), dir); return 2 * Math.PI * (pol === "s" ? s : f) / lam; };
  const L = L_mm * 1000, nu1c = C_UM_PS / l1, nu2c = C_UM_PS / l2, nupc = C_UM_PS / lp;
  const dk = (nu1, nu2) => k(C_UM_PS / (nu1 + nu2), pols[0]) - k(C_UM_PS / nu1, pols[1]) - k(C_UM_PS / nu2, pols[2]);
  const dk0 = dk(nu1c, nu2c);
  const xi = opts.xi || 0;
  const kg = opts.periodUm === "auto" ? dk0 + (xi ? 1.04 * Math.PI / L : 0) : opts.periodUm ? 2 * Math.PI / opts.periodUm : 0;
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
    if (xi) {
      // F is referred to the crystal centre; the factor e^{iΦ/2} refers it to the entrance face, as the sinc term below
      const [fr, fi] = benninkF(xi, 2 * x, 60), c = Math.cos(x), sn = Math.sin(x);
      re[i * n + j] = amp * (fr * c - fi * sn); im[i * n + j] = amp * (fr * sn + fi * c);
      continue;
    }
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

// Bennink's spatial overlap factor F(ξ, Φ) = ∫₋₁¹ √ξ e^{iΦl/2}/(1 − iξl) dl (Eq. 27, with C ≈ 0): the phase-matching
// function of focused collinear Gaussian modes; for ξ ≪ 1 it tends to 2√ξ sinc(Φ/2). Returns [re, im].
export function benninkF(xi, Phi, m = 200) {
  let re = 0, im = 0;
  for (let k = 0; k <= 2 * m; k++) { // Simpson's rule on [−1, 1]
    const l = k / m - 1, w = k === 0 || k === 2 * m ? 1 : k % 2 ? 4 : 2;
    const c = Math.cos(Phi * l / 2), s = Math.sin(Phi * l / 2), d = 1 + xi * xi * l * l;
    // e^{iΦl/2}(1 + iξl)/(1 + ξ²l²)
    re += w * (c - s * xi * l) / d; im += w * (s + c * xi * l) / d;
  }
  const h = Math.sqrt(xi) / (3 * m);
  return [re * h, im * h];
}

// Focusing of collinear Gaussian modes with ξp = ξs = ξi = ξ (Bennink 2010): waists w = √(L/(k ξ)) (µm, k in the
// medium), the pair collection probability relative to its limit, arctan(ξ)/(π/2) (Eq. 40 with A₊B₊ = 4), and the
// heralding ratios ηs = (ki/kp)(ks/kp + 1), ηi = (ks/kp)(ki/kp + 1) (Eq. 55).
export function focusing({ xi, L_mm, kp, ks, ki }) {
  const L = L_mm * 1000, w = (k) => Math.sqrt(L / (k * xi));
  return { wp: w(kp), ws: w(ks), wi: w(ki), brightness: Math.atan(xi) / (Math.PI / 2),
    etaS: ki / kp * (ks / kp + 1), etaI: ks / kp * (ki / kp + 1) };
}

// The transform-limited intensity FWHM (nm) of a Gaussian pulse of duration tauPs (intensity FWHM) at λ (µm).
export function transformLimitedNm(lam, tauPs) {
  return 2 * LN2 / Math.PI / tauPs * lam * lam / C_UM_PS * 1000;
}

// Coupling of a pair into single-mode fibres (Ljunggren & Tengner 2005): a monochromatic Gaussian pump of waist wp
// and collinear phase matching (Δk = 0 on axis), the fibre-matched modes Gaussian beams of waists ws, wi, all
// focused at the crystal centre. In the paraxial angular spectrum (transverse wavevectors q, µm⁻¹),
// Ψ(qs, qi) = exp(−wp²|qs + qi|²/4) sinc(ΔL/2), Δ = qs²/(2ks) + qi²/(2ki) − |qs + qi|²/(2kp) (k in the medium),
// G(q) = (w/√(2π)) exp(−w²q²/4). Returns the single couplings γs, γi (Eq. 19: the fraction of the photons, at
// these frequencies, found in the fibre mode), the pair coupling γc (Eq. 26) and the conditional coincidences
// μ_i|s = γc/γs, μ_s|i = γc/γi. ξ = L/zR with zR = k w²/2 (Ljunggren's focusing parameter), so w = √(2L/(kξ)).
// With azimuthal: false only the rotationally symmetric (l = 0) part of Ψ is kept, as Ljunggren & Tengner do by
// writing the amplitude in the polar angles alone (Sec. II A); that drops the l ≠ 0 Schmidt modes from the total
// and raises the couplings (their 98 %, 93 % against 82 %, 80 % with all modes, 10 mm PPKTP 532 → 810 + 1550 nm).
export function fiberCoupling(opts) {
  return opts.azimuthal === false ? fiberCouplingL0(opts) : fiberCouplingFull(opts);
}

function fiberCouplingL0({ kp, ks, ki, L_mm, xiP, xiS, xiI, n = 120, nphi = 64 }) {
  const L = L_mm * 1000, w = (k, xi) => Math.sqrt(2 * L / (k * xi));
  const wp = w(kp, xiP), ws = w(ks, xiS), wi = w(ki, xiI);
  const G = (wv, q) => wv / Math.sqrt(2 * Math.PI) * Math.exp(-wv * wv * q * q / 4);
  const qm = 4.5 * Math.max(2 / wp, 2 / Math.min(ws, wi), Math.sqrt(4 * Math.PI * Math.min(ks, ki) / L)), h = qm / n;
  const rad = (i) => (i + 0.5) * h, ring = (i) => 2 * Math.PI * rad(i) * h;
  let tot = 0, nS = 0, nI = 0, pair = 0;
  const As = new Float64Array(n), Ai = new Float64Array(n);
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    const a = rad(i), b = rad(j);
    let p0 = 0; // Ψ averaged over the angle between qs and qi
    for (let m = 0; m < nphi; m++) {
      const p2 = a * a + b * b + 2 * a * b * Math.cos((m + 0.5) * 2 * Math.PI / nphi);
      const x = (a * a / (2 * ks) + b * b / (2 * ki) - p2 / (2 * kp)) * L / 2;
      p0 += Math.exp(-wp * wp * p2 / 4) * (Math.abs(x) < 1e-9 ? 1 : Math.sin(x) / x);
    }
    p0 /= nphi;
    tot += p0 * p0 * ring(i) * ring(j); As[j] += G(ws, a) * p0 * ring(i); Ai[i] += G(wi, b) * p0 * ring(j);
  }
  for (let j = 0; j < n; j++) { nS += As[j] ** 2 * ring(j); pair += G(wi, rad(j)) * As[j] * ring(j); nI += Ai[j] ** 2 * ring(j); }
  const gs = nS / tot, gi = nI / tot, gc = pair * pair / tot;
  return { wp, ws, wi, gammaS: gs, gammaI: gi, gammaC: gc, muIgS: gc / gs, muSgI: gc / gi };
}

function fiberCouplingFull({ kp, ks, ki, L_mm, xiP, xiS, xiI, n = 64 }) {
  const L = L_mm * 1000, w = (k, xi) => Math.sqrt(2 * L / (k * xi));
  const wp = w(kp, xiP), ws = w(ks, xiS), wi = w(ki, xiI);
  const G = (wv, q2) => wv / Math.sqrt(2 * Math.PI) * Math.exp(-wv * wv * q2 / 4);
  const psi = (sx, sy, ix) => {
    const px = sx + ix, p2 = px * px + sy * sy, s2 = sx * sx + sy * sy, i2 = ix * ix;
    const x = (s2 / (2 * ks) + i2 / (2 * ki) - p2 / (2 * kp)) * L / 2;
    return Math.exp(-wp * wp * p2 / 4) * (Math.abs(x) < 1e-9 ? 1 : Math.sin(x) / x);
  };
  // extents: the narrowest of the pump, fibre and phase-matching widths in q
  const qm = 4.5 * Math.max(2 / wp, 2 / Math.min(ws, wi), Math.sqrt(4 * Math.PI * Math.min(ks, ki) / L));
  const h = 2 * qm / (n - 1), hr = qm / (n - 1);
  let tot = 0, numS = 0, pair = 0;
  const A = new Float64Array(n); // ∫ Gs(qs) Ψ(qs, qi) d²qs for qi = (r, 0)
  for (let r = 0; r < n; r++) {
    const ix = (r + 0.5) * hr, wr = 2 * Math.PI * ix * hr; // midpoint ring (∫ d²qi over a ring)
    let a = 0, t = 0;
    for (let u = 0; u < n; u++) for (let v = 0; v < n; v++) {
      const sx = -qm + u * h, sy = -qm + v * h, p = psi(sx, sy, ix);
      a += G(ws, sx * sx + sy * sy) * p; t += p * p;
    }
    A[r] = a * h * h; tot += t * h * h * wr; numS += A[r] * A[r] * wr; pair += G(wi, ix * ix) * A[r] * wr;
  }
  // γi by symmetry: the same with the roles of s and i exchanged
  let numI = 0;
  for (let r = 0; r < n; r++) {
    const sx0 = (r + 0.5) * hr, wr = 2 * Math.PI * sx0 * hr;
    let a = 0;
    for (let u = 0; u < n; u++) for (let v = 0; v < n; v++) {
      const ix = -qm + u * h, iy = -qm + v * h;
      // Ψ is symmetric under a joint rotation, so Ψ(qs = (sx0, 0), qi) = Ψ evaluated with roles of the vectors
      const px = sx0 + ix, p2 = px * px + iy * iy, i2 = ix * ix + iy * iy, s2 = sx0 * sx0;
      const x = (s2 / (2 * ks) + i2 / (2 * ki) - p2 / (2 * kp)) * L / 2;
      a += G(wi, i2) * Math.exp(-wp * wp * p2 / 4) * (Math.abs(x) < 1e-9 ? 1 : Math.sin(x) / x);
    }
    a *= h * h; numI += a * a * wr;
  }
  const gs = numS / tot, gi = numI / tot, gc = pair * pair / tot;
  return { wp, ws, wi, gammaS: gs, gammaI: gi, gammaC: gc, muIgS: gc / gs, muSgI: gc / gi };
}
