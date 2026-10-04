// The phase-matching engine against angles published for these crystals.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { entryIndex } from "../src/dispersion.client.js";
import { eigenIndices, solveAll } from "../src/phasematch.client.js";

const A = JSON.parse(readFileSync(new URL("../public/ri/aniso.json", import.meta.url)));
const source = (mat, label) => A.find((c) => c.material === mat).sources.find((s) => !label || s.label === label);
const nAt = (s) => (s.kind === "uniaxial"
  ? (l) => { const o = entryIndex(s.axes.o, l); return [o, o, entryIndex(s.axes.e, l)]; }
  : (l) => ["x", "y", "z"].map((a) => entryIndex(s.axes[a], l)));
const angle = (mat, label, proc, a, b, plane, type) => {
  const s = source(mat, label);
  return solveAll(nAt(s), s.kind, proc, a, b).find((r) => r.plane === plane && r.type === type)?.angle;
};

test("Fresnel equation: uniaxial limits", () => {
  const [s, f] = eigenIndices([1.66, 1.66, 1.55], [Math.sin(0.5), 0, Math.cos(0.5)]);
  assert.ok(Math.abs(s - 1.66) < 1e-12);
  const ne = 1 / Math.sqrt(Math.cos(0.5) ** 2 / 1.66 ** 2 + Math.sin(0.5) ** 2 / 1.55 ** 2);
  assert.ok(Math.abs(f - ne) < 1e-12);
});

test("published phase-matching angles", () => {
  // CdSiP2, Kato et al. 2011: type-1 SHG of 4.7846 µm at 43.13°, type 2 of 5.2955 µm at 76.47°
  assert.ok(Math.abs(angle("CdSiP2", null, "shg", 4.7846, 0, "xz", "I") - 43.13) < 0.05);
  assert.ok(Math.abs(angle("CdSiP2", null, "shg", 5.2955, 0, "xz", "IIa") - 76.47) < 0.1);
  // GdCOB, Aka et al. 1997: SHG of 1.064 µm, type I, ZX plane θ = 19.68°, XY plane φ = 45.99°
  assert.ok(Math.abs(angle("GdCa4O(BO3)3", null, "shg", 1.064, 0, "xz", "I") - 19.68) < 0.05);
  assert.ok(Math.abs(angle("GdCa4O(BO3)3", null, "shg", 1.064, 0, "xy", "I") - 45.99) < 0.05);
  // BBO, type-I SHG of 1.064 µm: 22.8° (textbook)
  assert.ok(Math.abs(angle("BaB2O4", "Tamosauskas", "shg", 1.064, 0, "xz", "I") - 22.8) < 0.2);
});

test("no phase matching where there is none: SHG to 200 nm in BBO", () => {
  const s = source("BaB2O4", "Tamosauskas");
  assert.equal(solveAll(nAt(s), s.kind, "shg", 0.4, 0).length, 0);
});
