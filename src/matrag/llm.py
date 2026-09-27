"""The language model.

Two providers behind LlamaIndex's common LLM interface, so the rest of the
code does not change when switching between them:

- Ollama: an open-source model running locally (free, unlimited, slower).
- Gemini: Google's hosted model (stronger, limited free quota).
"""

import time

from llama_index.core.llms import LLM

from matrag.config import Settings


def make_llm(settings: Settings) -> LLM:
    if settings.llm_provider == "ollama":
        from llama_index.llms.ollama import Ollama

        return Ollama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
            request_timeout=settings.ollama_timeout_s,
            context_window=settings.ollama_context_window,
        )

    from llama_index.llms.google_genai import GoogleGenAI

    if settings.google_api_key is None:
        raise RuntimeError("No Gemini API key: set MATRAG_GOOGLE_API_KEY.")
    return GoogleGenAI(
        model=settings.gemini_model,
        api_key=settings.google_api_key.get_secret_value(),
        temperature=settings.llm_temperature,
        max_retries=settings.gemini_max_retries,
    )


class Throttle:
    """Keeps a minimum delay between consecutive LLM calls (free-tier rate limits)."""

    def __init__(self, min_interval_s: float):
        self.min_interval_s = min_interval_s
        self._last = 0.0

    def wait(self) -> None:
        delay = self._last + self.min_interval_s - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        self._last = time.monotonic()
