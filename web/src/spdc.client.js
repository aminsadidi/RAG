// Spontaneous parametric down-conversion: the joint spectral amplitude (JSA) of a collinear pair,
// f(ν1, ν2) = α(ν1 + ν2)·φ(ν1, ν2), with a Gaussian pump spectrum α and the phase-matching function φ of a
// crystal of length L (Grice & Walmsley 1997; Mosley et al. 2008). From it: the joint spectral intensity,
// the heralded-photon purity P = Tr ρ² = Σ λn² (the Schmidt decomposition, Law, Walmsley & Eberly 2000),
// the Schmidt number K = 1/P, the marginal spectra, and the Hong–Ou–Mandel dip of the two photons.
// The pump is a plane wave (sinc phase matching), or the pump and the two collection modes are collinear Gaussian
// beams focused at the crystal centre with equal focal parameters ξ = L/(k w²) (Bennink 2010, Eqs. 11, 25, 27).
// Frequencies ν in THz (1/ps), wavelengths in µm, Δk in µm⁻¹.
import { TYPES, direction, eigenIndices, walkOff } from "./phasematch.client.js";

export const C_UM_PS = 299.792458; // c in µm/ps, so ν = c/λ is in THz
const LN2 = Math.log(2);

// A grid of n points centred on c with spacing step.
const grid = (c, step, n) => Array.from({ length: n }, (_, i) => c + (i - (n - 1) / 2) * step);

// opts: nAt (λ → principal indices), plane, angle (rad), type ("I", "IIa", "IIb": the pump on the fast wave, as
// in the phase-matching tab; wave 1 takes the first polarization of the type) or pols ([pump, wave 1, wave 2],
// each "s" or "f", e.g. ["s", "s", "s"] for type 0 along a principal axis), lp, l1, l2 (centre wavelengths, µm; 1/lp = 1/l1 + 1/l2), L_mm, pumpFwhmNm
// (FWHM of the pump intensity spectrum), periodUm (QPM grating period; "auto" phase-matches the centre),
// pm ("sinc", "gauss": exp(−γ(ΔkL/2)²) with γ = 0.193, the sinc's Gaussian of equal FWHM, or "apod": a Gaussian-
// apodized grating of width apodSigma·L, see apodized), xi (focal parameter
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
    const phi = pm === "gauss" ? Math.exp(-0.193 * x * x) : pm === "apod" ? apodized(x, opts.apodSigma || 0.25)
      : Math.abs(x) < 1e-9 ? 1 : Math.sin(x) / x;
    re[i * n + j] = amp * phi * Math.cos(x);
    im[i * n + j] = amp * phi * Math.sin(x);
  }
  return { n, nu1, nu2, re, im, dk0, kg, periodUm: kg ? 2 * Math.PI / Math.abs(kg) : null };
}

// Phase matching of an apodized grating (domain engineering: Brańczyk et al. 2011, Dixon et al. 2013): the
// nonlinearity follows g(z) = exp(−(z − L/2)²/(2σ²)) inside the crystal, so the phase-matching function is
// (1/L)∫₀ᴸ g(z) e^{iΔk z} dz = e^{iΔkL/2}·A(x), x = ΔkL/2, A(x) = ∫₋½^½ exp(−u²/(2s²)) cos(2xu) du with s = σ/L. A is
// real and tends to sinc(x) as s → ∞; its side lobes fall as s shrinks (purity rises), and so does A(0)² (the pair
// rate relative to the uniform grating of the same length). Simpson's rule on 48 intervals.
export function apodized(x, s, m = 48) {
  let a = 0;
  for (let k = 0; k <= m; k++) {
    const u = k / m - 0.5, w = k === 0 || k === m ? 1 : k % 2 ? 4 : 2;
    a += w * Math.exp(-u * u / (2 * s * s)) * Math.cos(2 * x * u);
  }
  return a / (3 * m);
}

