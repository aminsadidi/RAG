import json

from PIL import Image

from matrag.pdfview import render_highlight, source_pages


def test_highlight_drawn_on_the_right_page(tmp_path):
    pdf = tmp_path / "blank.pdf"
    pages = [Image.new("RGB", (600, 800), "white") for _ in range(2)]
    pages[0].save(pdf, save_all=True, append_images=pages[1:])
    meta = {"boxes": json.dumps([[2, 0.1, 0.1, 0.5, 0.2]]), "pages": "2"}
    assert source_pages(meta) == [2]

    image = render_highlight(pdf, meta, scale=1.0)
    w, h = image.size
    inside = image.getpixel((int(0.3 * w), int(0.15 * h)))
    outside = image.getpixel((int(0.8 * w), int(0.8 * h)))
    assert outside == (255, 255, 255) and inside != outside  # tinted only inside the box
    assert render_highlight(pdf, meta, page=1, scale=1.0).getpixel((int(0.3 * w), int(0.15 * h))) == (255, 255, 255)
