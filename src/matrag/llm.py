"""The language model (Gemini through LlamaIndex).

Going through LlamaIndex's LLM interface keeps the rest of the code
provider-independent, so other models can be swapped in for comparison.
"""

import time

from llama_index.core.llms import LLM

from matrag.config import Settings


def make_llm(settings: Settings) -> LLM:
    from llama_index.llms.google_genai import GoogleGenAI

    if settings.google_api_key is None:
        raise RuntimeError("No Gemini API key: set MATRAG_GOOGLE_API_KEY in the .env file.")
    return GoogleGenAI(
        model=settings.llm_model,
        api_key=settings.google_api_key.get_secret_value(),
        temperature=settings.llm_temperature,
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
