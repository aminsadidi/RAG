"""Central configuration.

Every value can be overridden with an environment variable prefixed with
``MATRAG_`` (e.g. ``MATRAG_TOP_K=10``) or in a ``.env`` file. Keeping all
experimental parameters here makes runs reproducible and easy to report.
"""

from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MATRAG_", env_file=".env", extra="ignore")

    # --- Paths ---
    # Each corpus (e.g. "hitran", "optical") has its own papers and database:
    #   data/<corpus>/pdfs, data/<corpus>/processed, storage/<corpus>
    corpus: str = "hitran"
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

    # --- LLM ---
    # "ollama": free local open-source model (development, and a baseline to compare);
    # "gemini": Google's hosted model (limited free quota).
    llm_provider: Literal["ollama", "gemini"] = "ollama"
    # None keeps the model's default; Gemini 3 models may reject a custom temperature.
    llm_temperature: float | None = None

    ollama_model: str = "qwen3:4b-instruct-2507-q4_K_M"
    ollama_base_url: str = "http://localhost:11434"
    # Local models on a laptop CPU are slow; allow long generations.
    ollama_timeout_s: float = 900.0
    ollama_context_window: int = 8192

    google_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.7-flash"
    # Retries with exponential backoff for transient errors (503 "high demand", 429).
    gemini_max_retries: int = 6
    # Pause between Gemini calls to stay within free-tier rate limits.
    gemini_min_interval_s: float = 4.0

    @property
    def llm_name(self) -> str:
        """Provider and model, for recording in results."""
        model = self.gemini_model if self.llm_provider == "gemini" else self.ollama_model
        return f"{self.llm_provider}:{model}"

    @property
    def llm_min_interval_s(self) -> float:
        return self.gemini_min_interval_s if self.llm_provider == "gemini" else 0.0

    @property
    def raw_pdf_dir(self) -> Path:
        return self.data_dir / self.corpus / "pdfs"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / self.corpus / "processed"

    @property
    def chroma_dir(self) -> Path:
        return self.storage_dir / self.corpus / "chroma"

    @property
    def docstore_path(self) -> Path:
        return self.storage_dir / self.corpus / "docstore.json"


def get_settings() -> Settings:
    return Settings()
