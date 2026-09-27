"""Central configuration.

Every value can be overridden with an environment variable prefixed with
``MATRAG_`` (e.g. ``MATRAG_TOP_K=10``) or in a ``.env`` file. Keeping all
experimental parameters here makes runs reproducible and easy to report.
"""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MATRAG_", env_file=".env", extra="ignore")

    # --- Paths ---
    data_dir: Path = Path("data")
    storage_dir: Path = Path("storage")

    # --- Document conversion (Docling) ---
    # OCR is only needed for scanned PDFs and is slow on CPU.
    do_ocr: bool = False

    # --- Chunking & embeddings ---
    embed_model: str = "BAAI/bge-base-en-v1.5"
    # Recommended query prefix for BGE v1.5 models (empty string disables it).
    embed_query_instruction: str = "Represent this sentence for searching relevant passages: "
    chunk_max_tokens: int = 512

    # --- Vector store ---
    collection_name: str = "papers"

    # --- Retrieval ---
    top_k: int = 8

    # --- LLM (Gemini) ---
    google_api_key: SecretStr | None = None
    llm_model: str = "gemini-3.7-flash"
    # None keeps the model's default; Gemini 3 models may reject a custom temperature.
    llm_temperature: float | None = None
    # Retries with exponential backoff for transient errors (503 "high demand", 429).
    llm_max_retries: int = 6
    # Pause between LLM calls to stay within free-tier rate limits.
    llm_min_interval_s: float = 4.0

    @property
    def raw_pdf_dir(self) -> Path:
        return self.data_dir / "raw_pdfs"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def chroma_dir(self) -> Path:
        return self.storage_dir / "chroma"

    @property
    def docstore_path(self) -> Path:
        return self.storage_dir / "docstore.json"


def get_settings() -> Settings:
    return Settings()
