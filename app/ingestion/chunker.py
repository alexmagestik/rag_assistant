"""
Text chunking:
  1. Split by paragraphs (\\n\\n)
  2. If paragraph > max_chunk_size → split by sentences (NLTK)
  3. Assemble chunks within [min, max] size with overlap
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import List

import nltk

from app.config.settings import ChunkingConfig, get_config

# Download punkt tokeniser on first use (silent)
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)


@dataclass
class Chunk:
    chunk_id: str
    source: str
    text: str
    position: int
    metadata: dict = field(default_factory=dict)


def _split_sentences(text: str) -> List[str]:
    return nltk.sent_tokenize(text, language="russian")


def _build_chunks(
    sentences: List[str],
    cfg: ChunkingConfig,
) -> List[str]:
    """
    Greedily accumulate sentences into chunks respecting min/max sizes,
    then add overlap by prepending the tail of the previous chunk.
    """
    chunks: List[str] = []
    current = ""

    for sent in sentences:
        candidate = (current + " " + sent).strip() if current else sent
        if len(candidate) <= cfg.max_chunk_size:
            current = candidate
        else:
            if len(current) >= cfg.min_chunk_size:
                chunks.append(current)
            current = sent  # start fresh

    if current and len(current) >= cfg.min_chunk_size:
        chunks.append(current)

    # Add overlap: prepend tail of previous chunk
    if cfg.overlap > 0 and len(chunks) > 1:
        overlapped: List[str] = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = chunks[i - 1][-cfg.overlap:]
            overlapped.append((tail + " " + chunks[i]).strip())
        return overlapped

    return chunks


def chunk_text(text: str, source: str, cfg: ChunkingConfig | None = None) -> List[Chunk]:
    if cfg is None:
        cfg = get_config().chunking

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    all_sentences: List[str] = []

    for para in paragraphs:
        if len(para) > cfg.max_chunk_size:
            all_sentences.extend(_split_sentences(para))
        else:
            all_sentences.append(para)

    raw_chunks = _build_chunks(all_sentences, cfg)

    return [
        Chunk(
            chunk_id=str(uuid.uuid4()),
            source=source,
            text=chunk,
            position=idx,
        )
        for idx, chunk in enumerate(raw_chunks)
    ]
