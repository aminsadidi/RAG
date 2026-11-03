// The search's crystal filter groups the collection's folders into crystal families. Every folder of the collection must
// fall in exactly one family (none left to "other"), and the server must accept one folder or several.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../src/page.html", import.meta.url), "utf8");
const papers = JSON.parse(readFileSync(new URL("../src/papers.json", import.meta.url), "utf8"));
const folders = [...new Set((Array.isArray(papers) ? papers : Object.values(papers)).map((p) => p.material).filter(Boolean))];
const block = html.match(/const MAT_FAMILIES = (\[[\s\S]*?\n\]);/)[1];
const FAMILIES = new Function(`return ${block}`)();  // [name, examples, folder pattern]

test("every folder of the collection is in exactly one crystal family", () => {
  assert.ok(folders.length > 40);
  for (const f of folders) {
    const hits = FAMILIES.filter(([, , re]) => re.test(f)).map(([name]) => name);
    assert.equal(hits.length, 1, `${f}: ${hits.join(" | ") || "no family"}`);
  }
});

test("the search sends the chosen folders as a list, and the server filters on any of them", () => {
  assert.match(html, /material: \[\.\.\.MATSEL\]/);
  const src = readFileSync(new URL("../src/index.js", import.meta.url), "utf8");
  assert.match(src, /match: \{ any: mats \}/);
});
