"""
Configuration management using Pydantic + YAML.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# ──────────────────────────────────────────────────────────────
# Sub-models
# ──────────────────────────────────────────────────────────────

class LLMConfig(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tokens: int = 800


class EmbeddingConfig(BaseModel):
    model: str = "text-embedding-3-small"


class RetrievalConfig(BaseModel):
    top_k: int = 5


class ChunkingConfig(BaseModel):
    min_chunk_size: int = 300
    max_chunk_size: int = 1000
    overlap: int = 100


class MemoryConfig(BaseModel):
    max_history: int = 5


class CacheConfig(BaseModel):
    similarity_threshold: float = 0.92
    max_size: int = 512


class PathsConfig(BaseModel):
    data_dir: Path = Path("./data/raw")
    chroma_dir: Path = Path("./chroma_db")


class LoggingConfig(BaseModel):
    enabled: bool = True
    log_file: Path = Path("./logs/assistant.log")


# ──────────────────────────────────────────────────────────────
# Root config
# ──────────────────────────────────────────────────────────────

class AppConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(path: str = "config.yaml") -> AppConfig:
    """Load config from YAML file, falling back to defaults."""
    config_path = Path(path)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return AppConfig.model_validate(raw or {})
    return AppConfig()


# Singleton
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config
