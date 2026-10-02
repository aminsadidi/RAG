// The site's n(λ) must equal the Python formula engine's for every refractiveindex.info entry.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { interpolate, refractiveIndex } from "../src/dispersion.client.js";

const cases = JSON.parse(readFileSync(new URL("./dispersion_cases.json", import.meta.url)));

test("n(λ) matches Python for all formula entries", () => {
  let checked = 0;
  for (const k of cases) {
    const n = refractiveIndex(k.t, k.c, k.lam);
    if (k.n === null) { assert.ok(!Number.isFinite(n), JSON.stringify(k)); continue; }
    assert.ok(Math.abs(n - k.n) < 1e-9, `type ${k.t} at ${k.lam}: ${n} vs ${k.n}`);
    checked++;
  }
  assert.ok(checked > 1000);
});

test("tabulated points are interpolated linearly, NaN outside", () => {
  const pts = [[0.5, 1.5], [1.0, 1.45], [2.0, 1.40]];
  assert.equal(interpolate(pts, 0.75), 1.475);
  assert.equal(interpolate(pts, 2.0), 1.40);
  assert.ok(Number.isNaN(interpolate(pts, 2.1)));
});

test("standard Sellmeier entered by hand (B, C pairs) = refractiveindex.info type 2 with C1 = 0", () => {
  // Malitson (1965), fused silica: n_D = 1.4584 at the sodium D line
  const n = refractiveIndex(2, [0, 0.6961663, 0.0046791, 0.4079426, 0.0135121, 0.8974794, 97.934], 0.5893);
  assert.ok(Math.abs(n - 1.4584) < 1e-4, String(n));
  // Cauchy n = A + B/λ² + C/λ⁴ = type 5 with powers −2, −4
  assert.ok(Math.abs(refractiveIndex(5, [1.5, 0.004, -2, 0.0001, -4], 0.5) - (1.5 + 0.004 / 0.25 + 0.0001 / 0.0625)) < 1e-12);
});
