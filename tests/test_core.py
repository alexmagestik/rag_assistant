"""
Unit tests for core modules (chunker, cache, memory).
Run with: pytest tests/test_core.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.ingestion.chunker import chunk_text, ChunkingConfig
from app.memory.memory import ConversationMemory
from app.utils.cache import EmbeddingCache


# ──────────────────────────────────────────────────────────────
# Chunker
# ──────────────────────────────────────────────────────────────

class TestChunker:
    cfg = ChunkingConfig(min_chunk_size=10, max_chunk_size=100, overlap=10)

    def test_basic_chunking(self):
        text = "Первый абзац.\n\nВторой абзац.\n\nТретий абзац."
        chunks = chunk_text(text, source="test.txt", cfg=self.cfg)
        assert len(chunks) >= 1
        for c in chunks:
            assert c.source == "test.txt"
            assert c.chunk_id
            assert len(c.text) >= self.cfg.min_chunk_size or len(c.text) > 0

    def test_long_paragraph_splits(self):
        long_para = "Это предложение. " * 50  # ~850 chars
        chunks = chunk_text(long_para, source="long.txt", cfg=self.cfg)
        for c in chunks:
            assert len(c.text) <= self.cfg.max_chunk_size + self.cfg.overlap + 50

    def test_positions_are_sequential(self):
        text = "\n\n".join([f"Абзац номер {i}." * 5 for i in range(10)])
        chunks = chunk_text(text, source="seq.txt", cfg=self.cfg)
        positions = [c.position for c in chunks]
        assert positions == list(range(len(chunks)))

    def test_empty_text_returns_no_chunks(self):
        chunks = chunk_text("", source="empty.txt", cfg=self.cfg)
        assert chunks == []


# ──────────────────────────────────────────────────────────────
# EmbeddingCache
# ──────────────────────────────────────────────────────────────

class TestEmbeddingCache:
    def _vec(self, val: float, dim: int = 8) -> list:
        return [val] * dim

    def test_set_and_get_exact(self):
        cache = EmbeddingCache(max_size=10, similarity_threshold=0.99)
        emb = self._vec(0.5)
        cache.set("hello", emb)
        assert cache.get("hello") == emb

    def test_lru_eviction(self):
        cache = EmbeddingCache(max_size=3, similarity_threshold=0.99)
        for i in range(4):
            cache.set(f"key{i}", self._vec(float(i)))
        # key0 should have been evicted
        assert cache.get("key0") is None
        assert cache.get("key3") is not None

    def test_similar_vector_reuse(self):
        cache = EmbeddingCache(max_size=10, similarity_threshold=0.99)
        emb = self._vec(1.0)
        cache.set("original", emb)
        # A nearly identical vector
        almost_same = [1.0 + 1e-10] * 8
        similar = cache.find_similar(almost_same)
        assert similar is not None

    def test_dissimilar_vector_not_reused(self):
        cache = EmbeddingCache(max_size=10, similarity_threshold=0.99)
        cache.set("a", self._vec(1.0))
        orthogonal = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        different = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        result = cache.find_similar(different)
        assert result is None

    def test_clear(self):
        cache = EmbeddingCache(max_size=10, similarity_threshold=0.99)
        cache.set("x", self._vec(0.1))
        cache.clear()
        assert len(cache) == 0


# ──────────────────────────────────────────────────────────────
# ConversationMemory
# ──────────────────────────────────────────────────────────────

class TestMemory:
    def test_add_and_get(self):
        mem = ConversationMemory(max_history=5)
        mem.add("Вопрос 1", "Ответ 1")
        history = mem.get()
        assert len(history) == 1
        assert history[0]["user"] == "Вопрос 1"
        assert history[0]["assistant"] == "Ответ 1"

    def test_max_history_eviction(self):
        mem = ConversationMemory(max_history=3)
        for i in range(5):
            mem.add(f"Q{i}", f"A{i}")
        history = mem.get()
        assert len(history) == 3
        assert history[0]["user"] == "Q2"

    def test_clear(self):
        mem = ConversationMemory(max_history=5)
        mem.add("Q", "A")
        mem.clear()
        assert mem.get() == []
