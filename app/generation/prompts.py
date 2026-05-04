"""
Prompt templates for the RAG assistant.
"""
from __future__ import annotations

from typing import List

SYSTEM_PROMPT = """Ты — RAG-ассистент компании.

Отвечай ТОЛЬКО на основе предоставленного контекста.
Если в контексте нет ответа — скажи:
"Я не нашёл информации по этому вопросу в базе знаний."

Запрещено:
- додумывать
- использовать внешние знания
- фантазировать

Отвечай кратко, точно и по делу."""


def build_generation_prompt(
    retrieved_chunks: List[str],
    chat_history: List[dict],
    query: str,
) -> str:
    context = "\n\n---\n\n".join(retrieved_chunks) if retrieved_chunks else "(контекст пуст)"

    history_lines = []
    for turn in chat_history:
        history_lines.append(f"Пользователь: {turn['user']}")
        history_lines.append(f"Ассистент: {turn['assistant']}")
    history_str = "\n".join(history_lines) if history_lines else "(нет истории)"

    return (
        f"Контекст:\n{context}\n\n"
        f"История диалога:\n{history_str}\n\n"
        f"Вопрос пользователя:\n{query}\n\n"
        f"Ответ:"
    )


REWRITE_SYSTEM = (
    "Переформулируй вопрос пользователя так, чтобы он был максимально понятен "
    "для поиска в базе знаний. Верни только переформулированный вопрос без пояснений."
)


def build_rewrite_prompt(chat_history: List[dict], query: str) -> str:
    history_lines = []
    for turn in chat_history:
        history_lines.append(f"Пользователь: {turn['user']}")
        history_lines.append(f"Ассистент: {turn['assistant']}")
    history_str = "\n".join(history_lines) if history_lines else "(нет истории)"

    return (
        f"История:\n{history_str}\n\n"
        f"Вопрос:\n{query}\n\n"
        f"Переформулированный запрос:"
    )
