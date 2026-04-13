"""Preflight warnings for index-dependent workflows."""

from __future__ import annotations

from change_radar.types import RepoStatus


def build_index_warnings(
    status: RepoStatus, *, command_name: str, requires_index: bool
) -> list[str]:
    warnings: list[str] = []
    reindex_hint = f"Run `change-radar index {status.repo_root}` to refresh it."

    if not status.has_index:
        if requires_index:
            warnings.append(
                f"`{command_name}` depends on the local index, but no index exists yet. "
                f"{reindex_hint}"
            )
        else:
            warnings.append(
                f"No local index exists yet, so `{command_name}` is using reduced heuristics. "
                f"{reindex_hint}"
            )
        return warnings

    if status.is_stale:
        reason_text = "; ".join(status.stale_reasons)
        warnings.append(
            f"The local index looks stale for `{command_name}` ({reason_text}). {reindex_hint}"
        )

    return warnings
