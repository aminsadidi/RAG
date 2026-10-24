// Phase matching of three-wave mixing in birefringent crystals, in the principal planes.
// λ in µm, angles in radians (degrees only for display). The waves: λ1 + λ2 → λ3 with
// 1/λ3 = 1/λ1 + 1/λ2. The highest frequency travels in the fast (lower-index) eigenmode, as it must
// with normal dispersion: type I is s + s → f, type II is s + f → f or f + s → f.
// nAt(λ) gives the principal indices [nx, ny, nz] (a uniaxial crystal: [no, no, ne]).

const TWO_PI = 2 * Math.PI;
export const TYPES = { I: ["s", "s"], IIa: ["s", "f"], IIb: ["f", "s"] };
// Half maximum of sinc²(ΔkL/2) at ΔkL/2 = 1.39156: the full width of the acceptance is |Δk| < 2.78312/L.
const HALF = 2.78312;
const L_UM = 1e4; // acceptance bandwidths are given for a 1 cm crystal

// Unit propagation vector in a principal plane; the angle is θ from z (yz, xz) or φ from x (xy).
export function direction(plane, a) {
  const c = Math.cos(a), s = Math.sin(a);
  if (plane === "xy") return [c, s, 0];
  if (plane === "yz") return [0, s, c];
  return [s, 0, c]; // xz; also a uniaxial crystal (θ from the optic axis)
}

// The two refractive indices [slow, fast] for propagation along s (Fresnel's equation, solved for 1/n²).
export function eigenIndices([nx, ny, nz], [sx, sy, sz]) {
  const ax = nx ** -2, ay = ny ** -2, az = nz ** -2;
  const b = sx * sx * (ay + az) + sy * sy * (ax + az) + sz * sz * (ax + ay);
  const c = sx * sx * ay * az + sy * sy * ax * az + sz * sz * ax * ay;
  const r = Math.sqrt(Math.max(0, b * b - 4 * c));
  return [1 / Math.sqrt((b - r) / 2), 1 / Math.sqrt((b + r) / 2)];
}

// The three wavelengths of a process: SHG of λ; SFG of λ1 and λ2; DFG/OPO with pump λp and signal λs.
export function waves(process, a, b) {
  if (process === "shg") return { l1: a, l2: a, l3: a / 2 };
  if (process === "sfg") return { l1: a, l2: b, l3: 1 / (1 / a + 1 / b) };
  return { l1: b, l2: 1 / (1 / a - 1 / b), l3: a }; // opo: a = pump, b = signal → idler
}
// The same process with its tuned wavelength moved by d (SHG: λ; SFG: λ1; OPO: the signal).
export function shifted(process, a, b, d) {
  return process === "shg" ? waves(process, a + d) : process === "sfg" ? waves(process, a + d, b) : waves(process, a, b + d);
}

function indexOf(nAt, plane, a, lam, pol) {
  const [s, f] = eigenIndices(nAt(lam), direction(plane, a));
  return pol === "s" ? s : f;
}

// Phase mismatch Δk = k3 − k1 − k2 in µm⁻¹.
export function deltaK(nAt, plane, a, w, type) {
  const [p1, p2] = TYPES[type];
  return TWO_PI * (indexOf(nAt, plane, a, w.l3, "f") / w.l3 - indexOf(nAt, plane, a, w.l1, p1) / w.l1
    - indexOf(nAt, plane, a, w.l2, p2) / w.l2);
}

function bisect(f, a, b, fa) {
  for (let k = 0; k < 60; k++) {
    const m = (a + b) / 2, fm = f(m);
    if (Math.sign(fm) === Math.sign(fa)) { a = m; fa = fm; } else b = m;
  }
  return (a + b) / 2;
}

// Phase-matching angles in [0, 90°] of one plane and type.
export function roots(f, steps = 720) {
  const out = [];
  let a0 = 0, f0 = f(0);
  for (let k = 1; k <= steps; k++) {
    const a1 = (Math.PI / 2) * k / steps, f1 = f(a1);
    if (!Number.isFinite(f0) || !Number.isFinite(f1)) { a0 = a1; f0 = f1; continue; }
    if (f0 === 0) out.push(a0);
    else if (Math.sign(f0) !== Math.sign(f1)) out.push(f1 === 0 ? a1 : bisect(f, a0, a1, f0));
    a0 = a1; f0 = f1;
  }
  if (f0 === 0) out.push(a0);
  return out;
}