// The pump bandwidth (intensity FWHM, nm) that maximizes the heralded purity of a configuration (opts as for
// jointSpectrum), by golden-section search on its logarithm between lo and hi; purity against the pump bandwidth
// has a single maximum where the pump and phase-matching ellipses meet at right angles (Mosley et al. 2008).
// Searched on a coarse grid (n = 70), the best point is evaluated again at opts.n.
export function bestPumpBandwidth(opts, [lo, hi] = [0.01, 60]) {
  const P = (bw, n = 70) => purity(jointSpectrum({ ...opts, pumpFwhmNm: bw, n })).purity;
  let a = Math.log(lo), b = Math.log(hi);
  const g = (Math.sqrt(5) - 1) / 2;
  let c = b - g * (b - a), d = a + g * (b - a), fc = P(Math.exp(c)), fd = P(Math.exp(d));
  for (let it = 0; it < 26; it++) {
    if (fc > fd) { b = d; d = c; fd = fc; c = b - g * (b - a); fc = P(Math.exp(c)); }
    else { a = c; c = d; fc = fd; d = a + g * (b - a); fd = P(Math.exp(d)); }
  }
  const bw = Math.exp((a + b) / 2);
  return { pumpFwhmNm: bw, purity: P(bw, opts.n || 120) };
}

// Non-collinear emission in the plane of the pump direction (plane, angle) for a fixed pump wavelength: for photon 1
// at wavelength l1 the internal angles θ1, θ2 (rad, on either side of the pump) with k1 sin θ1 = k2 sin θ2 and
// k1 cos θ1 + k2 cos θ2 = kp − kg (kg the grating vector along the pump), the indices taken along each photon's own
// direction (so the e photons of type I or II are exact in this plane). Returns null when no angle up to maxRad
// phase-matches (the pair is then not emitted at l1), else { theta1, theta2, ext1, ext2 } with the external angles
// for a crystal face normal to the pump (sin θext = n sin θ).
export function emissionAngles({ nAt, plane, angle, pols, lp, l1, kg = 0, maxRad = 0.35 }) {
  const l2 = 1 / (1 / lp - 1 / l1);
  if (!(l2 > 0)) return null;
  const n = (lam, pol, a) => { const [s, f] = eigenIndices(nAt(lam), direction(plane, a)); return pol === "s" ? s : f; };
  const kp = 2 * Math.PI * n(lp, pols[0], angle) / lp - kg;
  const solve = (t1) => { // photon 1 at angle + t1, photon 2 on the other side at angle − t2
    const k1 = 2 * Math.PI * n(l1, pols[1], angle + t1) / l1;
    let t2 = 0, k2 = 0;
    for (let it = 0; it < 4; it++) { k2 = 2 * Math.PI * n(l2, pols[2], angle - t2) / l2; t2 = Math.asin(Math.min(1, k1 * Math.sin(t1) / k2)); }
    return { f: k1 * Math.cos(t1) + k2 * Math.cos(t2) - kp, t2, k1, k2 };
  };
  const steps = 700;
  let prev = solve(0);
  if (Math.abs(prev.f) < 1e-12) return out(0, prev);
  for (let s = 1; s <= steps; s++) {
    const t = maxRad * s / steps, cur = solve(t);
    if (prev.f * cur.f <= 0) { // bisection between the two samples
      let a = maxRad * (s - 1) / steps, b = t, fa = prev.f;
      for (let it = 0; it < 50; it++) { const m = (a + b) / 2, fm = solve(m).f; if (fa * fm <= 0) b = m; else { a = m; fa = fm; } }
      return out((a + b) / 2, solve((a + b) / 2));
    }
    prev = cur;
  }
  return null;
  function out(t1, r) {
    const n1 = r.k1 * l1 / (2 * Math.PI), n2 = r.k2 * l2 / (2 * Math.PI), ext = (nn, t) => Math.asin(Math.min(1, nn * Math.sin(t)));
    return { theta1: t1, theta2: r.t2, ext1: ext(n1, t1), ext2: ext(n2, r.t2) };
  }
}

