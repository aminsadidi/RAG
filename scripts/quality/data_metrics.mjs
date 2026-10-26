// How much crystal data the site holds and how much of it each tool can use, counted from the exported files
// (web/public/ri): the numbers for a before/after comparison of a data import.
//
//     node scripts/quality/data_metrics.mjs [OUT.json]
import fs from "node:fs";

const dir = new URL("../../web/public/ri/", import.meta.url);
const read = (f) => JSON.parse(fs.readFileSync(new URL(f, dir)));
const aniso = read("aniso.json"), index = read("index.json");
const dij = read("dij.json"), props = read("props.json");
const POLED = new Set(["LiNbO3", "MgO-LiNbO3", "LiTaO3", "Mg-LiTaO3", "KTiOPO4", "RbTiOPO4", "KTiOAsO4", "RbTiOAsO4"]);
const span = (c) => Math.max(...c.sources.map((s) => s.range_um[1] / s.range_um[0])) * 1.21;  // page.html canDo, EXTRA 0.1
const count = (xs, f) => xs.filter(f).length;
const sources = aniso.flatMap((c) => c.sources);
const tier = (s) => s.tier || "untagged";
const nlo = aniso.filter((c) => dij[c.material]);
const m = {
  "refractive-index materials (RI tab)": index.length,
  "refractive-index entries (RI tab)": index.reduce((n, e) => n + (e.n || 0), 0),
  "birefringent crystals with dispersion formulas": aniso.length,
  "dispersion sources (Sellmeier) of these crystals": sources.length,
  "sources with temperature dependence": count(sources, (s) => s.thermo),
  "crystals with temperature dependence": count(aniso, (c) => c.sources.some((s) => s.thermo)),
  "crystals with thermal expansion": count(aniso, (c) => c.sources.some((s) => s.thermo?.expansion)),
  "crystals with d coefficients": Object.keys(dij).length,
  "d-coefficient sources": Object.values(dij).reduce((n, e) => n + (e.sources?.length || 0), 0),
  "crystals with properties (advisor)": Object.keys(props).length,
  "with transparency range": count(Object.values(props), (p) => p.transparency_um),
  "with damage threshold": count(Object.values(props), (p) => p.damage),
  "with hygroscopicity": count(Object.values(props), (p) => p.hygroscopic),
  "with thermal conductivity": count(Object.values(props), (p) => p.thermal_conductivity),
  // the tools
  "phase matching: crystals with d (SFG/DFG/OPO/SPDC)": nlo.length,
  "phase matching: crystals that can do SHG": count(nlo, (c) => span(c) >= 2),
  "phase matching: crystals that can do THG": count(nlo, (c) => span(c) >= 3),
  "phase matching: crystals with temperature tuning / NCPM temperature": count(nlo, (c) => c.sources.some((s) => s.thermo)),
  "QPM: poled crystals with d and temperature dependence": count(nlo, (c) => POLED.has(c.material) && c.sources.some((s) => s.thermo)),
  "solver: crystals that solve for temperature": count(nlo, (c) => c.sources.some((s) => s.thermo)),
  "advisor: crystals ranked (d + properties)": count(nlo, (c) => props[c.material]),
  "advisor: crystals with damage threshold": count(nlo, (c) => props[c.material]?.damage),
  "sources by provenance": Object.fromEntries([...new Set(sources.map(tier))].map((t) => [t, count(sources, (s) => tier(s) === t)])),
};
const out = JSON.stringify(m, null, 1);
if (process.argv[2]) fs.writeFileSync(process.argv[2], out + "\n");
console.log(out);