// Full width of |g(x)| < limit around x = 0 (g(0) = 0): the distance to the edges on both sides.
function width(g, limit, start, max) {
  const edge = (dir) => {
    let x = start;
    while (Math.abs(g(dir * x)) < limit) { x *= 2; if (x > max) return max; }
    let lo = x / 2, hi = x;
    if (Math.abs(g(dir * lo)) >= limit) lo = 0;
    for (let k = 0; k < 50; k++) { const m = (lo + hi) / 2; if (Math.abs(g(dir * m)) < limit) lo = m; else hi = m; }
    return (lo + hi) / 2;
  };
  return edge(1) + edge(-1);
}

// Walk-off angle of the wave λ with polarization pol: ρ = −(1/n)·dn/dangle (radians).
export function walkOff(nAt, plane, a, lam, pol) {
  const h = 1e-5, n = indexOf(nAt, plane, a, lam, pol);
  return -(indexOf(nAt, plane, a + h, lam, pol) - indexOf(nAt, plane, a - h, lam, pol)) / (2 * h) / n;
}

// Group index n_g = n − λ·dn/dλ of the wave λ with polarization pol along the fixed direction.
export function groupIndex(nAt, plane, a, lam, pol) {
  const h = 1e-4, n = (l) => indexOf(nAt, plane, a, l, pol), n0 = n(lam), up = n(lam + h), down = n(lam - h);
  // at the end of a formula's range (tabulated data stops there) a one-sided difference
  const slope = Number.isFinite(up) && Number.isFinite(down) ? (up - down) / (2 * h) : Number.isFinite(up) ? (up - n0) / h : (n0 - down) / h;
  return n0 - lam * slope;
}

// Everything about one phase-matching solution.
export function describe(nAt, plane, a, process, p, q, type) {
  const w = waves(process, p, q), [p1, p2] = TYPES[type];
  const limit = HALF / L_UM;
  const angular = width((x) => deltaK(nAt, plane, a + x, w, type), limit, 1e-6, 0.5);
  const spectral = width((d) => deltaK(nAt, plane, a, shifted(process, p, q, d), type), limit, 1e-6, 0.5);
  const rho = [[w.l1, p1], [w.l2, p2], [w.l3, "f"]].map(([lam, pol]) => walkOff(nAt, plane, a, lam, pol));
  const n = [[w.l1, p1], [w.l2, p2], [w.l3, "f"]].map(([lam, pol]) => indexOf(nAt, plane, a, lam, pol));
  const ng = [[w.l1, p1], [w.l2, p2], [w.l3, "f"]].map(([lam, pol]) => groupIndex(nAt, plane, a, lam, pol));
  return {
    plane, type, angle: a * 180 / Math.PI, waves: w, pol: [p1, p2, "f"], n,
    walkoff_mrad: rho.map((r) => Math.abs(r) * 1e3), // per wave
    group_index: ng,
    gvm_fs_mm: [ng[0] - ng[2], ng[1] - ng[2], ng[0] - ng[1]].map((d) => d / 2.99792458e-4), // 1/v_g differences: 1−3, 2−3, 1−2
    angular_mrad: angular * 1e3, // for a 1 cm crystal
    spectral_nm: spectral * 1e3, // of the tuned wavelength, for a 1 cm crystal
    noncritical: a < 1e-4 || Math.abs(a - Math.PI / 2) < 1e-4,
  };
}

// All solutions of a process in a crystal: uniaxial crystals have one plane (θ), biaxial ones three.
export function solveAll(nAt, kind, process, p, q) {
  const w = waves(process, p, q), out = [];
  if (!(w.l1 > 0 && w.l2 > 0 && w.l3 > 0)) return out;
  const planes = kind === "uniaxial" ? ["xz"] : ["xy", "yz", "xz"];
  const types = process === "shg" ? ["I", "IIa"] : ["I", "IIa", "IIb"];
  for (const plane of planes) for (const type of types) {
    for (const a of roots((x) => deltaK(nAt, plane, x, w, type))) out.push(describe(nAt, plane, a, process, p, q, type));
  }
  return out;
}

// ---------- effective nonlinear coefficient