// Absolute rate of photon pairs emitted into the collinear Gaussian collection modes (cw pump of power P), both
// photons in their modes (the rate before any loss; detected coincidences are this times the two arms'
// efficiencies). Low-gain parametric amplification of the vacuum, one photon per mode per second per hertz:
//   R = Γ0 ∫ dν |∫_{−L/2}^{L/2} O(z) e^{iΔk(ν)z} dz|²,  Γ0 = 8π² d_eff² P / (n_p n_1 n_2 ε0 c λ1 λ2),
// with O(z) = ∫ u_p u_1* u_2* dA the overlap of the three power-normalized Gaussian modes (waists wp, w1, w2 at the
// crystal centre, Gouy phase and wavefront curvature included; with plane waves of area A it is 1/√A and
// Γ0|O|² is Boyd's parametric gain Γ²), Δk(ν) = kp − k1(ν) − k2(νp − ν) − kg on the axis, ν the frequency of
// photon 1. Pairs of two photons with the same polarization (type 0 and I) are counted once (ν above νp/2).
// Spatial walk-off: each mode's envelope drifts sideways by ρ·z in the plane of the angle (ρ = walkOff, the centres
// meet at the crystal centre), which multiplies O(z) by exp(−S), S = Σ a_j c_j² − (Σ a_j c_j)²/Σ a_j, c_j = ρ_j z
// (Boyd & Kleinman 1968). walkoff: false leaves it out. Temporal walk-off (group-velocity mismatch) is already in
// Δk(ν). Against the measured rates: Evans et al. 2010 (20 mm type-II
// PPKTP, 776 → 1552 nm) infer 123000 pairs/s/mW, this gives 129000; Fedrizzi et al. 2007 (25 mm, 405 → 810 nm,
// 27 µm waists) detect 82000/s/mW with 40 % detectors (≥ 5.1·10⁵ in the modes), this gives 5.8·10⁵. Bennink's
// closed formula (2010, Eq. 40) is higher by n_p n_1 n_2 (≈ 6 in KTP): its fields lack the 1/√n of the flux
// normalization in a medium.
// opts: nAt, plane, angle, pols (["s"|"f"] × 3), lp, l1 (µm), L_mm, dEff (pm/V, the QPM factor 2/π included),
// wp, w1, w2 (µm, 1/e² intensity radii = 1/e field radii), powerMw, kg (µm⁻¹; "auto" phase-matches the centre
// wavelengths on axis), nz, nnu. Returns { rate (pairs/s), perMw, fwhmNm (spectrum of photon 1), peakPerNm (pairs/s
// per nm of photon 1 at the peak), lam (nm), spectrum }.
export function pairRate(opts) {
  const { nAt, plane, angle, pols, lp, l1, L_mm, dEff, wp, w1, w2, powerMw = 1, nz = 481, nnu = 2001, walkoff = true } = opts;
  const l2 = 1 / (1 / lp - 1 / l1), L = L_mm * 1000, dir = direction(plane, angle);
  const n = (lam, pol) => { const [s, f] = eigenIndices(nAt(lam), dir); return pol === "s" ? s : f; };
  const k = (lam, pol) => 2 * Math.PI * n(lam, pol) / lam;
  const kp = k(lp, pols[0]);
  const rho = walkoff ? [[lp, pols[0]], [l1, pols[1]], [l2, pols[2]]].map(([lam, pol]) => walkOff(nAt, plane, angle, lam, pol)) : [0, 0, 0];
  const kg = opts.kg === "auto" || opts.kg === undefined ? kp - k(l1, pols[1]) - k(l2, pols[2]) : opts.kg;
  const nup = C_UM_PS / lp, nu1c = C_UM_PS / l1; // THz
  const dk = (nu) => kp - k(C_UM_PS / nu, pols[1]) - k(C_UM_PS / (nup - nu), pols[2]) - kg; // µm⁻¹
  // the overlap O(z) on Simpson nodes (µm⁻¹)
  const zr = [kp * wp * wp / 2, k(l1, pols[1]) * w1 * w1 / 2, k(l2, pols[2]) * w2 * w2 / 2];
  const zs = [], Ore = [], Oim = [], wz = [], norm = (2 / Math.PI) ** 1.5 / (wp * w1 * w2) * Math.PI;
  const m = nz % 2 ? nz - 1 : nz;
  for (let q = 0; q <= m; q++) {
    const z = -L / 2 + L * q / m;
    // 1/((1 + iζp)(1 − iζ1)(1 − iζ2)) · 1/a, a = 1/(wp²(1+iζp)) + 1/(w1²(1−iζ1)) + 1/(w2²(1−iζ2))
    const cp = [1, z / zr[0]], c1 = [1, -z / zr[1]], c2 = [1, -z / zr[2]];
    const mul = (a, b) => [a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]], inv = (a) => { const d = a[0] * a[0] + a[1] * a[1]; return [a[0] / d, -a[1] / d]; };
    const ip = inv(cp), i1 = inv(c1), i2 = inv(c2);
    const a = [ip[0] / (wp * wp) + i1[0] / (w1 * w1) + i2[0] / (w2 * w2), ip[1] / (wp * wp) + i1[1] / (w1 * w1) + i2[1] / (w2 * w2)];
    let o = mul(mul(mul(ip, i1), i2), inv(a));
    if (rho.some((r) => r)) {
      const aj = [[ip[0] / (wp * wp), ip[1] / (wp * wp)], [i1[0] / (w1 * w1), i1[1] / (w1 * w1)], [i2[0] / (w2 * w2), i2[1] / (w2 * w2)]];
      let s2 = [0, 0], s1 = [0, 0];
      aj.forEach((x, j) => { const c = rho[j] * z; s2 = [s2[0] + x[0] * c * c, s2[1] + x[1] * c * c]; s1 = [s1[0] + x[0] * c, s1[1] + x[1] * c]; });
      const t = mul(mul(s1, s1), inv(a)), S = [s2[0] - t[0], s2[1] - t[1]], e = Math.exp(-S[0]);
      o = mul(o, [e * Math.cos(S[1]), -e * Math.sin(S[1])]);
    }
    zs.push(z); Ore.push(norm * o[0]); Oim.push(norm * o[1]); wz.push((q === 0 || q === m ? 1 : q % 2 ? 4 : 2) * L / m / 3);
  }
  const amp2 = (nu) => { // |∫ O e^{iΔk z} dz|², dimensionless
    const d = dk(nu); let re = 0, im = 0;
    for (let q = 0; q < zs.length; q++) {
      const c = Math.cos(d * zs[q]), s = Math.sin(d * zs[q]);
      re += wz[q] * (Ore[q] * c - Oim[q] * s); im += wz[q] * (Ore[q] * s + Oim[q] * c);
    }
    return re * re + im * im;
  };
  // the frequency range: out from the centre until |Δk|·L passes 2π·60 (60 lobes of the sinc each side; their
  // tails hold under 1 % of the rate) or the photon reaches 1.6·λ1 on the long side and 0.6·λ1 on the short side
  const reach = (sgn) => {
    let step = 1e-4, off = 0;
    while (off < 0.4 * nu1c) { off = Math.min(0.4 * nu1c, off + step); if (Math.abs(dk(nu1c + sgn * off)) * L > 2 * Math.PI * 60) break; step *= 1.3; }
    return off;
  };
  let lo = nu1c - reach(-1), hi = nu1c + reach(1);
  const same = pols[1] === pols[2];
  // each pair once: photon 1 stays on its own side of the degenerate frequency νp/2
  if (same) { if (nu1c >= nup / 2) lo = Math.max(lo, nup / 2); else hi = Math.min(hi, nup / 2); }
  if (!(hi > lo)) return null;
  const nn = nnu % 2 ? nnu : nnu + 1, h = (hi - lo) / (nn - 1), spec = new Float64Array(nn);
  let integ = 0;
  for (let q = 0; q < nn; q++) { spec[q] = amp2(lo + q * h); integ += (q === 0 || q === nn - 1 ? 1 : q % 2 ? 4 : 2) * spec[q]; }
  integ *= h / 3 * 1e12; // THz → Hz
  const eps0 = 8.8541878128e-12, c = 299792458;
  const G0 = 8 * Math.PI ** 2 * (dEff * 1e-12) ** 2 * (powerMw * 1e-3)
    / (n(lp, pols[0]) * n(l1, pols[1]) * n(l2, pols[2]) * eps0 * c * l1 * 1e-6 * l2 * 1e-6);
  const rate = G0 * integ;
  // spectrum of photon 1 against wavelength: pairs/s per nm
  const lam = Array.from(spec, (_, q) => C_UM_PS / (lo + q * h) * 1000);
  let pk = 0; for (let q = 1; q < nn; q++) if (spec[q] > spec[pk]) pk = q;
  const perNm = (q) => G0 * spec[q] * 1e12 * (lo + q * h) ** 2 / (C_UM_PS * 1000); // dν/dλ = ν²/c, c in nm·THz
  // FWHM of the photon's spectrum, between the outermost half-maximum crossings (a spectrum with two humps
  // counts as one band). Same-polarization pairs whose range stops at νp/2 hold only half of a spectrum that is
  // symmetric about νp/2 (either photon can be the one above it): the band is mirrored there. NaN when the band
  // reaches the edge of the computed range.
  const half = spec[pk] / 2;
  let ia = 0, ib = nn - 1;
  while (ia < nn - 1 && spec[ia] < half) ia++;
  while (ib > 0 && spec[ib] < half) ib--;
  const cross = (i, j) => lo + h * (i + (half - spec[i]) / (spec[j] - spec[i]) * (j - i)); // THz, between nodes i and j
  const cutLo = same && Math.abs(lo - nup / 2) < 1e-9 * nup, cutHi = same && Math.abs(hi - nup / 2) < 1e-9 * nup;
  let nuA = ia > 0 ? cross(ia - 1, ia) : cutLo ? null : NaN, nuB = ib < nn - 1 ? cross(ib + 1, ib) : cutHi ? null : NaN;
  if (nuA === null) nuA = nup - nuB; // mirror of the far edge
  if (nuB === null) nuB = nup - nuA;
  const fwhmNm = Math.abs(C_UM_PS / nuA - C_UM_PS / nuB) * 1000;
  return { rate, perMw: rate / powerMw, fwhmNm, peakPerNm: perNm(pk), lam, spectrum: spec, l2, walkoffMrad: rho.map((r) => r * 1e3) };
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

