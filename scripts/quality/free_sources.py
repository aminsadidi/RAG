"""Free copies of the papers the collection has only as abstracts: an open-access version (OpenAlex: preprints,
repositories, author manuscripts) and the Supporting Information that ACS, Optica and others post on figshare even
when the article itself is paywalled. Writes data/rag-optics/free_sources.csv (doi, kind, url, license, note, title) for the
Colab notebook that downloads them into Drive; only links, no paper text.

    python scripts/quality/free_sources.py [N]
"""
import csv
import json
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def get(url, body=None):
    req = urllib.request.Request(url, json.dumps(body).encode() if body else None,
                                 {"content-type": "application/json", "user-agent": "MatRAG (University of Isfahan)"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except Exception:  # noqa: BLE001 - a lookup that fails only leaves this paper without free links
        return None


def find(doi):
    rows = []
    w = get(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}?select=display_name,locations")
    for loc in (w or {}).get("locations") or []:
        if loc.get("pdf_url") and loc.get("is_oa"):
            src = (loc.get("source") or {}).get("display_name") or ""
            rows.append([doi, "oa_pdf", loc["pdf_url"], loc.get("license") or "", f"{loc.get('version') or ''} {src}".strip(),
                         w.get("display_name") or ""])
            break
    for art in get("https://api.figshare.com/v2/articles/search", {"search_for": f":resource_doi: {doi}", "page_size": 10}) or []:
        if (art.get("resource_doi") or "").lower() != doi.lower():
            continue
        full = get(f"https://api.figshare.com/v2/articles/{art['id']}") or {}
        for f in full.get("files") or []:
            if f["name"].lower().endswith((".pdf", ".docx", ".xlsx", ".csv", ".txt", ".zip")):
                rows.append([doi, "supporting_info", f["download_url"], (full.get("license") or {}).get("name", ""),
                             f"{f['name']} ({f['size'] // 1024} kB)", ""])
    return rows


def main(n=None):
    papers = json.loads((ROOT / "web/src/papers.json").read_text(encoding="utf-8"))
    dois = sorted({p["doi"] for p in papers if p["source_type"] != "full_text_pdf" and p.get("doi")})[:n]
    with ThreadPoolExecutor(8) as ex:
        rows = [r for found in ex.map(find, dois) for r in found]
    out = ROOT / "data/rag-optics/free_sources.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["doi", "kind", "url", "license", "note", "title"], *rows])
    kinds = {k: len({r[0] for r in rows if r[1] == k}) for k in ("oa_pdf", "supporting_info")}
    print(f"{len(dois)} abstract-only papers: {kinds['oa_pdf']} with an open-access PDF, "
          f"{kinds['supporting_info']} with Supporting Information on figshare ({len(rows)} files) -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
