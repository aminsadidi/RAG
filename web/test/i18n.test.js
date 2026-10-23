// The English page: every Persian text the page shows must come out without Persian after /i18n/en.json, with the
// page's own whole-word rule (page.html, the i18n script), so an edited Persian sentence cannot lose its translation.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../src/page.html", import.meta.url), "utf8");
const page = html.slice(0, html.indexOf('getElementById("langbtn")')); // the translator's own script is not page text
const dict = JSON.parse(readFileSync(new URL("../public/i18n/en.json", import.meta.url)));
const L = JSON.parse(`"${/const L = "([^"]+)"/.exec(html)[1]}"`); // the letters of a word, as the page has them
const esc = (k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const keys = Object.keys(dict).sort((a, b) => b.length - a.length);
const re = new RegExp(`(?<![${L}])(?:${keys.map(esc).join("|")})(?![${L}])`, "g");
const tr = (t) => { for (let i = 0; i < 2; i++) t = t.replace(re, (m) => dict[m]); return t; };
const KEEP = new Set(["فارسی", "English / فارسی"]); // the language button stays Persian on purpose

// the Persian strings of the page's markup and scripts: between tags, in quotes or in template pieces
export function shownStrings() {
  const out = new Set();
  let list = false; // inside the search's Persian word list (FA_MAT), which runs over several lines
  for (const line of page.split("\n")) {
    if (/const FA_MAT = /.test(line)) list = !/};\s*$/.test(line);
    else if (list) { list = !/};\s*$/.test(line); continue; }
    if (/^\s*\/\/|const (FA_MAT|MAT_SKIP) = |FA_MAT\[/.test(line)) continue; // comments, the search's Persian word lists
    const code = line.replace(/\s\/\/ [^"'`]*$/, "");
    for (const m of code.matchAll(/(["'`>}]|^)([^"'`<>{}]*[\u0600-\u06FF][^"'`<>{}]*)(?=["'`<$]|$)/g)) { // a text may start or end a line
      const t = m[2].trim().replace(/&(amp|lt|gt|quot|#39);/g, (e, c) => ({ amp: "&", lt: "<", gt: ">", quot: '"', "#39": "'" })[c]); // as the browser shows it
      if (t && !KEEP.has(t) && !/\breplace\(/.test(t)) out.add(t); // code that only holds Persian punctuation is not page text
    }
  }
  return [...out];
}

// Whole sentences, not words: each text has its own entry, so no English is pieced together word by word. A text
// built around numbers (${...}) has an entry for each of its pieces.
test("every Persian text of the page has its own English entry", () => {
  assert.deepEqual(shownStrings().filter((t) => !(t in dict)), []);
});

test("no English entry is left over from an old wording", () => {
  const shown = new Set(shownStrings());
  assert.deepEqual(keys.filter((k) => !shown.has(k) && !["«", "»"].includes(k)), []);
});