// Eigenvalues and eigenvectors of a symmetric 3×3 matrix (Jacobi rotations): [[λ, v], ...].
function eigSym(a) {
  a = a.map((r) => [...r]);
  const v = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  for (let sweep = 0; sweep < 50; sweep++) {
    let off = 0;
    for (let p = 0; p < 2; p++) for (let q = p + 1; q < 3; q++) off += a[p][q] ** 2;
    if (off < 1e-30) break;
    for (let p = 0; p < 2; p++) for (let q = p + 1; q < 3; q++) {
      if (Math.abs(a[p][q]) < 1e-300) continue;
      const th = (a[q][q] - a[p][p]) / (2 * a[p][q]);
      const t = Math.sign(th || 1) / (Math.abs(th) + Math.sqrt(th * th + 1)), c = 1 / Math.sqrt(t * t + 1), s = t * c;
      for (let k = 0; k < 3; k++) { const akp = a[k][p], akq = a[k][q]; a[k][p] = c * akp - s * akq; a[k][q] = s * akp + c * akq; }
      for (let k = 0; k < 3; k++) { const apk = a[p][k], aqk = a[q][k]; a[p][k] = c * apk - s * aqk; a[q][k] = s * apk + c * aqk; }
      for (let k = 0; k < 3; k++) { const vkp = v[k][p], vkq = v[k][q]; v[k][p] = c * vkp - s * vkq; v[k][q] = s * vkp + c * vkq; }
    }
  }
  return [0, 1, 2].map((i) => [a[i][i], [v[0][i], v[1][i], v[2][i]]]);
}

// Unit electric-field vectors [slow, fast] for propagation along s: the D vectors are the eigenvectors
// of the inverse dielectric tensor projected on the plane normal to s (eigenvalues 1/n²), and E ∝ η·D.
export function fieldVectors([nx, ny, nz], s) {
  const eta = [nx ** -2, ny ** -2, nz ** -2];
  const P = [0, 1, 2].map((i) => [0, 1, 2].map((j) => (i === j ? 1 : 0) - s[i] * s[j]));
  const M = [0, 1, 2].map((i) => [0, 1, 2].map((j) => [0, 1, 2].reduce((acc, k) => acc + P[i][k] * eta[k] * P[k][j], 0)));
  const modes = eigSym(M).filter(([, v]) => Math.abs(v[0] * s[0] + v[1] * s[1] + v[2] * s[2]) < 0.5).sort((p, q) => p[0] - q[0]);
  return modes.slice(0, 2).map(([, d]) => { const e = d.map((x, i) => x * eta[i]), n = Math.hypot(...e); return e.map((x) => x / n); });
}

// d_ijk (pm/V) from contracted elements {"22": 2.2, ...}; l = 1..6 ↔ xx, yy, zz, yz, xz, xy.
const PAIRS = { 1: [[0, 0]], 2: [[1, 1]], 3: [[2, 2]], 4: [[1, 2], [2, 1]], 5: [[0, 2], [2, 0]], 6: [[0, 1], [1, 0]] };
export function dTensor(elements) {
  const d = [0, 1, 2].map(() => [0, 1, 2].map(() => [0, 0, 0]));
  for (const [il, v] of Object.entries(elements)) {
    const i = +String(il)[0] - 1;
    for (const [j, k] of PAIRS[+String(il)[1]]) d[i][j][k] = v;
  }
  return d;
}
export function contract(d, e3, e1, e2) {
  let sum = 0;
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) for (let k = 0; k < 3; k++) sum += e3[i] * d[i][j][k] * e1[j] * e2[k];
  return sum;
}

// |d_eff| of a phase-matching solution (from describe/solveAll). A uniaxial crystal is free in φ:
// the best φ is taken. A biaxial one is evaluated for the four equivalent directions of the
// principal plane (they differ in monoclinic crystals) and the best is kept.
export function effectiveD(nAt, kind, sol, d) {
  const a = sol.angle * Math.PI / 180, w = sol.waves, D = dTensor(d);
  const mode = (lam, pol, s) => fieldVectors(nAt(lam), s)[pol === "s" ? 0 : 1];
  const at = (s) => Math.abs(contract(D, mode(w.l3, sol.pol[2], s), mode(w.l1, sol.pol[0], s), mode(w.l2, sol.pol[1], s)));
  if (kind === "uniaxial") {
    let best = { deff: 0, phi: 0 };
    for (let k = 0; k < 360; k += 1) {
      const p = k * Math.PI / 180, v = at([Math.sin(a) * Math.cos(p), Math.sin(a) * Math.sin(p), Math.cos(a)]);
      if (v > best.deff + 1e-12) best = { deff: v, phi: k };
    }
    return best;
  }
  const c = Math.cos(a), s = Math.sin(a);
  const dirs = sol.plane === "xy" ? [[c, s, 0], [c, -s, 0], [-c, s, 0], [-c, -s, 0]]
    : sol.plane === "yz" ? [[0, s, c], [0, -s, c], [0, s, -c], [0, -s, -c]] : [[s, 0, c], [-s, 0, c], [s, 0, -c], [-s, 0, -c]];
  const vals = dirs.map(at);
  return { deff: Math.max(...vals), spread: Math.max(...vals) - Math.min(...vals) };
}

