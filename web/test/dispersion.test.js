// The site's n(λ) must equal the Python formula engine's for every refractiveindex.info entry.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { refractiveIndex } from "../src/dispersion.client.js";

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
