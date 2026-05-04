"""
Conversation memory.
Stores the last N user ↔ assistant turns.
Retrieved chunks are intentionally NOT stored here.
"""
from __future__ import annotations

from collections import deque
from typing import List

from app.config.settings import get_config


class ConversationMemory:
    def __init__(self, max_history: int | None = None) -> None:
        if max_history is None:
            max_history = get_config().memory.max_history
        self._max = max_history
        self._history: deque[dict] = deque(maxlen=max_history)

    def add(self, user: str, assistant: str) -> None:
        self._history.append({"user": user, "assistant": assistant})

    def get(self) -> List[dict]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)
