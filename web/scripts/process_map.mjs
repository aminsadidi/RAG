// Which crystals can do each process at all, and where: public/ri/procs.json for the phase-matching tab's crystal menu.
// For every crystal and process the wavelengths of its refractive-index formulas are scanned (at the formula's own
// temperature) and the phase-matching solutions counted: SHG and THG over the fundamental, SFG over pairs of inputs,
// OPO / SPDC over pump and signal. A periodically poled or orientation-patterned crystal with d coefficients does
// every process its formulas hold (quasi-phase matching). Output: {material: {shg: [lo, hi] (µm of the scanned
// wavelength that phase-matches) or 0, ...}}. Run after aniso.json or dij.json change: node web/scripts/process_map.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { solveAll, waves } from "../src/phasematch.client.js";
import { entryIndex } from "../src/dispersion.client.js";

const DIR = new URL("../public/ri/", import.meta.url);
const A = JSON.parse(readFileSync(new URL("aniso.json", DIR))), D = JSON.parse(readFileSync(new URL("dij.json", DIR)));
// the same lists as the page (page.html, POLED and OP)
const QPM = new Set(["LiNbO3", "MgO-LiNbO3", "LiTaO3", "Mg-LiTaO3", "KTiOPO4", "RbTiOPO4", "KTiOAsO4", "RbTiOAsO4", "GaAs", "GaP"]);
const nAt = (s) => {
  const ax = s.axes;
  if (s.kind === "uniaxial") return (l) => { const o = entryIndex(ax.o, l); return [o, o, entryIndex(ax.e, l)]; };
  return (l) => [entryIndex(ax.x, l), entryIndex(ax.y, l), entryIndex(ax.z, l)];
};
const covers = (s, w) => [w.l1, w.l2, w.l3].every((l) => l >= s.range_um[0] - 1e-9 && l <= s.range_um[1] + 1e-9);
const geo = (lo, hi, n) => Array.from({ length: n }, (_, i) => lo * (hi / lo) ** (i / (n - 1)));
// the first wavelength of each case to scan (the fundamental, λ1, or the pump) and the second (λ2 or the signal)
function cases(proc, [lo, hi]) {
  if (proc === "shg") return geo(2 * lo, hi, 40).map((a) => [a]);
  if (proc === "thg") return geo(3 * lo, hi, 40).map((a) => [a]);
  if (proc === "sfg") return geo(lo * 1.5, hi, 10).flatMap((a) => geo(lo * 1.5, hi, 10).map((b) => [a, b]));
  return geo(lo, hi / 2, 12).flatMap((p) => [1.1, 1.3, 1.6, 2, 2.6, 4, 7].map((f) => [p, p * f]).filter(([, s]) => s < hi));
}
const out = {};
for (const c of A) {
  const sources = (Array.isArray(c.sources) ? c.sources : []).filter((s) => !s.isotropic);
  const qpm = QPM.has(c.material) && D[c.material] && !D[c.material].partial;
  const all = Array.isArray(c.sources) ? c.sources : [];
  const row = {};
  for (const proc of ["shg", "thg", "sfg", "opo", "spdc"]) {
    let lo = Infinity, hi = -Infinity;
    for (const s of qpm ? all : sources) for (const [a, b] of cases(proc, s.range_um)) {
      const w = waves(proc, a, b);
      if (!covers(s, w)) continue;
      if (qpm || solveAll(nAt(s), s.kind, proc, a, b).length) { lo = Math.min(lo, a); hi = Math.max(hi, a); }
    }
    row[proc] = lo <= hi ? [+lo.toFixed(3), +hi.toFixed(3)] : 0;
  }
  out[c.material] = row;
}
writeFileSync(new URL("procs.json", DIR), JSON.stringify(out));
const count = (p) => Object.values(out).filter((r) => r[p]).length;
console.log(`${Object.keys(out).length} crystals: ${["shg", "thg", "sfg", "opo", "spdc"].map((p) => `${p} ${count(p)}`).join(", ")}`);
