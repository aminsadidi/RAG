// Second-harmonic output power with focused Gaussian beams (Boyd & Kleinman, J. Appl. Phys. 39, 3597 (1968)), and the
// margin of a laser beam to a crystal's damage threshold. SI units inside; µm, mm, pm/V, ns at the edges as named.
const C = 2.99792458e8, EPS0 = 8.8541878128e-12;

// ---------- the Boyd–Kleinman focusing function
// H(σ, B, ξ) = 1/(4ξ) ∫∫ exp[iσ(τ−τ') − (B²/ξ)(τ−τ')²] / ((1+iτ)(1−iτ')) dτ dτ' over [−ξ, ξ]², focus at the centre, no
// absorption. ξ = L/b (b = k₁w₀², the confocal parameter inside the crystal), B = ρ·√(L k₁)/2 (walk-off), σ = bΔk/2.
// With u = τ − τ' the inner integral has a closed form (partial fractions), so H is a single integral over u:
// 1/((a+iτ')(1−iτ')) = [1/(a+iτ') + 1/(1−iτ')]/(1+a), a = 1+iu, whose integrals are −i·ln(a+iτ') and i·ln(1−iτ');
// both arguments keep a positive real part, so the logarithms never cross their branch cut.
const cmul = (a, b) => [a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]];
const cdiv = (a, b) => { const d = b[0] * b[0] + b[1] * b[1]; return [(a[0] * b[0] + a[1] * b[1]) / d, (a[1] * b[0] - a[0] * b[1]) / d]; };
const clog = (a) => [Math.log(Math.hypot(a[0], a[1])), Math.atan2(a[1], a[0])];
function kernel(u, xi) { // ∫ dτ' / ((1+i(τ'+u))(1−iτ')) over the τ' where both τ' and τ'+u lie in [−ξ, ξ]
  const t1 = Math.max(-xi, -xi - u), t2 = Math.min(xi, xi - u);
  if (t2 <= t1) return [0, 0];
  const la2 = clog([1, u + t2]), la1 = clog([1, u + t1]), lb2 = clog([1, -t2]), lb1 = clog([1, -t1]);
  // −i(la2 − la1) + i(lb2 − lb1) = i·[(lb2 − lb1) − (la2 − la1)]
  const re = (lb2[0] - lb1[0]) - (la2[0] - la1[0]), im = (lb2[1] - lb1[1]) - (la2[1] - la1[1]);
  return cdiv([-im, re], [2, u]);
}
export function bkH(sigma, B, xi, N = 400) {
  const a = -2 * xi, h = (4 * xi) / N;
  let re = 0;
  for (let k = 0; k <= N; k++) {
    const u = a + k * h, w = k === 0 || k === N ? 1 : k % 2 ? 4 : 2;
    const ph = sigma * u, damp = Math.exp(-B * B * u * u / xi);
    re += w * cmul([damp * Math.cos(ph), damp * Math.sin(ph)], kernel(u, xi))[0];
  }
  return (re * h / 3) / (4 * xi);
}
// Golden-section maximum of f on [lo, hi].
function goldenMax(f, lo, hi, iters = 40) {
  const g = (Math.sqrt(5) - 1) / 2;
  let a = lo, b = hi, c = b - g * (b - a), d = a + g * (b - a), fc = f(c), fd = f(d);
  for (let i = 0; i < iters; i++) {
    if (fc > fd) { b = d; d = c; fd = fc; c = b - g * (b - a); fc = f(c); } else { a = c; c = d; fc = fd; d = a + g * (b - a); fd = f(d); }
  }
  const x = (a + b) / 2;
  return { x, f: f(x) };
}
// The best phase mismatch σ for a given ξ and B (the maximum of H over σ): a scan, then golden refinement.
export function bkBestSigma(B, xi) {
  let best = { x: 0, f: -Infinity };
  for (let s = -0.5; s <= 4.0001; s += 0.25) { const v = bkH(s, B, xi, 160); if (v > best.f) best = { x: s, f: v }; }
  const r = goldenMax((s) => bkH(s, B, xi), best.x - 0.25, best.x + 0.25, 30);
  return { sigma: r.x, h: r.f };
}
// h(B, ξ) at the best σ; with ξ null, also the best ξ (h_m(B): 1.068 at ξ = 2.84 for B = 0).
// xiMax caps ξ (a tighter focus would damage the crystal).
export function bkFocus(B, xi = null, xiMax = Infinity) {
  if (xi != null) return { xi, ...bkBestSigma(B, xi) };
  const top = Math.min(20, xiMax), grid = [];
  for (let k = 0; k <= 24; k++) { const x = 0.02 * Math.pow(top / 0.02, k / 24); grid.push([x, bkBestSigma(B, x).h]); }
  let i = grid.reduce((m, p, j) => (p[1] > grid[m][1] ? j : m), 0);
  if (i === grid.length - 1) return { xi: top, ...bkBestSigma(B, top), capped: xiMax < 20 };
  const lo = Math.log(grid[Math.max(0, i - 1)][0]), hi = Math.log(grid[i + 1][0]);
  const r = goldenMax((lx) => bkBestSigma(B, Math.exp(lx)).h, lo, hi, 18);
  const x = Math.exp(r.x);
  return { xi: x, ...bkBestSigma(B, x), capped: false };
}

