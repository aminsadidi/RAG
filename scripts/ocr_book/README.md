# OCR of a book sent in parts (Dmitriev et al. 1999, October 2026)

The 39 MB scan was over the site's 25 MB PDF limit and the Drive connector's 10 MB, so it came in parts of
80 pages, named with their page range (`pNNNNN-MMMMM.pdf`).

1. `ocr_parts.py DIR` — full-page OCR (RapidOCR) of every part into `DIR/units/NNNNN-MMMMM.json.gz`
   (about 5–9 s a page on 4 cores; parts done before are skipped).
2. `publish.py DIR/units` — joins the parts in page order (a missing range becomes empty pages, so page
   numbers stay right), re-chunks and embeds them with the pipeline's chunker and model, and replaces the
   book's full-text points on the site (`ocr: true`). The book is in `data/rag-optics/external_points.txt`,
   so export-qdrant leaves it alone.

Result: 426 pages, 1362 chunks (108 before, from the first 60 pages only).
