"""Offline test fixtures: no network, no model downloads, no API key."""

from pathlib import Path

import pytest
from docling_core.transforms.chunker.tokenizer.base import BaseTokenizer
from llama_index.core import MockEmbedding

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


@pytest.fixture
def embed_model() -> MockEmbedding:
    return MockEmbedding(embed_dim=8)


@pytest.fixture
def tokenizer() -> WhitespaceTokenizer:
    return WhitespaceTokenizer()


@pytest.fixture
def sample_paper() -> Path:
    return FIXTURES / "sample_paper.md"
