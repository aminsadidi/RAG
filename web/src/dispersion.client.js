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
      n2 = C(1); // a term with C2 or C6 = 0 is absent (its pole 0^0 = 1 would give 0/0 at λ = 1 µm)
      for (const i of [2, 6]) if (C(i)) n2 += C(i) * lam ** C(i + 1) / (l2 - C(i + 2) ** C(i + 3));
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
// linear in T − t0, spec {c: [A, B, C, D], dc: [dA, dB, dC, dD]} (Zhang et al. 2013, CBO); "oscillator":
// the classical-oscillator model of Thomas et al. (1998), spec {t0_k, eps_inf, modes: [[ν, a1, a2, Δε, b1, b2, Γ/ν, c1, c2]]}.
export function thermoShift(form, spec, t0, n0, lam, T) {
  if (T === t0 || !Number.isFinite(T)) return 0;
  if (form === "kato") {
    const dist = (p) => Math.max(p.range_um[0] - lam, lam - p.range_um[1], 0);
    const piece = spec.reduce((best, p) => (dist(p) < dist(best) ? p : best));
    // dn/dT may carry a factor (1 + t_coef·ΔT + t_coef2·ΔT²), as for BiBO (Umemura et al. 2007) and BaTiO3 (Buse et al. 1993)
    const dT = T - t0;
    const sum = (terms) => terms.reduce((s, [c, p]) => s + c * lam ** p, 0);
    // t_terms: dn/dT also has T·Σ c'·λ^p with T in kelvin, integrated from t0 (Xu et al. 2014, SiC, Eq. 4)
    const K = 273.15, linear = piece.t_terms ? sum(piece.t_terms) * ((T + K) ** 2 - (t0 + K) ** 2) / 2 : 0;
    const f = dT + (piece.t_coef || 0) * dT * dT / 2 + (piece.t_coef2 || 0) * dT ** 3 / 3;
    return (f * sum(piece.terms) + linear) * 1e-5;
  }
  if (form === "oscillator") { // ε = ε∞ + Σ Δεi·νi²/(νi² − ν² + iΓi·ν), νi, Δεi, Γi/νi quadratic in T − T0 (K),
    // ν in cm⁻¹ (Thomas et al. 1998, sapphire, Eqs. 2, 4–6); Δn = Re n(T) − Re n(t0) of that model
    const nu = 1e4 / lam, re = (t) => {
      const d = t - spec.t0_k;
      let er = spec.eps_inf, ei = 0;
      for (const [v0, a1, a2, de0, b1, b2, g0, c1, c2] of spec.modes) {
        const v = v0 + a1 * d + a2 * d * d, de = de0 + b1 * d + b2 * d * d, G = (g0 + c1 * d + c2 * d * d) * v;
        const x = v * v - nu * nu, y = G * nu, s = de * v * v / (x * x + y * y);
        er += s * x; ei -= s * y;
      }
      return Math.sqrt((Math.hypot(er, ei) + er) / 2); // real part of √ε
    };
    return re(T + 273.15) - re(t0 + 273.15);
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
    const l2 = lam * lam, k = spec.kelvin ? 273.15 : 0; // Ghosh & Bhar (1982) fit in kelvin
    const n2 = (t) => { const [A, B, C, D] = spec.c.map((c, i) => c + spec.m[i] * (t + k)); return A + B / (1 - C / l2) + D / (1 - spec.E / l2); };
    return Math.sqrt(n2(T)) - Math.sqrt(n2(t0));
  }
  if (form === "mangin") { // β = (1/n)dn/dT = (c0 + c1·T) × 10⁻⁶, T in °C, c_j = [a + b/(λ²−C) + d/(λ²−E) + e/(λ²−E)²]/(2n0²),
    // n(T) = n0·exp(∫β dT) from t0 (Mangin et al. 2009, Eqs. 7–9)
    const l2 = lam * lam, c = (k) => (k[0] + k[1] / (l2 - spec.C) + k[2] / (l2 - spec.E) + k[3] / (l2 - spec.E) ** 2) / (2 * n0 * n0);
    return n0 * Math.expm1((c(spec.c0) * (T - t0) + c(spec.c1) * (T * T - t0 * t0) / 2) * 1e-6);
  }
  if (form === "skauli") { // n² = g0 + Σ gi/(λi⁻² − λ⁻²), each gi, λi a polynomial in T − t0 (Skauli et al. 2003, Eq. 13)
    const poly = (c, d) => c.reduce((s, v, k) => s + v * d ** k, 0);
    const n2 = (d) => poly(spec.g[0], d) + [1, 2, 3].reduce((s, i) => s + poly(spec.g[i], d) / (poly(spec.lam[i - 1], d) ** -2 - lam ** -2), 0);
    return Math.sqrt(n2(T - t0)) - Math.sqrt(n2(0));
  }
  if (form === "pomeroy") { // n² = a0 + a1T² + (b0 + b1T²)/(λ² − (c0 + c1T² + c2T⁴)) − dλ², T in K (Pomeroy 1971, BSN)
    const l2 = lam * lam, n2 = (t) => { const K = t + 273.15, K2 = K * K, [a0, a1, b0, b1, c0, c1, c2, d] = spec.c;
      return a0 + a1 * K2 + (b0 + b1 * K2) / (l2 - (c0 + c1 * K2 + c2 * K2 * K2)) - d * l2; };
    return Math.sqrt(n2(T)) - Math.sqrt(n2(t0));
  }
  if (form === "wei") { // n² = A(T) + B(T)/(λ² − C) + D(T)/(λ² − E), A, B, D quadratic in T (K) (Wei et al. 2018, GaP)
    const q = (c, t) => c[0] + c[1] * t + c[2] * t * t, l2 = lam * lam;
    const n2 = (t) => q(spec.A, t) + q(spec.B, t) / (l2 - spec.C) + q(spec.D, t) / (l2 - spec.E);
    return Math.sqrt(n2(T + 273.15)) - Math.sqrt(n2(t0 + 273.15));
  }
  if (form === "rams") { // n² = A + B/(λ0(T)⁻² − λ⁻²) + (c0 + c1·T)λ², λ0 = p0 + p1·T + p2·T², λ and λ0 in nm, T in °C
    // (Rams, Tejeda, Cabrera 1997, rutile, Eqs. 1–2)
    const l = lam * 1000, n2 = (t) => { const l0 = spec.lam0[0] + spec.lam0[1] * t + spec.lam0[2] * t * t;
      return spec.A + spec.B / (l0 ** -2 - l ** -2) + (spec.c[0] + spec.c[1] * t) * l * l; };
    return Math.sqrt(n2(T)) - Math.sqrt(n2(t0));
  }
  if (form === "uchida") { // single-oscillator model: (1/n)(dn/dT)·n²/(n² − 1) = −Δ·λ²/(λ² − λ1²) + Ω/2, constant in T
    // (Uchida 1971, TeO2, Eq. 13 and Table V)
    return (n0 * n0 - 1) / n0 * (-spec.delta * lam * lam / (lam * lam - spec.lam1 ** 2) + spec.omega / 2) * (T - t0);
  }
  if (form === "phillips") { // dn/dT = −c·(n² + a·n + b), constant in T (Phillips 1966, Eqs. 7–9, KDP)
    return -spec.c * (n0 * n0 + spec.a * n0 + spec.b) * (T - t0);
  }
  if (form === "emanueli") { // Δn = n1·ΔT + n2·ΔT², n1, n2 = Σ a_m/λ^m (10⁻⁶ and 10⁻⁸); the z axis of KTA adds
    // B(λ − λ0)/(1 + exp(−γ(λ − λ0))) to both (B1 in 10⁻⁶, B2 in 10⁻⁹) (Emanueli & Arie 2003, Eqs. 2–4)
    const poly = (a) => a.reduce((s, c, m) => s + c / lam ** m, 0), d = T - t0, k = spec.corr;
    const corr = k ? (lam - k.lam0) / (1 + Math.exp(-k.gamma * (lam - k.lam0))) : 0;
    return (poly(spec.n1) + (k ? k.B1 * corr : 0)) * 1e-6 * d + (poly(spec.n2) * 1e-8 + (k ? k.B2 * corr * 1e-9 : 0)) * d * d;
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
