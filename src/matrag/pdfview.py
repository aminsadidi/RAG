"""Page images with the source of an answer highlighted.

The page is rendered with pypdfium2 and the chunk's boxes (stored at ingest
as fractions of the page, see ``ingest.chunk_boxes``) are drawn on it, so a
reader can check a value against the original paper at a glance.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw

# Semi-transparent highlight plus a solid outline (the orange of the app's palette).
_FILL = (235, 104, 52, 60)
_OUTLINE = (235, 104, 52, 255)


def source_pages(metadata: dict) -> list[int]:
    """Pages holding the chunk, in order."""
    return sorted({int(b[0]) for b in json.loads(metadata.get("boxes") or "[]")}) or [
        int(p) for p in str(metadata.get("pages", "")).split(",") if p.strip().isdigit()]


def render_highlight(pdf_path: Path, metadata: dict, page: int | None = None, scale: float = 1.6) -> Image.Image:
    """The page (default: first page of the chunk) with the chunk's boxes highlighted."""
    import pypdfium2

    boxes = [b for b in json.loads(metadata.get("boxes") or "[]")]
    pages = source_pages(metadata)
    if not pages:
        raise ValueError("The chunk has no page information.")
    page = page or pages[0]
    pdf = pypdfium2.PdfDocument(str(pdf_path))
    try:
        image = pdf[page - 1].render(scale=scale).to_pil().convert("RGBA")
    finally:
        pdf.close()
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = image.size
    pad = 3
    for p, x0, y0, x1, y1 in boxes:
        if int(p) == page:
            draw.rectangle([x0 * w - pad, y0 * h - pad, x1 * w + pad, y1 * h + pad],
                           fill=_FILL, outline=_OUTLINE, width=3)
    return Image.alpha_composite(image, overlay).convert("RGB")
