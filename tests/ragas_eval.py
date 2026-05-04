"""
RAGAS evaluation module.

Evaluates the RAG pipeline on a test dataset using three metrics:
  - faithfulness        (answer grounded in context)
  - answer_relevancy    (answer relevant to question)
  - context_precision   (retrieved context is on-point)

Usage:
    python tests/ragas_eval.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import os
from typing import List

from dotenv import load_dotenv
load_dotenv()

from datasets import Dataset
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

# ragas >= 0.2: import classes, not singleton objects
from ragas.metrics import Faithfulness, AnswerRelevancy, LLMContextPrecisionWithReference

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config.settings import get_config
from app.generation.generator import generate_answer
from app.retrieval.retriever import retrieve


def _make_wrappers():
    """Return ragas-compatible LLM and embeddings wrappers."""
    cfg = get_config()
    api_key = os.environ["OPENAI_API_KEY"]

    llm = LangchainLLMWrapper(
        ChatOpenAI(
            model=cfg.llm.model,
            temperature=cfg.llm.temperature,
            openai_api_key=api_key,
        )
    )
    emb = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(
            model=cfg.embedding.model,
            openai_api_key=api_key,
        )
    )
    return llm, emb


# ──────────────────────────────────────────────────────────────
# Test dataset
# ──────────────────────────────────────────────────────────────
TEST_CASES = [
    {
        "question": "Когда работает техподдержка?",
        "ground_truth": "Техническая поддержка работает по рабочим дням с 10 до 18 часов омского времени, кроме выходных и праздничных дней. Поддержка партнеров по срочным вопросам осуществляется круглосуточно.",
    },
    {
        "question": "Максимальное время реакции на обращение?",
        "ground_truth": "Максимальное время реакции на обращение зависит от уровня поддержки. Для некоммерческих клиентов – 24 рабочих часа, для стандартной поддержки партнеров – 5 рабочих часов, для оперативной поддержки партнеров – 3 рабочих часа.",
    },
    {
        "question": "В какое время вы отвечаете?",
        "ground_truth": "Техническая поддержка отвечает в рабочие дни с 10 до 18 часов омского времени.",
    },
    {
        "question": "А как быстро вы отвечаете?",
        "ground_truth": "Максимальное время реакции на обращение зависит от уровня поддержки: для некоммерческих клиентов – 24 рабочих часа, для стандартной поддержки партнеров – 5 рабочих часов, для оперативной поддержки партнеров – 3 рабочих часа.",
    },
    {
        "question": "Возможен ли обратный переход с Тарифов 2.0?",
        "ground_truth": "Я не нашёл информации по этому вопросу в базе знаний.",
    },
]


def build_ragas_dataset(test_cases: List[dict]) -> Dataset:
    rows: dict = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": [],
    }
    for case in test_cases:
        q = case["question"]
        chunks = retrieve(q)
        answer = generate_answer(query=q, retrieved_chunks=chunks, chat_history=[])

        rows["question"].append(q)
        rows["answer"].append(answer)
        rows["contexts"].append(chunks if chunks else [""])
        rows["ground_truth"].append(case["ground_truth"])

    return Dataset.from_dict(rows)


def run_evaluation(output_path: str = "tests/ragas_results.json") -> dict:
    print("Формирование датасета для RAGAS…")
    dataset = build_ragas_dataset(TEST_CASES)

    llm, emb = _make_wrappers()

    # Instantiate metric objects and inject llm/embeddings
    metrics = [
        Faithfulness(llm=llm),
        AnswerRelevancy(llm=llm, embeddings=emb),
        LLMContextPrecisionWithReference(llm=llm),
    ]

    print("Запуск оценки…")
    results = evaluate(
        dataset=dataset,
        metrics=metrics,
    )

    df = results.to_pandas()

    col_map = {
        "faithfulness": "faithfulness",
        "answer_relevancy": "answer_relevancy",
        "llm_context_precision_with_reference": "context_precision",
    }
    scores = {}
    for src_col, label in col_map.items():
        if src_col in df.columns:
            scores[label] = float(df[src_col].mean())

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(
        json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n=== RAGAS результаты ===")
    for metric_name, score in scores.items():
        print(f"  {metric_name}: {score:.4f}")
    print(f"\nРезультаты сохранены в {output_path}")

    return scores


if __name__ == "__main__":
    run_evaluation()
