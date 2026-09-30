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
