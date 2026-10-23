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
  for (const line of page.split("\n")) {
    if (/^\s*\/\/|const (FA_MAT|MAT_SKIP) = |FA_MAT\[/.test(line)) continue; // comments, the search's Persian word lists
    const code = line.replace(/\s\/\/ [^"'`]*$/, "");
    for (const m of code.matchAll(/(["'`>}])([^"'`<>{}]*[؀-ۿ][^"'`<>{}]*)(?=["'`<$])/g)) {
      const t = m[2].trim().replace(/&(amp|lt|gt|quot|#39);/g, (e, c) => ({ amp: "&", lt: "<", gt: ">", quot: '"', "#39": "'" })[c]); // as the browser shows it
      if (t && !KEEP.has(t) && !/^, [\u0600-\u06FF\u200c]+:$/.test(t)) out.add(t); // ", باریوم:" is FA_MAT going on
    }
  }
  return [...out];
}

test("every Persian text of the page has an English translation", () => {
  const left = shownStrings().filter((t) => /[؀-ۿ]/.test(tr(t)));
  assert.deepEqual(left.map((t) => `${t}  =>  ${tr(t)}`), []);
});
