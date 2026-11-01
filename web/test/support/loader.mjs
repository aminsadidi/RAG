// Node module hooks that import src/index.js the way wrangler bundles it (wrangler.toml [[rules]]): .html and
// .client.js files as text, .json files as their parsed value. Only for the tests that drive the Worker.
import { readFile } from "node:fs/promises";

export async function load(url, context, next) {
  if (url.startsWith("file:") && (url.endsWith(".html") || url.endsWith(".client.js")) && context.importAttributes?.type !== "js") {
    const text = await readFile(new URL(url), "utf8");
    return { format: "module", source: `export default ${JSON.stringify(text)};`, shortCircuit: true };
  }
  if (url.startsWith("file:") && url.endsWith(".json")) {
    const text = await readFile(new URL(url), "utf8");
    return { format: "module", source: `export default ${text};`, shortCircuit: true };
  }
  return next(url, context);
}
