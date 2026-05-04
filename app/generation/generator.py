"""
LLM generation module.
Wraps OpenAI Chat Completions for answer generation and query rewriting.
"""
from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI

from app.config.settings import get_config
from app.generation.prompts import (
    SYSTEM_PROMPT,
    REWRITE_SYSTEM,
    build_generation_prompt,
    build_rewrite_prompt,
)

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


def generate_answer(
    query: str,
    retrieved_chunks: List[str],
    chat_history: List[dict],
) -> str:
    """Generate an answer grounded strictly in retrieved_chunks."""
    cfg = get_config().llm
    user_content = build_generation_prompt(retrieved_chunks, chat_history, query)

    response = _get_client().chat.completions.create(
        model=cfg.model,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content.strip()


def rewrite_query(query: str, chat_history: List[dict]) -> str:
    """Optionally rewrite the user query for better retrieval."""
    cfg = get_config().llm
    user_content = build_rewrite_prompt(chat_history, query)

    response = _get_client().chat.completions.create(
        model=cfg.model,
        temperature=0.0,
        max_tokens=200,
        messages=[
            {"role": "system", "content": REWRITE_SYSTEM},
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content.strip()