// ---------- pulses
// P_peak = PEAK·E/τ (τ the intensity FWHM); TBP the transform-limited Δν·τ; the shapes' power P(t)/P_peak.
export const PEAK = { gauss: 2 * Math.sqrt(Math.LN2 / Math.PI), sech2: 0.881374, flat: 1 };
export const TBP = { gauss: 0.441, sech2: 0.315, flat: 0.886 };
const SHAPE = {
  gauss: (x) => Math.exp(-4 * Math.LN2 * x * x),
  sech2: (x) => 1 / Math.cosh(1.762747 * x) ** 2,
  flat: (x) => (Math.abs(x) <= 0.5 ? 1 : 0),
};
// The transform-limited spectral width (nm) of a pulse τ (s) at λ (µm).
export const pulseBandwidthNm = (lam_um, tau_s, shape = "gauss") => TBP[shape] * (lam_um * 1e-6) ** 2 / (C * tau_s) * 1e9;

// ---------- second-harmonic generation
// in: {lam_um (fundamental), n1, n2 (fundamental, harmonic), deff_pm, rho_mrad (largest walk-off), L_mm,
//      focus: {mode: "optimal"} | {mode: "waist", w0_um} | {mode: "safe", Imax} (the tightest focus whose peak intensity
//      stays under Imax, W/cm²), laser: {cw: true, P} (W) | {E, tau, rep, shape} (J, s, Hz)}.
// Type II SHG with the fundamental polarized at 45° gives the same formula with the whole power (each field carries half
// of it, and the two distinguishable fields double the nonlinear polarization).
export function shg(inp) {
  const lam = inp.lam_um * 1e-6, L = inp.L_mm * 1e-3, d = inp.deff_pm * 1e-12, k1 = 2 * Math.PI * inp.n1 / lam;
  const B = (inp.rho_mrad * 1e-3) * Math.sqrt(L * k1) / 2;
  const las = inp.laser, Ppk = las.cw ? las.P : PEAK[las.shape || "gauss"] * las.E / las.tau;
  const xiOf = (w0) => L / (k1 * w0 * w0);
  let f;
  if (inp.focus.mode === "waist") f = bkFocus(B, xiOf(inp.focus.w0_um * 1e-6));
  else if (inp.focus.mode === "safe" && inp.focus.Imax > 0) {
    const w0min = Math.sqrt(2 * Ppk / (Math.PI * inp.focus.Imax * 1e4)); // I = 2P/(πw²), Imax in W/cm²
    f = bkFocus(B, null, xiOf(w0min));
  } else f = bkFocus(B, null);
  const w0 = Math.sqrt(L / (f.xi * k1));
  const kappa = 16 * Math.PI ** 2 * d * d * L * f.h / (EPS0 * C * lam ** 3 * inp.n1 * inp.n2); // P₂ = κP₁² (1/W)
  const I = 2 * Ppk / (Math.PI * w0 * w0) / 1e4; // peak intensity at the focus, W/cm²
  const out = { B, xi: f.xi, h: f.h, sigma: f.sigma, capped: Boolean(f.capped), w0_um: w0 * 1e6,
    zR_mm: k1 * w0 * w0 / 2 * 1e3, kappa, Ppk, I_peak: I, dk_per_mm: 2 * f.sigma / (k1 * w0 * w0) * 1e-3 };
  if (las.cw) {
    const und = kappa * las.P * las.P, dep = las.P * Math.tanh(Math.sqrt(kappa * las.P)) ** 2;
    return { ...out, P2_und: und, P2: dep, eta_und: und / las.P, eta: dep / las.P };
  }
  const e = pulseSH(kappa, las.E, las.tau, las.shape);
  return { ...out, F_peak: 2 * las.E / (Math.PI * w0 * w0) / 1e4, E2_und: e.und, E2: e.dep, eta_und: e.und / las.E, eta: e.dep / las.E,
    P2avg: e.dep * (las.rep || 0), P2pk: Ppk * Math.tanh(Math.sqrt(kappa * Ppk)) ** 2 };
}
// Second-harmonic pulse energy (J) of a pulse E (J), τ (s) with P₂(t) = κP(t)² (und) and with the pump depleted as a
// plane wave, P·tanh²(√(κP)) (dep): the instantaneous conversion integrated over the pulse (quasi-static: the pulse is
// longer than the delay the group-velocity mismatch builds up in the crystal).
export function pulseSH(kappa, E, tau, shape = "gauss") {
  const Ppk = PEAK[shape] * E / tau;
  if (shape === "flat") return { und: kappa * Ppk * Ppk * tau, dep: Ppk * Math.tanh(Math.sqrt(kappa * Ppk)) ** 2 * tau };
  const f = SHAPE[shape], N = 2000, span = 3, dt = 2 * span / N;
  let und = 0, dep = 0;
  for (let k = 0; k <= N; k++) {
    const P = Ppk * f(-span + k * dt), w = k === 0 || k === N ? 0.5 : 1;
    und += w * kappa * P * P; dep += w * P * Math.tanh(Math.sqrt(kappa * P)) ** 2;
  }
  return { und: und * dt * tau, dep: dep * dt * tau };
}

