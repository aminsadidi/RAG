// procs.json (web/scripts/process_map.mjs): which crystals the phase-matching tab offers for each process. It must
// cover every crystal of aniso.json and agree with the phase-matching code on well-known cases.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (f) => JSON.parse(readFileSync(new URL(`../public/ri/${f}`, import.meta.url)));
const P = read("procs.json"), A = read("aniso.json");

test("every crystal has an entry for every process", () => {
  for (const c of A) {
    assert.ok(P[c.material], c.material);
    for (const p of ["shg", "thg", "sfg", "opo", "spdc"]) assert.ok(P[c.material][p] === 0 || Array.isArray(P[c.material][p]), `${c.material} ${p}`);
  }
});

test("known cases: BBO, LBO and KTP double 1064 nm; PPLN and OP-GaAs do every process their formulas hold", () => {
  const inside = (r, x) => Array.isArray(r) && r[0] <= x && x <= r[1];
  for (const m of ["BaB2O4", "LiB3O5", "KTiOPO4"]) assert.ok(inside(P[m].shg, 1.064), m);
  assert.ok(inside(P.ZnGeP2.shg, 4), "ZGP doubles mid-infrared light");
  assert.ok(Array.isArray(P.LiNbO3.opo) && Array.isArray(P.GaAs.opo), "QPM crystals");
  // a crystal with no birefringence and no QPM form phase-matches nothing
  const cubic = A.find((c) => Array.isArray(c.sources) && c.sources.every((s) => s.isotropic) && !["GaAs", "GaP"].includes(c.material));
  if (cubic) for (const p of ["shg", "opo"]) assert.equal(P[cubic.material][p], 0, cubic.material);
});