// What two single-photon detectors count from a CW pair source, for planning an experiment. R: pairs/s with both
// photons in the collection modes (pairRate); mu12 = μ₂|₁ and mu21 = μ₁|₂: the conditional couplings of
// fiberCoupling (a photon 1 in its mode has its twin in mode 2 with probability μ₂|₁), so R/μ₂|₁ photons 1 reach mode 1.
// Each arm then has a transmission T (optics, filter, fibre) and a detector efficiency eta, and dark counts (/s);
// tauNs is the coincidence window. Returns singles S1, S2, true coincidences C, accidentals A = S1·S2·τ (uncorrelated
// counts falling in the window), CAR = C/A, the heralding (Klyshko) efficiencies h1 = C/(S2 − D2) (the chance that
// photon 1 is detected when photon 2 was) and h2 = C/(S1 − D1), and the mean number of pairs per window R·τ.
export function detectedCounts({ R, mu12, mu21, T1 = 1, T2 = 1, eta1 = 1, eta2 = 1, dark1 = 0, dark2 = 0, tauNs = 1 }) {
  const tau = tauNs * 1e-9, e1 = T1 * eta1, e2 = T2 * eta2;
  const S1 = (R / mu12) * e1 + dark1, S2 = (R / mu21) * e2 + dark2;
  const C = R * e1 * e2, A = S1 * S2 * tau;
  return { S1, S2, C, A, CAR: C / A, h1: C / (S2 - dark2), h2: C / (S1 - dark1), pairsPerWindow: R * tau };
}

