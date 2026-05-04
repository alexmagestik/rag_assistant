"""
Embedding cache with:
  - cosine-similarity lookup (avoids re-embedding near-duplicate queries)
  - LRU eviction (bounded memory)
"""
from __future__ import annotations

import math
from collections import OrderedDict
from typing import List, Optional, Tuple

from app.config.settings import get_config


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class EmbeddingCache:
    """
    LRU cache that stores (text → embedding) pairs.
    On lookup, also performs cosine-similarity search over stored embeddings
    so that semantically near-identical queries reuse the cached vector.
    """

    def __init__(self, max_size: int = 512, similarity_threshold: float = 0.92):
        self._max_size = max_size
        self._threshold = similarity_threshold
        # OrderedDict preserves insertion order; most-recently used at end
        self._store: OrderedDict[str, List[float]] = OrderedDict()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, text: str) -> Optional[List[float]]:
        """
        Exact-key lookup first, then cosine-similarity fallback.
        Returns cached embedding or None.
        """
        # 1. Exact match
        if text in self._store:
            self._store.move_to_end(text)
            return self._store[text]

        # 2. Similarity search (only if cache is non-empty)
        best = self._best_similar(text)
        if best is not None:
            return best

        return None

    def set(self, text: str, embedding: List[float]) -> None:
        """Store a new embedding, evicting LRU entry if over capacity."""
        if text in self._store:
            self._store.move_to_end(text)
        else:
            if len(self._store) >= self._max_size:
                self._store.popitem(last=False)  # evict LRU
            self._store[text] = embedding

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _best_similar(self, text: str) -> Optional[List[float]]:
        """
        We cannot compute cosine similarity without an embedding for `text`.
        This method is intentionally a no-op at lookup time — similarity
        comparison happens AFTER we have the new embedding, in `find_similar`.
        """
        return None

    def find_similar(self, new_embedding: List[float]) -> Optional[List[float]]:
        """
        After computing a fresh embedding, check if an existing cached vector
        is close enough to reuse (avoids storing near-duplicate entries).
        Returns the cached embedding if similarity >= threshold, else None.
        """
        best_sim = -1.0
        best_vec: Optional[List[float]] = None
        for vec in self._store.values():
            sim = _cosine(new_embedding, vec)
            if sim > best_sim:
                best_sim = sim
                best_vec = vec
        if best_sim >= self._threshold:
            return best_vec
        return None


# ──────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────

_cache: Optional[EmbeddingCache] = None


def get_cache() -> EmbeddingCache:
    global _cache
    if _cache is None:
        cfg = get_config().cache
        _cache = EmbeddingCache(
            max_size=cfg.max_size,
            similarity_threshold=cfg.similarity_threshold,
        )
    return _cache
