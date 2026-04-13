"""Markdown formatters for CLI output."""

from __future__ import annotations

from change_radar.types import DiffFileInsight, RankedFile, RepoStatus, SymbolInsight


def format_working_set(task_text: str, ranked_files: list[RankedFile]) -> str:
    lines = [f"Working set for task: {task_text}", ""]

    if not ranked_files:
        lines.append("No strong file matches yet.")
        return "\n".join(lines)

    for item in ranked_files:
        reason_text = "; ".join(item.reasons)
        lines.append(f"- {item.relative_path} [score={item.score:.1f}]")
        lines.append(f"  why: {reason_text}")

    return "\n".join(lines)


def format_symbol_insights(symbol_query: str, insights: list[SymbolInsight]) -> str:
    lines = [f"Symbol analysis for: {symbol_query}", ""]

    if not insights:
        lines.append("No matching indexed symbols found.")
        return "\n".join(lines)

    for item in insights:
        lines.append(
            f"- {item.symbol_name} ({item.symbol_kind}) in {item.relative_path}:{item.start_line}"
        )
        if item.dependents:
            lines.append(f"  dependents: {', '.join(item.dependents)}")
        else:
            lines.append("  dependents: none")

        if item.dependencies:
            lines.append(f"  dependencies: {', '.join(item.dependencies)}")
        else:
            lines.append("  dependencies: none")

    return "\n".join(lines)


def format_diff_insights(insights: list[DiffFileInsight]) -> str:
    lines = ["Diff preflight", ""]

    if not insights:
        lines.append("No uncommitted JS/TS changes found.")
        return "\n".join(lines)

    for item in insights:
        lines.append(f"- {item.relative_path}")
        lines.append(
            f"  changed lines: {', '.join(str(line) for line in item.changed_lines)}"
        )
        if item.changed_symbols:
            lines.append(f"  changed symbols: {', '.join(item.changed_symbols)}")
        else:
            lines.append("  changed symbols: none mapped")

        if item.dependents:
            lines.append(f"  likely dependents: {', '.join(item.dependents)}")
        else:
            lines.append("  likely dependents: none")

        if item.dependencies:
            lines.append(f"  direct dependencies: {', '.join(item.dependencies)}")
        else:
            lines.append("  direct dependencies: none")

        if item.suggested_tests:
            lines.append(f"  suggested tests: {', '.join(item.suggested_tests)}")
        else:
            lines.append("  suggested tests: none")

    return "\n".join(lines)


def format_prompt_pack(task_text: str, ranked_files: list[RankedFile]) -> str:
    lines = [
        "Prompt pack",
        "",
        f"Task: {task_text}",
        "",
    ]

    if not ranked_files:
        lines.append("No strong file recommendations yet.")
        return "\n".join(lines)

    lines.extend(
        [
            "Use the following files as the primary working set:",
            "",
        ]
    )
    for item in ranked_files:
        lines.append(f"- #{item.relative_path}")

    lines.extend(
        [
            "",
            "Why these files:",
            "",
        ]
    )
    for item in ranked_files:
        lines.append(f"- {item.relative_path}: {'; '.join(item.reasons)}")

    lines.extend(
        [
            "",
            "Editing instructions:",
            "- Make the smallest safe change that satisfies the task.",
            "- Stay within the working set unless another file is clearly necessary.",
            "- If another file is needed, explain why before expanding scope.",
            "- Update or run nearby tests for the touched area.",
        ]
    )

    return "\n".join(lines)


def format_repo_status(status: RepoStatus) -> str:
    lines = ["Repo status", ""]
    lines.append(f"Repo: {status.repo_root}")
    lines.append(f"Index DB: {status.db_path}")
    lines.append(f"Has index: {'yes' if status.has_index else 'no'}")
    lines.append(f"Indexed at: {status.indexed_at or 'never'}")
    lines.append(f"Indexed files: {status.indexed_file_count}")
    lines.append(f"Current files: {status.current_file_count}")
    lines.append(f"Git dirty: {'yes' if status.git_dirty else 'no'}")
    lines.append(f"Index stale: {'yes' if status.is_stale else 'no'}")
    if status.stale_reasons:
        lines.append("Reasons:")
        for reason in status.stale_reasons:
            lines.append(f"- {reason}")
    return "\n".join(lines)
