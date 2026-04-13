"""Markdown formatters for CLI output."""

from __future__ import annotations

from change_radar.types import DiffFileInsight, RankedFile, SymbolInsight


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
