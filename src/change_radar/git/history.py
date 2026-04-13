"""Git history summaries used for ranking."""

from __future__ import annotations

import subprocess
from pathlib import Path


def collect_recent_commit_counts(
    repo_root: Path, *, max_commits: int = 200
) -> dict[str, int]:
    """Return recent commit counts keyed by relative path.

    The signal is intentionally coarse. It captures which files appear most often
    in recent commits and is used as a lightweight hotness heuristic.
    """
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "log",
            f"-n{max_commits}",
            "--name-only",
            "--format=format:__COMMIT__",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {}
    return _parse_git_log_name_only(result.stdout)


def _parse_git_log_name_only(log_text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    current_commit_files: set[str] = set()

    def flush_current_commit() -> None:
        for path in current_commit_files:
            counts[path] = counts.get(path, 0) + 1

    for raw_line in log_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "__COMMIT__":
            if current_commit_files:
                flush_current_commit()
                current_commit_files = set()
            continue
        current_commit_files.add(line)

    if current_commit_files:
        flush_current_commit()

    return counts
