"""
Ingestion pipeline:
  load files → chunk → embed → upsert into ChromaDB
"""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.progress import track

from app.config.settings import get_config
from app.ingestion.chunker import Chunk, chunk_text
from app.ingestion.loader import load_txt_files
from app.retrieval.vectorstore import get_vectorstore
from app.generation.embedder import embed_texts

console = Console()


def run_ingestion(force: bool = False) -> int:
    """
    Load all .txt files, chunk, embed, and store in ChromaDB.
    Returns the number of chunks ingested.
    """
    cfg = get_config()
    data_dir = cfg.paths.data_dir

    if not data_dir.exists():
        console.print(f"[yellow]⚠ Data directory not found: {data_dir}[/yellow]")
        return 0

    vs = get_vectorstore()

    if force:
        vs.reset()
        console.print("[yellow]База знаний очищена.[/yellow]")

    all_chunks: List[Chunk] = []
    files_loaded = 0

    for filename, text in load_txt_files(data_dir):
        chunks = chunk_text(text, source=filename)
        all_chunks.extend(chunks)
        files_loaded += 1
        console.print(f"  [dim]Загружен:[/dim] {filename} → {len(chunks)} чанков")

    if not all_chunks:
        console.print("[yellow]Нет данных для индексации.[/yellow]")
        return 0

    console.print(f"\nВсего чанков: [bold]{len(all_chunks)}[/bold]. Начинаю эмбеддинг…")

    texts = [c.text for c in all_chunks]
    embeddings = embed_texts(texts)

    vs.upsert(chunks=all_chunks, embeddings=embeddings)

    console.print(
        f"[green]✓ Индексация завершена:[/green] {files_loaded} файлов, {len(all_chunks)} чанков."
    )
    return len(all_chunks)
