"""Evaluation report formatters."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from change_radar.evals.working_set import WorkingSetEvalResult
from change_radar.serialization import to_jsonable


def summarize_working_set_eval(results: list[WorkingSetEvalResult]) -> dict[str, object]:
    if not results:
        return {
            "case_count": 0,
            "average_recall_at_5": 0.0,
            "average_recall_at_10": 0.0,
            "average_query_duration_ms": 0.0,
            "max_query_duration_ms": 0.0,
            "perfect_recall_at_10_count": 0,
            "failing_cases": [],
        }

    average_recall_at_5 = sum(item.recall_at_5 for item in results) / len(results)
    average_recall_at_10 = sum(item.recall_at_10 for item in results) / len(results)
    average_query_duration_ms = sum(item.query_duration_ms for item in results) / len(results)
    max_query_duration_ms = max(item.query_duration_ms for item in results)
    perfect_recall_at_10_count = sum(1 for item in results if item.recall_at_10 == 1.0)
    failing_cases = [
        item.name for item in results if item.missing_from_top_10 or item.recall_at_10 < 1.0
    ]
    return {
        "case_count": len(results),
        "average_recall_at_5": average_recall_at_5,
        "average_recall_at_10": average_recall_at_10,
        "average_query_duration_ms": average_query_duration_ms,
        "max_query_duration_ms": max_query_duration_ms,
        "perfect_recall_at_10_count": perfect_recall_at_10_count,
        "failing_cases": failing_cases,
    }


def format_working_set_eval(results: list[WorkingSetEvalResult]) -> str:
    lines = ["Working-set evaluation", ""]

    if not results:
        lines.append("No eval cases found.")
        return "\n".join(lines)

    summary = summarize_working_set_eval(results)

    lines.append(f"Average Recall@5:  {summary['average_recall_at_5']:.2f}")
    lines.append(f"Average Recall@10: {summary['average_recall_at_10']:.2f}")
    lines.append(f"Average query latency: {summary['average_query_duration_ms']:.1f} ms")
    lines.append("")

    for item in results:
        lines.append(f"- {item.name}")
        lines.append(f"  task: {item.task}")
        lines.append(f"  recall@5: {item.recall_at_5:.2f}")
        lines.append(f"  recall@10: {item.recall_at_10:.2f}")
        lines.append(f"  query latency: {item.query_duration_ms:.1f} ms")
        lines.append(f"  predicted: {', '.join(item.predicted_top_10) or 'none'}")
        if item.missing_from_top_10:
            lines.append(f"  missing: {', '.join(item.missing_from_top_10)}")
        else:
            lines.append("  missing: none")

    return "\n".join(lines)


def write_working_set_eval_artifacts(
    output_dir: Path,
    *,
    repo_root: Path,
    case_file: Path,
    results: list[WorkingSetEvalResult],
) -> tuple[Path, Path, dict[str, object]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    generated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    summary = summarize_working_set_eval(results)

    payload = {
        "generated_at": generated_at,
        "repo_root": str(repo_root.resolve()),
        "case_file": str(case_file),
        "summary": summary,
        "results": results,
    }
    json_path = output_dir / f"working-set-benchmark-{stamp}.json"
    json_path.write_text(json.dumps(to_jsonable(payload), indent=2), encoding="utf-8")

    markdown_lines = [
        "# Working-set benchmark",
        "",
        f"- Generated at: {generated_at}",
        f"- Repo: {repo_root.resolve()}",
        f"- Case file: {case_file}",
        f"- Cases: {summary['case_count']}",
        f"- Average Recall@5: {summary['average_recall_at_5']:.2f}",
        f"- Average Recall@10: {summary['average_recall_at_10']:.2f}",
        f"- Average query latency: {summary['average_query_duration_ms']:.1f} ms",
        f"- Slowest query latency: {summary['max_query_duration_ms']:.1f} ms",
        "",
        format_working_set_eval(results),
        "",
    ]
    markdown_path = output_dir / f"working-set-benchmark-{stamp}.md"
    markdown_path.write_text("\n".join(markdown_lines), encoding="utf-8")
    return json_path, markdown_path, summary
