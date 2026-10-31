// The validation table of the site: every case computes, and the ones the site shows as agreeing do agree.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { entryIndex, thermoShift, refractiveIndex } from "../src/dispersion.client.js";
import { effectiveD, ncpmTemperatures, solveAll, solveMixing } from "../src/phasematch.client.js";
import { jointSpectrum, pairRate, purity } from "../src/spdc.client.js";
import { runValidation } from "../src/validation.client.js";

const A = JSON.parse(readFileSync(new URL("../public/ri/aniso.json", import.meta.url)));
const D = JSON.parse(readFileSync(new URL("../public/ri/dij.json", import.meta.url)));

test("validation cases: all computed; all within tolerance but the known limits", () => {
  const rows = runValidation({ A, D, entryIndex, thermoShift, refractiveIndex, solveAll, effectiveD, ncpmTemperatures, solveMixing, pairRate, jointSpectrum, purity });
  for (const r of rows) console.log(`${r.ok ? "ok " : "OFF"} ${r.crystal} ${r.what}: ${r.value} vs ${r.ref}`);
  assert.ok(rows.length >= 15);
  for (const r of rows) assert.ok(Number.isFinite(r.value), `${r.crystal} ${r.what}: not computed`);
  // a case outside its tolerance must say why (a note), so the table never shows an unexplained miss
  for (const r of rows.filter((x) => !x.ok)) assert.ok(r.note, `${r.crystal} ${r.what}: ${r.value} vs ${r.ref}`);
});
