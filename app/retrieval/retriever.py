"""
Retrieval module — embeds user query and fetches top_k chunks from ChromaDB.
"""
from __future__ import annotations

from typing import List

from app.config.settings import get_config
from app.generation.embedder import embed_single
from app.retrieval.vectorstore import get_vectorstore


def retrieve(query: str, top_k: int | None = None) -> List[str]:
    """
    Embed the query and return top_k most relevant chunk texts.
    """
    cfg = get_config()
    k = top_k if top_k is not None else cfg.retrieval.top_k

    vs = get_vectorstore()
    if vs.count() == 0:
        return []

    embedding = embed_single(query)
    return vs.query(embedding=embedding, top_k=k)
