// n(λ) for refractiveindex.info formula types 1-9: the same formulas as src/matrag/dispersion.py
// (checked against it by test/dispersion.test.js). λ in µm; coefficients C1..Cn as in the YAML files.
export function refractiveIndex(type, coefficients, lam) {
  const c = [...coefficients, ...Array(17).fill(0)].slice(0, 17);
  const C = (i) => c[i - 1];
  const l2 = lam * lam;
  let n2;
  switch (type) {
    case 1: case 2: // Sellmeier; type 1 has squared poles
      n2 = 1 + C(1);
      for (let i = 2; i < 17; i += 2) if (C(i)) n2 += C(i) * l2 / (l2 - (type === 1 ? C(i + 1) ** 2 : C(i + 1)));
      return Math.sqrt(n2);
    case 3: // polynomial
      n2 = C(1);
      for (let i = 2; i < 17; i += 2) if (C(i)) n2 += C(i) * lam ** C(i + 1);
      return Math.sqrt(n2);
    case 4: // RefractiveIndex.INFO
      n2 = C(1) + C(2) * lam ** C(3) / (l2 - C(4) ** C(5)) + C(6) * lam ** C(7) / (l2 - C(8) ** C(9));
      for (let i = 10; i < 17; i += 2) if (C(i)) n2 += C(i) * lam ** C(i + 1);
      return Math.sqrt(n2);
    case 5: { // Cauchy
      let n = C(1);
      for (let i = 2; i < 11; i += 2) if (C(i)) n += C(i) * lam ** C(i + 1);
      return n;
    }
    case 6: { // gases
      let n = 1 + C(1);
      for (let i = 2; i < 11; i += 2) if (C(i)) n += C(i) / (C(i + 1) - lam ** -2);
      return n;
    }
    case 7: { // Herzberger
      const d = 1 / (l2 - 0.028);
      return C(1) + C(2) * d + C(3) * d ** 2 + C(4) * l2 + C(5) * l2 ** 2 + C(6) * l2 ** 3;
    }
    case 8: { // Retro: (n²−1)/(n²+2) = …
      const r = C(1) + C(2) * l2 / (l2 - C(3)) + C(4) * l2;
      return Math.sqrt((1 + 2 * r) / (1 - r));
    }
    case 9: // Exotic
      n2 = C(1) + C(2) / (l2 - C(3)) + C(4) * (lam - C(5)) / ((lam - C(5)) ** 2 + C(6));
      return Math.sqrt(n2);
    case 10: // not a refractiveindex.info type: poles with free exponents (Fève et al. 2000)
      n2 = C(1) + C(2) * lam ** C(3) / (lam ** C(3) - C(4)) + C(5) * lam ** C(6) / (lam ** C(6) - C(7));
      return Math.sqrt(n2);
    default:
      return NaN;
  }
}

// Linear interpolation in tabulated [λ, n] points (sorted by λ), as numpy.interp.
export function interpolate(points, lam) {
  let a = 0, b = points.length - 1;
  if (!(b >= 0) || lam < points[0][0] || lam > points[b][0]) return NaN;
  while (b - a > 1) { const m = (a + b) >> 1; if (points[m][0] <= lam) a = m; else b = m; }
  const [x0, y0] = points[a], [x1, y1] = points[b];
  return x1 === x0 ? y0 : y0 + (y1 - y0) * (lam - x0) / (x1 - x0);
}

// n(λ) of an entry (formula, or tabulated points when type is "tab"); NaN outside its wavelength
// range, as EntryData.refractive_index does.
export function entryIndex(entry, lam) {
  const [lo, hi] = entry.range_um;
  if (!(lam >= lo - 1e-9 && lam <= hi + 1e-9)) return NaN;
  return entry.type === "tab" ? interpolate(entry.points, lam) : refractiveIndex(entry.type, entry.coefficients, lam);
}

// Change of a principal index with temperature, from a thermo_optic.yml block (data/rag-optics/):
// n(λ, T) = n(λ, t0) + thermoShift(...). "kato": dn/dT = Σ c·λ^p × 10⁻⁵ /°C, constant in T (the
// piece covering λ, else the nearest); "ghosh": 2n·dn/dT = G(T)·R + H(T)·R², R = λ²/(λ² − λig²),
// G and H in 10⁻⁶ /°C, polynomials in T (°C) integrated from t0 (Ghosh 1995).
// "gayer": the Sellmeier equation of Gayer et al. (2008) and Dolev et al. (2009), whose coefficients
// carry f = (T − t0)(T + t0 + 546.32) (Hobden & Warner's form; Edwards & Lawrence (1984) and Abedin & Ito
// (1996) write 546, given as spec.f_c); "sellmeier": n² = A + B/(λ² − C) − D·λ² with each coefficient
// linear in T − t0, spec {c: [A, B, C, D], dc: [dA, dB, dC, dD]} (Zhang et al. 2013, CBO).
export function thermoShift(form, spec, t0, n0, lam, T) {
  if (T === t0 || !Number.isFinite(T)) return 0;
  if (form === "kato") {
    const dist = (p) => Math.max(p.range_um[0] - lam, lam - p.range_um[1], 0);
    const piece = spec.reduce((best, p) => (dist(p) < dist(best) ? p : best));
    const dT = T - t0; // dn/dT may carry a factor (1 + t_coef·ΔT), as for BiBO (Umemura et al. 2007)
    return (dT + (piece.t_coef || 0) * dT * dT / 2) * piece.terms.reduce((s, [c, p]) => s + c * lam ** p, 0) * 1e-5;
  }
  if (form === "ghosh") {
    const integral = (poly) => poly.reduce((s, c, k) => s + c * (T ** (k + 1) - t0 ** (k + 1)) / (k + 1), 0);
    const R = lam * lam / (lam * lam - spec.lig_um ** 2);
    return (R * integral(spec.G) + R * R * integral(spec.H)) * 1e-6 / (2 * n0);
  }
  if (form === "sellmeier") {
    const t = T - t0, [A, B, C, D] = spec.c.map((v, i) => v + (spec.dc[i] || 0) * t), l2 = lam * lam;
    return Math.sqrt(A + B / (l2 - C) - D * l2) - n0;
  }
  if (form === "bhar") { // n² = A + B/(1 − C/λ²) + D/(1 − E/λ²), A..D = m·T + c (T in °C), E constant (Bhar & Ghosh 1979)
    const l2 = lam * lam, n2 = (t) => { const [A, B, C, D] = spec.c.map((c, i) => c + spec.m[i] * t); return A + B / (1 - C / l2) + D / (1 - spec.E / l2); };
    return Math.sqrt(n2(T)) - Math.sqrt(n2(t0));
  }
  if (form === "gayer") {
    const f = (T - t0) * (T + t0 + (spec.f_c ?? 546.32));
    const { a, b } = spec;
    const l2 = lam * lam;
    const p1 = (a[1] + (b[1] || 0) * f) / (l2 - (a[2] + (b[2] || 0) * f) ** 2);
    const p2 = (a[3] + (b[3] || 0) * f) / (l2 - (a[4] + (b[4] || 0) * f) ** 2);
    const n2 = a[0] + (b[0] || 0) * f + p1 + p2 - (a[5] || 0) * l2;
    return Math.sqrt(n2) - n0;
  }
  return NaN;
}
