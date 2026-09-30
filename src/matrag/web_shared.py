"""Texts and tables the web app (``web/``) must use exactly as the Python code does.

``python -m matrag.web_shared`` writes them to ``web/src/shared.json``; a test
checks that file is up to date, so the site and the evaluations never drift apart.
"""

import json
from pathlib import Path

from matrag import qa, qdrant_store
from matrag.config import Settings

SHARED_JSON = Path(__file__).resolve().parents[2] / "web" / "src" / "shared.json"


def shared() -> dict:
    return {
        "EMBED_MODEL": Settings.model_fields["embed_model"].default,
        "QUERY_INSTRUCTION": Settings.model_fields["embed_query_instruction"].default,
        "NOT_FOUND": qa.NOT_FOUND,
        "RAG_PROMPT": qa.RAG_PROMPT,
        "TRANSLATE_PROMPT": qa.TRANSLATE_PROMPT,
        "PERSIAN_GLOSSARY": qa.PERSIAN_GLOSSARY,
        "SYNONYMS": qdrant_store.SYNONYMS,
        "SPACED_FORMULA": qdrant_store._SPACED_FORMULA.pattern,
        "PAYLOAD_KEYS": list(qdrant_store.PAYLOAD_KEYS),
        "BM25_MODEL": qdrant_store.BM25_MODEL,
        "DENSE": qdrant_store.DENSE,
        "SPARSE": qdrant_store.SPARSE,
    }


def dump() -> str:
    return json.dumps(shared(), ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    SHARED_JSON.write_text(dump(), encoding="utf-8")
    print(f"wrote {SHARED_JSON}")
