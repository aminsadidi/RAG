// The page fills its boxes from a shared link (#tab=spdc&spapod=…): a box's raw value must never be put into HTML.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("no raw input value is interpolated into a template", () => {
  const page = readFileSync(new URL("../src/page.html", import.meta.url), "utf8");
  const raw = [...page.matchAll(/\$\{\$\("[\w-]+"\)\.value\}/g)].map((m) => m[0]);
  // the one allowed: a search query assembled as text (assigned to .value, not HTML)
  const lines = page.split("\n").filter((l) => /\$\{\$\("[\w-]+"\)\.value\}/.test(l) && !/^\s*\$\("q"\)\.value = `/.test(l) && !/PM\.svFor/.test(l));
  assert.deepEqual(lines, [], `raw values in HTML: ${raw.join(", ")}`);
});

test("highlighting marks the raw text, never the entities of the escaped HTML", () => {
  const page = readFileSync(new URL("../src/page.html", import.meta.url), "utf8");
  const esc = new Function(`${page.match(/const esc = .*$/m)[0]}; return esc;`)();
  const highlight = new Function("esc", `${page.match(/function highlight\(text, words\) \{[\s\S]*?\n\}/)[0]}; return highlight;`)(esc);
  assert.equal(highlight('n < 2 & LT "x" <b>', ["LT", "amp", "quot", "39", "lt"]), 'n &lt; 2 &amp; <mark>LT</mark> &quot;x&quot; &lt;b&gt;');
  assert.equal(highlight("<img onerror=1>", ["img"]), "&lt;<mark>img</mark> onerror=1&gt;");
});

test("pdf.js never evaluates font code from a PDF (CVE-2024-4367)", () => {
  const page = readFileSync(new URL("../src/page.html", import.meta.url), "utf8");
  const calls = [...page.matchAll(/getDocument\(\{[^}]*\}/g)].map((m) => m[0]);
  assert.ok(calls.length >= 3);
  for (const c of calls) assert.match(c, /isEvalSupported: false/, c);
});