// Noncritical phase matching by temperature: the waves travel along a principal axis and are polarized
// along the other two, so only the temperature tunes Δk. nAtT(T) gives λ → [nx, ny, nz] at T (°C).
// Returns every polarization assignment that phase-matches between lo and hi, with its temperature and,
// when the d tensor is given, |d_eff| (unit field vectors along the axes).
const AXES = ["x", "y", "z"];
export function ncpmTemperatures(nAtT, kind, process, a, b, d, [lo, hi] = [-50, 300]) {
  const w = waves(process, a, b), D = d ? dTensor(d) : null, unit = (i) => [0, 1, 2].map((j) => (j === i ? 1 : 0));
  const found = [];
  for (const k of kind === "uniaxial" ? [0] : [0, 1, 2]) {
    const across = [0, 1, 2].filter((i) => i !== k);
    for (const p1 of across) for (const p2 of across) for (const p3 of across) {
      if (p1 === p2 && p2 === p3) continue; // no birefringence to compensate the dispersion
      if (process === "shg" && p1 > p2) continue; // the same pair of fundamental waves
      const f = (T) => { const n = nAtT(T); return n(w.l3)[p3] / w.l3 - n(w.l1)[p1] / w.l1 - n(w.l2)[p2] / w.l2; };
      let t0 = lo, f0 = f(lo);
      for (let T = lo + 1; T <= hi; T += 1) {
        const f1 = f(T);
        if (Number.isFinite(f0) && Number.isFinite(f1) && Math.sign(f0) !== Math.sign(f1)) {
          const t = bisect(f, t0, T, f0);
          found.push({ axis: kind === "uniaxial" ? "⊥ z" : AXES[k], pol: [p1, p2, p3].map((i) => AXES[i]), T: t, waves: w,
            deff: D ? Math.abs(contract(D, unit(p3), unit(p1), unit(p2))) : null });
        }
        t0 = T; f0 = f1;
      }
    }
  }
  return found.sort((p, q) => p.T - q.T);
}

// ---------- temperature: a crystal already cut, and the oven it needs

// Temperatures in [lo, hi] at which a crystal cut along (plane, angle a, radians) phase-matches the process:
// the question to ask before buying a crystal for an oven of limited range. nAtT(T) gives λ → [nx, ny, nz].
export function cutTemperatures(nAtT, plane, a, process, p, q, type, [lo, hi] = [-50, 300]) {
  const w = waves(process, p, q), f = (T) => deltaK(nAtT(T), plane, a, w, type), out = [];
  let t0 = lo, f0 = f(lo);
  for (let T = lo + 1; T <= hi; T += 1) {
    const f1 = f(T);
    if (Number.isFinite(f0) && Number.isFinite(f1) && Math.sign(f0) !== Math.sign(f1)) out.push(bisect(f, t0, T, f0));
    t0 = T; f0 = f1;
  }
  return out;
}

// Temperature acceptance (FWHM, °C) of a 1 cm crystal phase-matched at T along (plane, a): divide by L in cm.
// Infinity when Δk does not change with T within 500 °C (no thermo-optic data).
export function temperatureAcceptance(nAtT, plane, a, process, p, q, type, T) {
  const w = waves(process, p, q), k0 = deltaK(nAtT(T), plane, a, w, type);
  const g = (x) => deltaK(nAtT(T + x), plane, a, w, type) - k0;
  return width(g, HALF / L_UM, 1e-3, 500);
}

// The same for 90° (noncritical) phase matching along a principal axis, with the axes of the three
// polarizations (indices 0..2, as the rows of ncpmTemperatures give them).
export function ncpmAcceptance(nAtT, process, a, b, pol, T) {
  const w = waves(process, a, b), [p1, p2, p3] = pol.map((x) => (typeof x === "number" ? x : AXES.indexOf(x)));
  const dk = (t) => { const n = nAtT(t); return TWO_PI * (n(w.l3)[p3] / w.l3 - n(w.l1)[p1] / w.l1 - n(w.l2)[p2] / w.l2); };
  const k0 = dk(T);
  return width((x) => dk(T + x) - k0, HALF / L_UM, 1e-3, 500);
}