// ---------- laser damage
// A crystal's threshold (props.json damage: value, unit GW/cm2 or J/cm2, tau_ns) at the pulse length of the laser:
// fluence F = I·τ, and F_th ∝ √τ for pulses from about 10 ps to a microsecond (thermal diffusion during the pulse:
// Stuart et al., Phys. Rev. Lett. 74, 2248 (1995); Wood, "Laser-Induced Damage of Optical Materials" (2003)).
// Shorter pulses break the rule (multiphoton ionization), and a threshold of unknown pulse length is not scaled.
// Returns {F, I} (J/cm², W/cm²; one may be null) and how: "same" (pulse within 2× of the source's), "scaled", "noref"
// (the source gives no pulse length), "short" (below 10 ps: no estimate), "cw".
export const SHORT_S = 1e-11;
export function thresholdAt(dmg, tau_s) {
  if (!dmg || !(dmg.value > 0)) return null;
  const ref = dmg.tau_ns ? dmg.tau_ns * 1e-9 : null;
  const Fref = dmg.unit === "J/cm2" ? dmg.value : ref ? dmg.value * 1e9 * ref : null;
  const Iref = dmg.unit === "GW/cm2" ? dmg.value * 1e9 : ref ? dmg.value / ref : null;
  if (!tau_s) return { F: null, I: null, how: "cw", ref, Fref, Iref };
  if (!ref) return { F: dmg.unit === "J/cm2" ? Fref : null, I: dmg.unit === "GW/cm2" ? Iref : null, how: "noref", ref, Fref, Iref };
  if (tau_s / ref <= 2 && ref / tau_s <= 2) return { F: Fref, I: Iref, how: "same", ref, Fref, Iref };
  if (tau_s < SHORT_S || ref < SHORT_S) return { F: null, I: null, how: "short", ref, Fref, Iref };
  const F = Fref * Math.sqrt(tau_s / ref);
  return { F, I: F / tau_s, how: "scaled", ref, Fref, Iref };
}
// A beam against a threshold. laser: {cw, P} or {E, tau, rep, shape}; w_um the 1/e² radius at the crystal (or flat: the
// radius of a top-hat beam with top: true); S the safety factor asked for. Peak (on-axis) values: a Gaussian's peak
// intensity is twice its mean over πw².
export function damageMargin(laser, w_um, dmg, S = 2, top = false) {
  const area = Math.PI * (w_um * 1e-4) ** 2, g = top ? 1 : 2; // cm²; peak/mean
  const Ppk = laser.cw ? laser.P : PEAK[laser.shape || "gauss"] * laser.E / laser.tau;
  const I = g * Ppk / area, F = laser.cw ? null : g * laser.E / area, Iavg = laser.cw ? I : g * laser.E * (laser.rep || 0) / area;
  const th = thresholdAt(dmg, laser.cw ? null : laser.tau);
  const out = { I, F, Iavg, Ppk, th, ratio: null };
  if (!th || th.how === "cw" || th.how === "short") return out;
  const r = [th.F && F != null ? F / th.F : null, th.I ? I / th.I : null].filter((x) => x != null);
  if (!r.length) return out;
  const ratio = Math.max(...r);
  // the largest pulse energy (or power) and the smallest beam radius that keep the margin S
  return { ...out, ratio, verdict: ratio * S <= 1 ? "ok" : ratio < 1 ? "thin" : "over",
    Emax: laser.cw ? null : laser.E / (ratio * S), Pmax: laser.cw ? laser.P / (ratio * S) : (laser.E / (ratio * S)) * (laser.rep || 0),
    wmin_um: w_um * Math.sqrt(ratio * S),
    // the peak intensity that keeps the margin, for focusing (I = PEAK·F/τ for a pulse)
    Ilim: Math.min(...[th.I, th.F && !laser.cw ? PEAK[laser.shape || "gauss"] * th.F / laser.tau : null].filter((x) => x > 0)) / S };
}
