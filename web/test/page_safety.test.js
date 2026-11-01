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

// a function of the page's script, by its source (the page is not a module)
const fn = (name) => {
  const start = html.indexOf(`function ${name}(`);
  let depth = 0, i = html.indexOf("{", start);
  for (; i < html.length; i++) { if (html[i] === "{") depth++; else if (html[i] === "}" && --depth === 0) break; }
  return html.slice(start, i + 1);
};
const escSrc = /const esc = .*$/m.exec(html)[0];
const highlight = new Function(`${escSrc}\n${fn("highlight")}; return highlight;`)();

test("highlight marks words of the raw text and never breaks an entity", () => {
  assert.equal(highlight("a <b> & c", ["lt"]), "a &lt;b&gt; &amp; c");
  for (const w of ["lt", "gt", "amp", "quot", "39"]) assert.equal(highlight(`x < y > z & "q" 'r'`, [w]), `x &lt; y &gt; z &amp; &quot;q&quot; &#39;r&#39;`, w);
  assert.equal(highlight("LT of <LiNbO3> & LT", ["LT"]), "<mark>LT</mark> of &lt;LiNbO3&gt; &amp; <mark>LT</mark>");
  assert.equal(highlight("n of β-LiB3O5 and <i>", ["LiB3O5"]), "n of β-<mark>LiB3O5</mark> and &lt;i&gt;");
  assert.equal(highlight("Si and Sintered", ["Si"]), "<mark>Si</mark> and Sintered");
  assert.equal(highlight("a<script>", ["script"]), "a&lt;<mark>script</mark>&gt;");
  assert.equal(highlight("plain", []), "plain");
});

test("the search marks the formulas of the materials the API found (LBO -> LiB3O5)", () => {
  assert.match(html, /\.\.\.\(data\.materials \|\| \[\]\)/);
});

test("every pdf.js getDocument turns eval off (CVE-2024-4367)", () => {
  const calls = html.match(/getDocument\(\{[^}]*\}/g);
  assert.ok(calls.length >= 3);
  for (const c of calls) assert.match(c, /isEvalSupported: false/, c);
});

test("no timer runs forever: the crystal pickers follow their select by its setters, not by polling", () => {
  assert.ok(!/setInterval\(/.test(html));
  assert.match(html, /getOwnPropertyDescriptor\(HTMLSelectElement\.prototype, prop\)/);
});