// The pump powers (same unit as P) at which CAR = target, for counts that scale as above (C, signal singles ∝ P, dark
// counts fixed), and the power of the highest CAR, P* = √(D1·D2/(b1·b2)) (b: singles per unit power). Below P* dark
// counts limit the CAR, above it accidental pairs do. Returns { best: {P, CAR}, low, high } (null where unreachable).
export function powerForCar(opts, P, target) {
  const one = detectedCounts({ ...opts, R: opts.R / P }); // per unit power
  const a = one.C, b1 = one.S1 - (opts.dark1 || 0), b2 = one.S2 - (opts.dark2 || 0), D1 = opts.dark1 || 0, D2 = opts.dark2 || 0;
  const tau = (opts.tauNs ?? 1) * 1e-9;
  const car = (p) => (a * p) / ((b1 * p + D1) * (b2 * p + D2) * tau);
  const pBest = D1 > 0 && D2 > 0 ? Math.sqrt((D1 * D2) / (b1 * b2)) : 0;
  // target·τ·b1b2 P² + (target·τ(b1D2 + b2D1) − a) P + target·τ·D1D2 = 0
  const qa = target * tau * b1 * b2, qb = target * tau * (b1 * D2 + b2 * D1) - a, qc = target * tau * D1 * D2;
  const disc = qb * qb - 4 * qa * qc;
  const roots = disc < 0 ? [] : [(-qb - Math.sqrt(disc)) / (2 * qa), (-qb + Math.sqrt(disc)) / (2 * qa)].filter((x) => x > 0);
  return { best: { P: pBest, CAR: pBest > 0 ? car(pBest) : Infinity }, low: roots.length === 2 ? roots[0] : null,
    high: roots.length ? roots[roots.length - 1] : null };
}
