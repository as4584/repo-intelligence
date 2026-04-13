"""Evaluation report formatters."""

from __future__ import annotations

from change_radar.evals.working_set import WorkingSetEvalResult


def format_working_set_eval(results: list[WorkingSetEvalResult]) -> str:
    lines = ["Working-set evaluation", ""]

    if not results:
        lines.append("No eval cases found.")
        return "\n".join(lines)

    avg_recall_at_5 = sum(item.recall_at_5 for item in results) / len(results)
    avg_recall_at_10 = sum(item.recall_at_10 for item in results) / len(results)

    lines.append(f"Average Recall@5:  {avg_recall_at_5:.2f}")
    lines.append(f"Average Recall@10: {avg_recall_at_10:.2f}")
    lines.append("")

    for item in results:
        lines.append(f"- {item.name}")
        lines.append(f"  task: {item.task}")
        lines.append(f"  recall@5: {item.recall_at_5:.2f}")
        lines.append(f"  recall@10: {item.recall_at_10:.2f}")
        lines.append(f"  predicted: {', '.join(item.predicted_top_10) or 'none'}")
        if item.missing_from_top_10:
            lines.append(f"  missing: {', '.join(item.missing_from_top_10)}")
        else:
            lines.append("  missing: none")

    return "\n".join(lines)
