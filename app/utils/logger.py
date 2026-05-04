"""
Logging utility — saves user queries and assistant answers.
Retrieved chunks are NOT logged (per spec).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from app.config.settings import get_config


def _setup_logger() -> logging.Logger:
    cfg = get_config()
    logger = logging.getLogger("rag_assistant")

    if not cfg.logging.enabled or logger.handlers:
        return logger

    log_path: Path = cfg.logging.log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


_logger = _setup_logger()


def log_interaction(query: str, answer: str) -> None:
    """Append a single interaction record to the log file."""
    if not get_config().logging.enabled:
        return
    record = {
        "ts": datetime.utcnow().isoformat(),
        "query": query,
        "answer": answer,
    }
    _logger.info(json.dumps(record, ensure_ascii=False))
