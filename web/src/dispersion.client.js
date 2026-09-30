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
    default:
      return NaN;
  }
}

// NaN outside the entry's wavelength range, as EntryData.refractive_index does.
export function entryIndex(entry, lam) {
  const [lo, hi] = entry.range_um;
  return lam >= lo - 1e-9 && lam <= hi + 1e-9 ? refractiveIndex(entry.type, entry.coefficients, lam) : NaN;
}
