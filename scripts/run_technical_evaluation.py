from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.backend.config import settings
from src.backend.rag.generator import (
    generate_source_grounded_answer,
    generated_answer_to_dict,
)


DEFAULT_TEST_SET_PATH = Path("data/evaluation/test_questions.json")
DEFAULT_RAW_RESULTS_PATH = Path(
    "data/evaluation/technical_evaluation_raw.json"
)
DEFAULT_SCORING_PATH = Path(
    "data/evaluation/technical_evaluation_scores.csv"
)


def load_test_questions(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Test question file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if not data.get("questions"):
        raise ValueError("The evaluation test set contains no questions.")

    return data


def extract_citation_markers(answer: str) -> list[str]:
    markers = re.findall(r"\[S\d+\]", answer or "")

    return list(dict.fromkeys(markers))


def format_sources(sources: list[dict[str, Any]]) -> str:
    formatted_sources = []

    for source in sources:
        source_id = source.get("source_id", "")
        source_name = source.get("source", "")
        similarity = source.get("similarity_score", "")

        formatted_sources.append(
            f"{source_id}:{source_name}:{similarity}"
        )

    return " | ".join(formatted_sources)


def create_scoring_row(result: dict[str, Any]) -> dict[str, Any]:
    question = result["question_data"]
    generated = result["generated_result"]

    citation_markers = extract_citation_markers(
        generated.get("answer", "")
    )

    return {
        "question_id": question["id"],
        "category": question["category"],
        "difficulty": question["difficulty"],
        "question": question["question"],
        "expected_retrieval_topics": " | ".join(
            question.get("expected_retrieval_topics", [])
        ),
        "expected_behavior": question.get("expected_behavior", ""),
        "evaluation_focus": " | ".join(
            question.get("evaluation_focus", [])
        ),
        "answer_status": generated.get("answer_status", ""),
        "latency_seconds": result.get("latency_seconds", ""),
        "source_count": len(generated.get("sources", [])),
        "citation_count": len(citation_markers),
        "citation_markers": " | ".join(citation_markers),
        "retrieved_sources": format_sources(
            generated.get("sources", [])
        ),
        "answer": generated.get("answer", ""),
        "error": result.get("error", ""),
        "retrieval_relevance_0_2": "",
        "answer_faithfulness_0_2": "",
        "citation_accuracy_0_2": "",
        "novice_readability_0_2": "",
        "refusal_appropriateness_0_2_or_na": "",
        "staged_hint_quality_0_2_or_na": "",
        "overall_pass_yes_no": "",
        "evaluator_notes": "",
    }


def save_results(
    results: list[dict[str, Any]],
    metadata: dict[str, Any],
    raw_results_path: Path,
    scoring_path: Path,
) -> None:
    raw_results_path.parent.mkdir(parents=True, exist_ok=True)
    scoring_path.parent.mkdir(parents=True, exist_ok=True)

    raw_payload = {
        "metadata": metadata,
        "results": results,
    }

    raw_results_path.write_text(
        json.dumps(raw_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    scoring_rows = [
        create_scoring_row(result)
        for result in results
    ]

    if not scoring_rows:
        return

    with scoring_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(scoring_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(scoring_rows)


def run_evaluation(
    test_set_path: Path,
    raw_results_path: Path,
    scoring_path: Path,
    evaluation_type: str,
    top_k: int,
    min_similarity_score: float,
) -> None:
    test_set = load_test_questions(test_set_path)
    questions = test_set["questions"]

    metadata = {
        "project": test_set.get("metadata", {}).get(
            "project",
            "RAG Programming Support System",
        ),
        "evaluation_type": evaluation_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": settings.ollama_model,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_timeout_seconds": settings.ollama_timeout_seconds,
        "ollama_num_predict": settings.ollama_num_predict,
        "ollama_think": settings.ollama_think,
        "ollama_keep_alive": settings.ollama_keep_alive,
        "embedding_model": "all-MiniLM-L6-v2",
        "collection_name": settings.collection_name,
        "top_k": top_k,
        "min_similarity_score": min_similarity_score,
        "question_count": len(questions),
    }

    results: list[dict[str, Any]] = []

    print("Technical evaluation started.")
    print(f"Model: {settings.ollama_model}")
    print(f"Questions: {len(questions)}")
    print(f"Top K: {top_k}")
    print(f"Minimum similarity: {min_similarity_score}")
    print("-" * 70)

    for index, question_data in enumerate(questions, start=1):
        question_id = question_data["id"]
        question_text = question_data["question"]

        print(
            f"[{index}/{len(questions)}] "
            f"{question_id}: {question_text.splitlines()[0]}"
        )

        started_at = time.perf_counter()
        error_message = ""

        try:
            generated_answer = generate_source_grounded_answer(
                query=question_text,
                top_k=top_k,
                min_similarity_score=min_similarity_score,
            )

            generated_result = generated_answer_to_dict(
                generated_answer
            )

        except Exception as error:
            error_message = str(error)

            generated_result = {
                "query": question_text,
                "answer_status": "error",
                "answer": "",
                "sources": [],
            }

        latency_seconds = round(
            time.perf_counter() - started_at,
            2,
        )

        evaluation_result = {
            "question_data": question_data,
            "generated_result": generated_result,
            "latency_seconds": latency_seconds,
            "error": error_message,
        }

        results.append(evaluation_result)

        # Save a checkpoint after every question.
        save_results(
            results=results,
            metadata=metadata,
            raw_results_path=raw_results_path,
            scoring_path=scoring_path,
        )

        print(
            f"Status: {generated_result['answer_status']} | "
            f"Sources: {len(generated_result['sources'])} | "
            f"Latency: {latency_seconds}s"
        )

        if error_message:
            print(f"Error: {error_message}")

        print("-" * 70)

    print("Technical evaluation completed.")
    print(f"Raw results: {raw_results_path}")
    print(f"Scoring sheet: {scoring_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the RAG system against the technical "
            "evaluation question set."
        )
    )

    parser.add_argument(
        "--test-set",
        type=Path,
        default=DEFAULT_TEST_SET_PATH,
    )
    parser.add_argument(
        "--raw-results",
        type=Path,
        default=DEFAULT_RAW_RESULTS_PATH,
    )
    parser.add_argument(
        "--scoring-file",
        type=Path,
        default=DEFAULT_SCORING_PATH,
    )
    parser.add_argument(
        "--evaluation-type",
        default="baseline_technical_evaluation",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--min-similarity-score",
        type=float,
        default=0.35,
    )

    args = parser.parse_args()

    run_evaluation(
        test_set_path=args.test_set,
        raw_results_path=args.raw_results,
        scoring_path=args.scoring_file,
        evaluation_type=args.evaluation_type,
        top_k=args.top_k,
        min_similarity_score=args.min_similarity_score,
    )


if __name__ == "__main__":
    main()
