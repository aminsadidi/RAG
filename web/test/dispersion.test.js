// The site's n(λ) must equal the Python formula engine's for every refractiveindex.info entry.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { entryIndex, interpolate, refractiveIndex } from "../src/dispersion.client.js";

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

test("type 10 (Fève et al. 2000): KTA nz(1.064 µm) = 1.8679, the paper's reference value", () => {
  const n = refractiveIndex(10, [2.1931, 1.2382, 1.8920, 0.059171, 0.5088, 2.0000, 53.2898], 1.064);
  assert.ok(Math.abs(n - 1.8679) < 1e-4, String(n));
});

test("formulas read from papers: the site computes what the Python tests checked", () => {
  // web/public/ri: entries of the "papers" shelf (data/rag-optics/paper_formulas.yml)
  const index = JSON.parse(readFileSync(new URL("../public/ri/index.json", import.meta.url)));
  const papers = index.filter((m) => m.shelf === "papers");
  assert.ok(papers.length >= 12);
  const kbbf = JSON.parse(readFileSync(new URL(`../public/ri/m/${papers.find((m) => m.material === "KBe2BO3F2").i}.json`, import.meta.url)));
  const no = kbbf.find((e) => e.direction === "o" && e.type !== "tab");
  assert.ok(Math.abs(refractiveIndex(no.type, no.coefficients, 0.4047) - 1.49148) < 2e-5); // Chen et al. 2009, Table 2
});

test("type 4 with one pole is finite at 1 µm (the unused term is not 0/(λ² − 0⁰))", () => {
  const n = refractiveIndex(4, [4.104676, 0.410385, 0, 0.532, 2], 1.0); // DSTMS n1, Mutter et al. 2007
  assert.ok(Math.abs(n - Math.sqrt(4.104676 + 0.410385 / (1 - 0.532 ** 2))) < 1e-12);
});

test("GaN: Sanford et al. (2003) is the first source and is positive uniaxial at 1.064 µm", () => {
  const A = JSON.parse(readFileSync(new URL("../public/ri/aniso.json", import.meta.url)));
  const src = A.find((c) => c.material === "GaN").sources[0];
  assert.equal(src.label, "Sanford-2003");
  const no = entryIndex(src.axes.o, 1.064), ne = entryIndex(src.axes.e, 1.064);
  assert.ok(ne > no, `ne ${ne} > no ${no}`);
  // the indices another paper of the same group fitted its Maker fringes with (Sanford et al. 2005, Table I, MOCVD GaN)
  assert.ok(Math.abs(no - 2.3040) < 3e-3, `no ${no}`);
  assert.ok(Math.abs(ne - 2.3373) < 3e-3, `ne ${ne}`);
  assert.ok(Math.abs(entryIndex(src.axes.o, 0.532) - 2.3970) < 5e-3);
  assert.ok(Math.abs(entryIndex(src.axes.e, 0.532) - 2.4350) < 5e-3);
});
