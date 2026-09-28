"""Compact text for tables, for prompts that need a whole table at once.

Docling's chunk serialization repeats the full column header in every cell
("Coefficients for ... microns - S1 = 1.04834. Coefficients for ... - S2 = ...").
For wide tables with long merged headers this splits one table across many
chunks. Here a table becomes a small Markdown grid; header text shared by all
columns is stated once above it.
"""

import os

from docling_core.types.doc import DoclingDocument, TableItem

from matrag.textfix import clean_text


def _common_prefix(texts: list[str]) -> str:
    prefix = os.path.commonprefix(texts)
    # Cut at a word/separator boundary so no column name is split.
    for sep in (" - ", "; ", ". ", " "):
        if sep in prefix:
            return prefix[: prefix.rfind(sep) + len(sep)]
    return ""


def compact_table(table: TableItem, doc: DoclingDocument) -> str:
    grid = [[clean_text(" ".join(cell.text.split())) for cell in row] for row in table.data.grid]
    if not grid:
        return ""
    header = grid[0]
    shared = _common_prefix([h for h in header if h]) if len([h for h in header if h]) > 1 else ""
    if len(shared) < 15:  # only strip genuinely long repeated headers
        shared = ""
    rows = [[h[len(shared):] if shared and h.startswith(shared) else h for h in header]] + grid[1:]
    # The first column often repeats the same shared text too.
    rows = [[c[len(shared):] if shared and c.startswith(shared) else c for c in row] for row in rows]
    # Rows repeating one text in every column (leftovers of merged headers) become notes.
    notes = [r[0] for r in rows if len({c for c in r if c}) == 1 and sum(bool(c) for c in r) > 1]
    rows = [r for r in rows if not (len({c for c in r if c}) == 1 and sum(bool(c) for c in r) > 1)]
    if not rows:
        return ""
    lines = []
    caption = clean_text(table.caption_text(doc) or "")
    if caption:
        lines.append(caption)
    if shared:
        lines.append(f"(All columns: {shared.rstrip(' -;.')})")
    lines += [f"({note})" for note in notes]
    lines.append("| " + " | ".join(rows[0]) + " |")
    lines.append("|" + "---|" * len(rows[0]))
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)