// ---------- quasi-phase matching (a grating of period Λ supplies 2π/Λ): periodically poled ferroelectrics
// (PPLN, PPKTP, ...) along a principal axis with the fields along the other two, and orientation-patterned cubic
// semiconductors (OP-GaAs, OP-GaP). First order: d_eff = (2/π)·|d_ijk e3 e1 e2|; for the cubic ones (2/π)·d14, the
// figure of merit of Petrov (2015), Table 3, as in the phase-matching tab.
// Returns the period at T, d_eff, and the spectral and temperature widths of a 1 cm grating (the grating's own
// thermal expansion is left out). kind: "poled" or "op".
export function qpmSolutions(nAtT, cryst, kind, d, process, a, b, T) {
  const w = waves(process, a, b), D = dTensor(d), out = [], unit = (i) => [0, 1, 2].map((j) => (j === i ? 1 : 0));
  const width0 = (g) => width(g, HALF / L_UM, 1e-6, 0.5);
  if (kind === "op") {
    const n = (T2, l) => nAtT(T2)(l)[0];
    const dk = (T2, ww) => TWO_PI * (n(T2, ww.l3) / ww.l3 - n(T2, ww.l1) / ww.l1 - n(T2, ww.l2) / ww.l2);
    const kg = dk(T, w);
    if (!kg) return out;
    out.push({ how: "qpm", qpm: "op", axis: "", pol: [], type: "0", period_um: TWO_PI / Math.abs(kg),
      n: [n(T, w.l1), n(T, w.l2), n(T, w.l3)], deff: (2 / Math.PI) * Math.abs(d["14"] ?? 0), walkoff_mrad: [0, 0, 0], noncritical: true,
      spectral_nm: width0((x) => dk(T, shifted(process, a, b, x)) - kg) * 1e3,
      temp_C: width((x) => dk(T + x, w) - kg, HALF / L_UM, 1e-3, 500) });
    return out;
  }
  for (const k of cryst === "uniaxial" ? [0] : [0, 1]) { // along x (and y for biaxial crystals); z is the polar axis
    const across = [0, 1, 2].filter((i) => i !== k);
    for (const p3 of across) for (const p1 of across) for (const p2 of across) {
      if (p1 > p2 && Math.abs(w.l1 - w.l2) < 1e-9) continue; // SHG or degenerate: the same pair of waves
      const deff = (2 / Math.PI) * Math.abs(contract(D, unit(p3), unit(p1), unit(p2)));
      if (deff < 0.005) continue;
      const dk = (T2, ww) => { const n = nAtT(T2); return TWO_PI * (n(ww.l3)[p3] / ww.l3 - n(ww.l1)[p1] / ww.l1 - n(ww.l2)[p2] / ww.l2); };
      const kg = dk(T, w);
      if (!kg || !Number.isFinite(kg)) continue; // the grating vector may point either way: Λ = 2π/|Δk|
      const n = nAtT(T);
      out.push({ how: "qpm", qpm: "poled", axis: AXES[k], pol: [p1, p2, p3].map((i) => AXES[i]),
        type: p1 === p2 ? (p1 === p3 ? "0" : "I") : "II", period_um: TWO_PI / Math.abs(kg),
        n: [n(w.l1)[p1], n(w.l2)[p2], n(w.l3)[p3]], deff, walkoff_mrad: [0, 0, 0], noncritical: true,
        spectral_nm: width0((x) => dk(T, shifted(process, a, b, x)) - kg) * 1e3,
        temp_C: width((x) => dk(T + x, w) - kg, HALF / L_UM, 1e-3, 500) });
    }
  }
  // along y the all-z configuration repeats the one along x (same indices): kept once
  const seen = new Set();
  return out.filter((r) => { const k = `${r.pol.join("")}|${r.period_um.toFixed(6)}`; if (seen.has(k)) return false; seen.add(k); return true; });
}

// ---------- crystal advisor

// The shortest first-order poling period reported: 1.4 µm in PPMgLN (Nikogosyan 2005, p. 175 of the PDF)
export const MIN_PERIOD = 1.4;

