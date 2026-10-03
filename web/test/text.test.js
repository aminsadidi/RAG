// The web app's query handling must match the Python code (cases.json is generated from it).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const S = JSON.parse(readFileSync(new URL("../src/shared.json", import.meta.url)));
const cases = JSON.parse(readFileSync(new URL("./cases.json", import.meta.url)));
// text.js imports shared.json the way wrangler bundles it; rebuild the functions here from its source.
const src = readFileSync(new URL("../src/text.js", import.meta.url), "utf8")
  .replace(/^import S from .*$/m, "").replace(/^export \{ S as shared \};$/m, "").replace(/^export /gm, "");
const mod = new Function("S", `${src}; return { normalizeFormulas, expandQuery, sourceLabel, contextPack, cleanTranslation };`)(S);

test("formula normalization and query expansion match Python", () => {
  for (const c of cases) {
    assert.equal(mod.normalizeFormulas(c.in), c.norm, c.in);
    assert.equal(mod.expandQuery(c.in), c.expand, c.in);
  }
});

test("source labels and context pack", () => {
  assert.equal(mod.sourceLabel({ citation: "Chen (1989)", source_type: "abstract" }), "Chen (1989), abstract only");
  assert.equal(mod.sourceLabel({ citation: "Chen (1989)", source_type: "full_text_pdf", pages: "3", content_type: "table" }), "Chen (1989), p. 3, table");
  const pack = mod.contextPack("q?", [{ citation: "A", pages: "2", text: "T", reference: "Ref A" }], { corpus: "x" }, "Persian", "q en");
  assert.match(pack, /\[1\] \(A, p\. 2\)\nT/);
  assert.match(pack, /Write the answer in Persian/);
  assert.match(pack, /Papers the sources come from:\n- Ref A\n$/);
  assert.equal(mod.cleanTranslation('"Sellmeier of LBO"\nextra', "x"), "Sellmeier of LBO");
});

test("relevance check: says 'not found' instead of passing off the nearest passages", () => {
  const rel = new Function("S", `${src}; return { queryTerms, relevance };`)(S);
  const bbo = [{ text: "Sellmeier equations of β-BaB 2 O 4 at room temperature", citation: "Eimerl (1987)" }];
  assert.deepEqual(rel.queryTerms("Sellmeier coefficients of beta barium borate").materials, ["BaB2O4"]);
  assert.deepEqual(rel.queryTerms("SHG in KTP and GaAs").materials, ["GaAs", "KTP"]);
  assert.equal(rel.relevance("Sellmeier equation of BBO", bbo, 0.8).verdict, "ok");
  assert.equal(rel.relevance("Sellmeier equation of LiB3O5", bbo, 0.8).verdict, "none");
  assert.deepEqual(rel.relevance("Sellmeier equation of LiB3O5", bbo, 0.8).missingMaterials, ["LiB3O5"]);
  assert.equal(rel.relevance("price of bitcoin", bbo, 0.5).verdict, "none");
  assert.equal(rel.relevance("Sellmeier equations at high pressure", bbo, 0.75).verdict, "weak");
  assert.equal(rel.relevance("quantum entanglement in black holes", bbo, 0.7).verdict, "none");
  assert.equal(rel.relevance("anything", [], 0.9).verdict, "none");
  assert.deepEqual(rel.relevance("Sellmeier equation of unobtainium crystal", bbo, 0.75).missingMaterials, ["unobtainium"]);
  const far = [{ text: "black ink was used. The holes of the semiconductor" }];
  assert.deepEqual(rel.relevance("black holes", far, 0.7).missingWords, ["black holes"]);
  assert.deepEqual(rel.relevance("Sellmeier equations at room temperature", bbo, 0.8).verdict, "ok");
});
