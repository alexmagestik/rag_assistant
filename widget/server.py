"""
HTTP API and static assets for the embeddable chat widget.

Run from the project root:

    pip install -r widget/requirements.txt
    uvicorn widget.server:app --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

from app.generation.generator import generate_answer, rewrite_query
from app.ingestion.pipeline import run_ingestion
from app.memory.memory import ConversationMemory
from app.retrieval.retriever import retrieve
from app.retrieval.vectorstore import get_vectorstore
from app.utils.logger import log_interaction

STATIC_DIR = Path(__file__).parent / "static"
_sessions: Dict[str, ConversationMemory] = {}

app = FastAPI(title="RAG Assistant Widget API", version="1.0.0")

_cors_origins = os.getenv("WIDGET_CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _cors_origins == "*" else [o.strip() for o in _cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str


class HealthResponse(BaseModel):
    status: str
    chunks: int


def _ensure_vectorstore() -> None:
    vs = get_vectorstore()
    if vs.count() == 0:
        ingested = run_ingestion()
        if ingested == 0:
            raise RuntimeError(
                "База знаний пуста. Добавьте .txt файлы в data/raw и перезапустите сервер."
            )


def _get_memory(session_id: str) -> ConversationMemory:
    if session_id not in _sessions:
        _sessions[session_id] = ConversationMemory()
    return _sessions[session_id]


@app.on_event("startup")
def on_startup() -> None:
    _ensure_vectorstore()


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", chunks=get_vectorstore().count())


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    query = body.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым.")

    session_id = body.session_id or str(uuid.uuid4())
    memory = _get_memory(session_id)

    try:
        history = memory.get()
        search_query = rewrite_query(query, history) if history else query
        chunks = retrieve(search_query)
        answer = generate_answer(
            query=query,
            retrieved_chunks=chunks,
            chat_history=history,
        )
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Не удалось обработать запрос. Попробуйте позже.",
        ) from exc

    memory.add(user=query, assistant=answer)
    log_interaction(query=query, answer=answer)

    return ChatResponse(answer=answer, session_id=session_id)


@app.get("/")
def demo_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "demo.html")


app.mount("/widget", StaticFiles(directory=STATIC_DIR), name="widget")
