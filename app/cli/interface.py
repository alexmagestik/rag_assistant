"""
Interactive CLI interface for the RAG assistant.

Commands:
  exit   — quit the program
  reload — re-index the knowledge base from scratch
"""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text

from app.generation.generator import generate_answer, rewrite_query
from app.ingestion.pipeline import run_ingestion
from app.memory.memory import ConversationMemory
from app.retrieval.retriever import retrieve
from app.retrieval.vectorstore import get_vectorstore
from app.utils.logger import log_interaction

console = Console()


def _banner() -> None:
    console.print(
        Panel(
            Text("RAG Ассистент", justify="center", style="bold cyan"),
            subtitle="[dim]exit — выход | reload — перезагрузка базы[/dim]",
            border_style="cyan",
        )
    )


def _check_db() -> bool:
    vs = get_vectorstore()
    count = vs.count()
    if count == 0:
        console.print(
            "[yellow]⚠  База знаний пуста. Запускаю индексацию…[/yellow]\n"
        )
        ingested = run_ingestion()
        if ingested == 0:
            console.print(
                "[red]Нет данных для индексации. "
                "Положите .txt файлы в папку data/raw и запустите reload.[/red]"
            )
            return False
    else:
        console.print(f"[dim]База знаний: {count} чанков[/dim]\n")
    return True


def run_cli() -> None:
    _banner()

    if not _check_db():
        return

    memory = ConversationMemory()

    while True:
        try:
            query = Prompt.ask("\n[bold cyan]>[/bold cyan] Введите вопрос").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]До свидания.[/dim]")
            break

        if not query:
            continue

        # ── Built-in commands ──────────────────────────────────────────
        if query.lower() == "exit":
            console.print("[dim]До свидания.[/dim]")
            break

        if query.lower() == "reload":
            console.print(Rule("[yellow]Перезагрузка базы знаний[/yellow]"))
            run_ingestion(force=True)
            memory.clear()
            console.print("[green]База перезагружена, история очищена.[/green]")
            continue

        # ── RAG pipeline ───────────────────────────────────────────────
        with console.status("[dim]Обработка запроса…[/dim]", spinner="dots"):
            # 1. Optionally rewrite query for better retrieval
            history = memory.get()
            search_query = rewrite_query(query, history) if history else query

            # 2. Retrieve relevant chunks
            chunks = retrieve(search_query)

            # 3. Generate answer
            answer = generate_answer(
                query=query,
                retrieved_chunks=chunks,
                chat_history=history,
            )

        # ── Output ─────────────────────────────────────────────────────
        console.print(
            Panel(
                answer,
                title="[bold green]Ответ[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )

        # ── Persist ────────────────────────────────────────────────────
        memory.add(user=query, assistant=answer)
        log_interaction(query=query, answer=answer)