// Every crystal that can do the process under the fixed conditions, best first, and the ones that cannot
// with the reason. crystals: [{material, kind, range_um, thermo (true if dn/dT is known), nAtT(T), d,
// transparency ([lo, hi] µm, if known), hygroscopic ("none", "slight", "yes", "strong", if known), qpm ("poled",
// "op" or absent: whether a periodically poled or orientation-patterned form exists), minPump (µm, the shortest
// wavelength it tolerates), cls (how established: basic, main-ir, often, poled, new, sfd, rare, newer)}].
// want: {process, a, b, T: [lo, hi] (the oven or the room; one value for a fixed temperature), type
// ("any", "I", "II"), ncpm (90° only), maxWalkoff (mrad), minSpectral (nm·cm), minAngular (mrad·cm),
// minTemp (°C·cm), needThermo, dry (no crystal a source calls hygroscopic), qpm (false: birefringent only),
// qpmOnly, minPeriod (µm: shorter gratings are hard to pole), classes (the cls values to keep; "research" for none),
// length (cm, for the bandwidths)}.
// nAtT with its values kept: the advisor asks for the same few wavelengths at the same temperatures thousands of
// times (every step of an angle scan needs the principal indices at λ1, λ2, λ3 again), which made it ~10× slower.
function memoT(nAtT) {
  const byT = new Map();
  return (T) => {
    let f = byT.get(T);
    if (!f) {
      const n = nAtT(T), byL = new Map();
      f = (l) => { let v = byL.get(l); if (v === undefined) { v = n(l); byL.set(l, v); } return v; };
      byT.set(T, f);
    }
    return f;
  };
}

