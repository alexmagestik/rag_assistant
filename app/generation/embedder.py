"""
Embedding generation via OpenAI API.
Integrates with EmbeddingCache (LRU + cosine-similarity dedup).
"""
from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI

from app.config.settings import get_config
from app.utils.cache import get_cache

load_dotenv()

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY не задан в .env")
        _client = OpenAI(api_key=api_key)
    return _client


def embed_single(text: str) -> List[float]:
    """
    Embed a single text string.
    Uses LRU cache with cosine-similarity deduplication.
    """
    cache = get_cache()
    cfg = get_config()

    # 1. Exact-key cache hit
    cached = cache.get(text)
    if cached is not None:
        return cached

    # 2. Call API
    response = _get_client().embeddings.create(
        model=cfg.embedding.model,
        input=text,
    )
    new_emb: List[float] = response.data[0].embedding

    # 3. Cosine-similarity dedup: if very similar vector exists, reuse it
    similar = cache.find_similar(new_emb)
    if similar is not None:
        cache.set(text, similar)
        return similar

    cache.set(text, new_emb)
    return new_emb


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Batch embed a list of texts.
    Sends uncached texts to API in a single batch call for efficiency.
    """
    cache = get_cache()
    cfg = get_config()

    results: List[List[float] | None] = [None] * len(texts)
    uncached_indices: List[int] = []
    uncached_texts: List[str] = []

    for i, text in enumerate(texts):
        hit = cache.get(text)
        if hit is not None:
            results[i] = hit
        else:
            uncached_indices.append(i)
            uncached_texts.append(text)

    if uncached_texts:
        response = _get_client().embeddings.create(
            model=cfg.embedding.model,
            input=uncached_texts,
        )
        for j, item in enumerate(response.data):
            emb = item.embedding
            idx = uncached_indices[j]
            similar = cache.find_similar(emb)
            final = similar if similar is not None else emb
            cache.set(uncached_texts[j], final)
            results[idx] = final

    return results  # type: ignore[return-value]
