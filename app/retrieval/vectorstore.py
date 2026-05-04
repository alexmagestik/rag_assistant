"""
ChromaDB vector store wrapper.
Collection: documents
"""
from __future__ import annotations

from typing import List

import chromadb
from chromadb.config import Settings

from app.config.settings import get_config
from app.ingestion.chunker import Chunk

COLLECTION_NAME = "documents"

_vs: "VectorStore | None" = None


class VectorStore:
    def __init__(self) -> None:
        cfg = get_config()
        chroma_dir = str(cfg.paths.chroma_dir)
        self._client = chromadb.PersistentClient(
            path=chroma_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._col = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------

    def upsert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        self._col.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "source": c.source,
                    "position": c.position,
                }
                for c in chunks
            ],
        )

    def query(self, embedding: List[float], top_k: int) -> List[str]:
        """Return top_k most relevant chunk texts."""
        results = self._col.query(
            query_embeddings=[embedding],
            n_results=min(top_k, self._col.count() or 1),
            include=["documents"],
        )
        docs: List[str] = results.get("documents", [[]])[0]
        return docs

    def count(self) -> int:
        return self._col.count()

    def reset(self) -> None:
        """Drop and recreate the collection (used on reload)."""
        self._client.delete_collection(COLLECTION_NAME)
        self._col = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )


def get_vectorstore() -> VectorStore:
    global _vs
    if _vs is None:
        _vs = VectorStore()
    return _vs
