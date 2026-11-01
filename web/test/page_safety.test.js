// The page's HTML templates must not carry a box's raw text: a shared link (#tab=…&id=value, page.html openShared)
// fills the boxes from the address and presses the tab's button, so a raw value in innerHTML is a script from the link.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../src/page.html", import.meta.url), "utf8");

test("no raw input value is interpolated into a template", () => {
  // templates often span lines (`… + (x ? `…${…}` : …)` after an innerHTML = on an earlier line), so every
  // interpolation is checked, and the few that build a box's own value rather than HTML are listed
  const NOT_HTML = [/^\s*\$\("q"\)\.value = `/, /PM\.svFor/];
  const bad = [];
  html.split("\n").forEach((line, i) => {
    if (NOT_HTML.some((r) => r.test(line))) return;
    for (const m of line.matchAll(/\$\{([^{}]*\$\("[^"]+"\)\.value[^{}]*)\}/g)) {
      // each value read must be made a number (+…, Number(…)), escaped (esc(…)) or only compared with a literal
      const raw = [...m[1].matchAll(/(.{0,7})\$\("[^"]+"\)\.value(\s*===?\s*")?/g)]
        .filter(([, before, cmp]) => !cmp && !/(\+|esc\(|Number\()$/.test(before));
      if (raw.length) bad.push(`${i + 1}: ${m[0]}`);
    }
  });
  assert.deepEqual(bad, []);
});

test("the SPDC lines that echoed σ, CAR and ξ show them escaped as numbers", () => {
  for (const id of ["spapod", "spCarT", "spxp", "spxs"])
    assert.ok(html.includes(`\${esc(+$("${id}").value)}`), id);
});
