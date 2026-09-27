"""Offline test fixtures: no network, no model downloads, no API key."""

import re
import zlib
from pathlib import Path

import pytest
from docling_core.transforms.chunker.tokenizer.base import BaseTokenizer
from llama_index.core.base.embeddings.base import BaseEmbedding

from matrag.config import Settings

FIXTURES = Path(__file__).parent / "fixtures"


class WhitespaceTokenizer(BaseTokenizer):
    """Stand-in for the embedding model's tokenizer."""

    max_tokens: int = 64

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def get_max_tokens(self) -> int:
        return self.max_tokens

    def get_tokenizer(self):
        return None


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(data_dir=tmp_path / "data", storage_dir=tmp_path / "storage", _env_file=None)


class HashingEmbedding(BaseEmbedding):
    """Deterministic bag-of-words embedding: texts sharing words get similar vectors.

    Unlike a constant mock, it makes vector retrieval meaningful, so ranking
    tests do not depend on arbitrary tie-breaking.
    """

    dim: int = 64

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            vec[zlib.crc32(word.encode()) % self.dim] += 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._vector(text)

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._vector(query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._vector(query)


@pytest.fixture
def embed_model() -> HashingEmbedding:
    return HashingEmbedding()


@pytest.fixture
def tokenizer() -> WhitespaceTokenizer:
    return WhitespaceTokenizer()


@pytest.fixture
def sample_paper() -> Path:
    return FIXTURES / "sample_paper.md"
