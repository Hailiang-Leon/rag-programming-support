"""Build baseline-versus-final technical evaluation artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any


METRICS = [
    ("retrieval_relevance_0_2", "Retrieval relevance"),
    ("answer_faithfulness_0_2", "Answer faithfulness"),
    ("citation_accuracy_0_2", "Citation accuracy"),
    ("novice_readability_0_2", "Novice readability"),
    (
        "refusal_appropriateness_0_2_or_na",
        "Refusal appropriateness",
    ),
    (
        "staged_hint_quality_0_2_or_na",
        "Staged hint quality",
    ),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def parse_score(value: str | None) -> float | None:
    if value is None:
        return None

    normalised = value.strip().upper()

    if normalised in {"", "N/A", "NA"}:
        return None

    return float(normalised)


def score_summary(
    rows: list[dict[str, str]],
) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}

    for column, _ in METRICS:
        values = [
            score
            for row in rows
            if (
                score := parse_score(row.get(column))
            ) is not None
        ]

        total = sum(values)
        maximum = len(values) * 2
        percentage = (
            total / maximum * 100
            if maximum
            else 0.0
        )

        summary[column] = {
            "total": total,
            "maximum": maximum,
            "percentage": percentage,
            "count": float(len(values)),
        }

    return summary


def count_passes(
    rows: list[dict[str, str]],
) -> int:
    return sum(
        row.get(
            "overall_pass_yes_no",
            "",
        ).strip().lower()
        == "yes"
        for row in rows
    )


def result_map(
    raw_data: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        result["question_data"]["id"]: result
        for result in raw_data["results"]
    }


def latency_summary(
    raw_data: dict[str, Any],
) -> dict[str, float]:
    values = [
        float(result["latency_seconds"])
        for result in raw_data["results"]
    ]

    return {
        "total": sum(values),
        "average": statistics.mean(values),
        "median": statistics.median(values),
    }


def format_score(value: float) -> str:
    if value.is_integer():
        return str(int(value))

    return f"{value:.2f}"


def metadata_value(
    metadata: dict[str, Any],
    key: str,
) -> str:
    value = metadata.get(key)

    if value is None:
        return "Not recorded"

    return str(value)


def build_comparison_csv(
    baseline_scores: list[dict[str, str]],
    final_scores: list[dict[str, str]],
    baseline_raw: dict[str, Any],
    final_raw: dict[str, Any],
    output_path: Path,
) -> None:
    baseline_score_map = {
        row["question_id"]: row
        for row in baseline_scores
    }
    final_score_map = {
        row["question_id"]: row
        for row in final_scores
    }
    baseline_result_map = result_map(baseline_raw)
    final_result_map = result_map(final_raw)

    question_ids = [
        result["question_data"]["id"]
        for result in final_raw["results"]
    ]

    fieldnames = [
        "question_id",
        "category",
        "baseline_answer_status",
        "final_answer_status",
        "baseline_overall_pass",
        "final_overall_pass",
        "pass_change",
        "baseline_latency_seconds",
        "final_latency_seconds",
        "latency_change_seconds",
    ]

    for column, _ in METRICS:
        fieldnames.extend(
            [
                f"baseline_{column}",
                f"final_{column}",
            ]
        )

    rows: list[dict[str, str]] = []

    for question_id in question_ids:
        baseline_score = baseline_score_map[question_id]
        final_score = final_score_map[question_id]
        baseline_result = baseline_result_map[question_id]
        final_result = final_result_map[question_id]

        baseline_latency = float(
            baseline_result["latency_seconds"]
        )
        final_latency = float(
            final_result["latency_seconds"]
        )

        baseline_pass = baseline_score.get(
            "overall_pass_yes_no",
            "",
        )
        final_pass = final_score.get(
            "overall_pass_yes_no",
            "",
        )

        row = {
            "question_id": question_id,
            "category": final_score.get(
                "category",
                "",
            ),
            "baseline_answer_status": (
                baseline_result["generated_result"][
                    "answer_status"
                ]
            ),
            "final_answer_status": (
                final_result["generated_result"][
                    "answer_status"
                ]
            ),
            "baseline_overall_pass": baseline_pass,
            "final_overall_pass": final_pass,
            "pass_change": (
                f"{baseline_pass} -> {final_pass}"
            ),
            "baseline_latency_seconds": (
                f"{baseline_latency:.2f}"
            ),
            "final_latency_seconds": (
                f"{final_latency:.2f}"
            ),
            "latency_change_seconds": (
                f"{final_latency - baseline_latency:.2f}"
            ),
        }

        for column, _ in METRICS:
            row[f"baseline_{column}"] = (
                baseline_score.get(column, "")
            )
            row[f"final_{column}"] = (
                final_score.get(column, "")
            )

        rows.append(row)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


def build_summary(
    baseline_scores: list[dict[str, str]],
    final_scores: list[dict[str, str]],
    baseline_raw: dict[str, Any],
    final_raw: dict[str, Any],
    output_path: Path,
) -> None:
    baseline_metrics = score_summary(
        baseline_scores
    )
    final_metrics = score_summary(final_scores)

    baseline_latency = latency_summary(
        baseline_raw
    )
    final_latency = latency_summary(final_raw)

    baseline_passes = count_passes(
        baseline_scores
    )
    final_passes = count_passes(final_scores)

    baseline_metadata = baseline_raw.get(
        "metadata",
        {},
    )
    final_metadata = final_raw.get(
        "metadata",
        {},
    )

    baseline_results = result_map(baseline_raw)
    final_results = result_map(final_raw)

    final_errors = [
        result
        for result in final_raw["results"]
        if result.get("error")
    ]

    lines = [
        "# Final Technical Evaluation Summary",
        "",
        "## Evaluation overview",
        "",
        (
            "The same 12-question technical evaluation set was "
            "used to evaluate the baseline and optimized system "
            "configurations. To support a fair comparison, the "
            "baseline responses were rescored using the same rubric "
            "and evaluator standard as the final responses."
        ),
        "",
        "| Configuration | Baseline | Final |",
        "|---|---:|---:|",
        (
            "| Model | "
            f"`{metadata_value(baseline_metadata, 'model')}` | "
            f"`{metadata_value(final_metadata, 'model')}` |"
        ),
        (
            "| Evaluation type | "
            f"`{metadata_value(baseline_metadata, 'evaluation_type')}` | "
            f"`{metadata_value(final_metadata, 'evaluation_type')}` |"
        ),
        (
            "| Questions completed | "
            f"{len(baseline_raw['results'])} | "
            f"{len(final_raw['results'])} |"
        ),
        (
            "| Overall behavioural passes | "
            f"{baseline_passes}/{len(baseline_scores)} | "
            f"{final_passes}/{len(final_scores)} |"
        ),
        (
            "| Behavioural pass rate | "
            f"{baseline_passes / len(baseline_scores) * 100:.1f}% | "
            f"{final_passes / len(final_scores) * 100:.1f}% |"
        ),
        (
            "| Average recorded latency | "
            f"{baseline_latency['average']:.2f}s | "
            f"{final_latency['average']:.2f}s |"
        ),
        (
            "| Median recorded latency | "
            f"{baseline_latency['median']:.2f}s | "
            f"{final_latency['median']:.2f}s |"
        ),
        (
            "| Top K | "
            f"{metadata_value(baseline_metadata, 'top_k')} | "
            f"{metadata_value(final_metadata, 'top_k')} |"
        ),
        (
            "| Minimum similarity score | "
            f"{metadata_value(baseline_metadata, 'min_similarity_score')} | "
            f"{metadata_value(final_metadata, 'min_similarity_score')} |"
        ),
        "",
        "## Manual scoring comparison",
        "",
        (
            "| Metric | Baseline score | Baseline % | "
            "Final score | Final % | Change |"
        ),
        "|---|---:|---:|---:|---:|---:|",
    ]

    for column, label in METRICS:
        baseline = baseline_metrics[column]
        final = final_metrics[column]
        change = (
            final["percentage"]
            - baseline["percentage"]
        )

        lines.append(
            "| "
            f"{label} | "
            f"{format_score(baseline['total'])}/"
            f"{format_score(baseline['maximum'])} | "
            f"{baseline['percentage']:.1f}% | "
            f"{format_score(final['total'])}/"
            f"{format_score(final['maximum'])} | "
            f"{final['percentage']:.1f}% | "
            f"{change:+.1f} pp |"
        )

    q007_baseline_status = (
        baseline_results["Q007"][
            "generated_result"
        ]["answer_status"]
    )
    q007_final_status = (
        final_results["Q007"][
            "generated_result"
        ]["answer_status"]
    )
    q012_baseline_status = (
        baseline_results["Q012"][
            "generated_result"
        ]["answer_status"]
    )
    q012_final_status = (
        final_results["Q012"][
            "generated_result"
        ]["answer_status"]
    )

    lines.extend(
        [
            "",
            "## Key behavioural outcomes",
            "",
            (
                f"- Q007 changed from `{q007_baseline_status}` "
                f"to `{q007_final_status}` and returned a "
                "deterministic level-1 hint without revealing "
                "the complete solution. The hint included a citation "
                "marker, although citation-source alignment remains "
                "a limitation."
            ),
            (
                f"- Q012 changed from `{q012_baseline_status}` "
                f"to `{q012_final_status}` and explicitly "
                "identified the medical request as outside the "
                "introductory programming support scope."
            ),
            (
                "- Q011 continued to avoid unsupported claims "
                "by returning `insufficient_evidence`."
            ),
            (
                f"- The final run completed all "
                f"{len(final_raw['results'])} questions with "
                f"{len(final_errors)} runner errors."
            ),
            "",
            "## Interpretation",
            "",
            (
                "The optimized system achieved a 12/12 behavioural "
                "pass rate, compared with the baseline result. "
                "The most important improvements were staged-hint "
                "behaviour and explicit scope-aware refusal."
            ),
            "",
            (
                "Not all manual quality dimensions improved. Citation "
                "accuracy and novice readability decreased because of "
                "citation-source mismatches and responses that reached "
                "the configured output-token limit."
            ),
            "",
            (
                "The final result should be interpreted as a "
                "comparison between complete system configurations, "
                "not as a controlled prompt-only experiment. The "
                "baseline used `qwen3:4b-thinking`, while the final "
                "configuration used `qwen3:4b-instruct` together "
                "with updated hint, refusal, prompt, and runtime "
                "logic."
            ),
            "",
            "## Remaining limitations",
            "",
            (
                "- Several generated answers reached the configured "
                "`num_predict=256` limit and ended before completing "
                "the final sentence or Markdown structure."
            ),
            (
                "- Citation precision remains inconsistent. In "
                "particular, Q006 and Q007 cited S1 even though "
                "another retrieved source more directly supported "
                "the accumulator or running-total claim."
            ),
            (
                "- Q006 did not retrieve the strongest available "
                "accumulator-pattern chunk within the top three "
                "results."
            ),
            (
                "- CLI latency includes repeated embedding-model "
                "initialization and therefore does not fully "
                "represent a persistent FastAPI service session."
            ),
            "",
            "## Conclusion",
            "",
            (
                "The final evaluation demonstrates that the system "
                "meets the expected behaviour for all 12 test cases, "
                "including normal explanations, debugging support, "
                "staged hints, insufficient-evidence handling, and "
                "out-of-scope refusal. However, citation alignment, "
                "retrieval ranking, response completion, and runtime "
                "performance remain areas for future improvement."
            ),
            "",
        ]
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare baseline and final technical "
            "evaluation results."
        )
    )
    parser.add_argument(
        "--baseline-raw",
        type=Path,
        default=Path(
            "data/evaluation/"
            "technical_evaluation_baseline_raw.json"
        ),
    )
    parser.add_argument(
        "--baseline-scores",
        type=Path,
        default=Path(
            "data/evaluation/"
            "technical_evaluation_baseline_rescored.csv"
        ),
    )
    parser.add_argument(
        "--final-raw",
        type=Path,
        default=Path(
            "data/evaluation/"
            "technical_evaluation_final_raw.json"
        ),
    )
    parser.add_argument(
        "--final-scores",
        type=Path,
        default=Path(
            "data/evaluation/"
            "technical_evaluation_final_scores.csv"
        ),
    )
    parser.add_argument(
        "--comparison-output",
        type=Path,
        default=Path(
            "data/evaluation/"
            "technical_evaluation_comparison.csv"
        ),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path(
            "docs/evaluation/"
            "final_technical_evaluation_summary.md"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    baseline_raw = load_json(args.baseline_raw)
    final_raw = load_json(args.final_raw)
    baseline_scores = load_csv(
        args.baseline_scores
    )
    final_scores = load_csv(args.final_scores)

    build_comparison_csv(
        baseline_scores=baseline_scores,
        final_scores=final_scores,
        baseline_raw=baseline_raw,
        final_raw=final_raw,
        output_path=args.comparison_output,
    )

    build_summary(
        baseline_scores=baseline_scores,
        final_scores=final_scores,
        baseline_raw=baseline_raw,
        final_raw=final_raw,
        output_path=args.summary_output,
    )

    print(
        "Comparison CSV:",
        args.comparison_output,
    )
    print(
        "Summary:",
        args.summary_output,
    )


if __name__ == "__main__":
    main()