export function advise(crystals, want) {
  const { process, a, b } = want, w = waves(process, a, b);
  const [lo, hi] = Array.isArray(want.T) ? want.T : [want.T ?? 25, want.T ?? 25];
  const mid = (lo + hi) / 2, L = want.length || 1, ok = [], no = [];
  // type "0": QPM with all three waves along one axis (d33 of PPLN, PPKTP)
  const typeOk = (t) => !want.type || want.type === "any" || want.type === t || (want.type === "II" && (t === "IIa" || t === "IIb"));
  for (const c0 of crystals) {
    const c = { ...c0, nAtT: memoT(c0.nAtT) };
    const why = (reason) => no.push({ material: c.material, reason });
    // the transmission range a source states, when known (crystal_properties.yml): a wave outside it is absorbed,
    // one within 10 % of an edge is marked (the "0" level edges are where transmission vanishes)
    const t = c.transparency;
    if (t && ![w.l1, w.l2, w.l3].every((l) => l >= t[0] && l <= t[1])) { why("absorbed"); continue; }
    const edge = Boolean(t) && [w.l1, w.l2, w.l3].some((l) => l < t[0] * 1.1 || l > t[1] / 1.1);
    if (![w.l1, w.l2, w.l3].every((l) => l >= c.range_um[0] - 1e-9 && l <= c.range_um[1] + 1e-9)) { why("range"); continue; }
    // how established the crystal is (a chapter of Nikogosyan 2005, or "newer"); a crystal no handbook treats is "research"
    if (want.classes && !want.classes.includes(c.cls || "research")) { why("class"); continue; }
    // the shortest wavelength the crystal tolerates (two-photon or residual absorption, crystal_properties.yml)
    if (c.minPump && w.l3 < c.minPump) { why("pump"); continue; }
    if (want.needThermo && !c.thermo) { why("no-thermo"); continue; }
    if (want.dry && (c.hygroscopic === "yes" || c.hygroscopic === "strong")) { why("hygroscopic"); continue; }
    // a cubic crystal (CdTe, GaAs) has no birefringence: phase matching by quasi-phase matching only
    const n0 = c.nAtT(lo)(w.l1), isotropic = Math.max(...n0) - Math.min(...n0) < 1e-6;
    if (isotropic && !(c.qpm && want.qpm !== false)) { why("isotropic"); continue; }
    const D = c.d ? dTensor(c.d) : null, found = [];
    if (c.qpm && c.d && want.qpm !== false) {
      for (const q of qpmSolutions(c.nAtT, c.kind, c.qpm, c.d, process, a, b, mid)) {
        if (typeOk(q.type)) found.push(c.thermo ? q : { ...q, temp_C: null }); // no dn/dT: no temperature width
      }
    }
    // critical phase matching at the middle of the temperature range; its angle at both ends
    if (!want.ncpm && !isotropic && !want.qpmOnly) {
      for (const s of solveAll(c.nAtT(mid), c.kind, process, a, b)) {
        if (!typeOk(s.type)) continue;
        const e = c.d ? effectiveD(c.nAtT(mid), c.kind, s, c.d) : null;
        // the angle of the same solution at T: the root of its plane and type nearest the one at the middle
        const ang = (T) => roots((x) => deltaK(c.nAtT(T), s.plane, x, w, s.type)).map((x) => x * 180 / Math.PI)
          .reduce((x, y) => (Math.abs(y - s.angle) < Math.abs(x - s.angle) ? y : x), Infinity);
        found.push({ ...s, how: s.noncritical ? "ncpm-angle" : "angle", deff: e ? e.deff : null,
          ...(() => { // the angle at both ends: Infinity when phase matching is lost there (the angle passes 90°)
            if (!c.thermo || !(hi > lo)) return { drift_deg: null };
            const d = Math.abs(ang(hi) - ang(lo));
            return Number.isFinite(d) ? { drift_deg: d } : { drift_deg: null, lostInRange: true };
          })(),
          temp_C: c.thermo ? temperatureAcceptance(c.nAtT, s.plane, s.angle * Math.PI / 180, process, a, b, s.type, mid) : null });
      }
    }
    // 90° phase matching tuned by temperature, anywhere from −50 to 300 °C; outside the range it is a near miss
    if (c.thermo && !isotropic && !want.qpmOnly) {
      for (const r of ncpmTemperatures(c.nAtT, c.kind, process, a, b, c.d, [-50, 300])) {
        const type = r.pol[0] === r.pol[1] ? "I" : "II";
        if (!typeOk(type)) continue;
        const n = c.nAtT(r.T), idx = r.pol.map((x) => AXES.indexOf(x)), nn = [n(w.l1)[idx[0]], n(w.l2)[idx[1]], n(w.l3)[idx[2]]];
        found.push({ how: "ncpm-temp", axis: r.axis, pol: r.pol, T: r.T, type, n: nn, deff: r.deff, walkoff_mrad: [0, 0, 0],
          noncritical: true, inRange: r.T >= lo - 1e-9 && r.T <= hi + 1e-9, temp_C: ncpmAcceptance(c.nAtT, process, a, b, idx, r.T) });
      }
    }
    if (!found.length) { why("no-pm"); continue; }
    const rated = found.map((s) => {
      const fails = [];
      if (s.how === "ncpm-temp" && !s.inRange) fails.push("temp");
      if (want.ncpm && !s.noncritical) fails.push("ncpm");
      if (s.how === "qpm" && s.period_um < (want.minPeriod ?? MIN_PERIOD)) fails.push("period");
      if (D && s.deff !== null && s.deff < 0.005) fails.push("deff0");
      if (want.maxWalkoff != null && Math.max(...s.walkoff_mrad) > want.maxWalkoff) fails.push("walkoff");
      if (want.minSpectral != null && s.spectral_nm != null && s.spectral_nm / L < want.minSpectral) fails.push("spectral");
      if (want.minAngular != null && s.angular_mrad != null && s.angular_mrad / L < want.minAngular) fails.push("angular");
      if (want.minTemp != null && (s.temp_C == null || s.temp_C / L < want.minTemp)) fails.push("tempacc");
      return { ...s, fails, fom: s.deff == null ? null : s.deff ** 2 / (s.n[0] * s.n[1] * s.n[2]) };
    });
    const good = rated.filter((s) => !s.fails.length);
    const byFom = (p, q) => (q.fom ?? -1) - (p.fom ?? -1) || Math.max(...p.walkoff_mrad) - Math.max(...q.walkoff_mrad);
    if (good.length) ok.push({ material: c.material, thermo: c.thermo, edge, best: good.sort(byFom)[0], all: good.sort(byFom) });
    else {
      const near = rated.sort((p, q) => p.fails.length - q.fails.length || byFom(p, q))[0];
      no.push({ material: c.material, reason: near.fails[0], near });
    }
  }
  ok.sort((p, q) => byFomTop(p, q));
  return { ok, no, waves: w, range: [lo, hi] };
}
const byFomTop = (p, q) => (q.best.fom ?? -1) - (p.best.fom ?? -1) || Math.max(...p.best.walkoff_mrad) - Math.max(...q.best.walkoff_mrad);
