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

// Everything about one phase-matching solution.
export function describe(nAt, plane, a, process, p, q, type) {
  const w = waves(process, p, q), [p1, p2] = TYPES[type];
  const limit = HALF / L_UM;
  const angular = width((x) => deltaK(nAt, plane, a + x, w, type), limit, 1e-6, 0.5);
  const spectral = width((d) => deltaK(nAt, plane, a, shifted(process, p, q, d), type), limit, 1e-6, 0.5);
  const rho = [[w.l1, p1], [w.l2, p2], [w.l3, "f"]].map(([lam, pol]) => walkOff(nAt, plane, a, lam, pol));
  const n = [[w.l1, p1], [w.l2, p2], [w.l3, "f"]].map(([lam, pol]) => indexOf(nAt, plane, a, lam, pol));
  return {
    plane, type, angle: a * 180 / Math.PI, waves: w, pol: [p1, p2, "f"], n,
    walkoff_mrad: rho.map((r) => Math.abs(r) * 1e3), // per wave
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
