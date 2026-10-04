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
