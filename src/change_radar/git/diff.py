"""Git diff parsing for preflight analysis."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from change_radar.types import DiffFileChange

DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(?P<path>.+)$")
HUNK_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? \+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)


def parse_working_tree_diff(repo_root: Path) -> list[DiffFileChange]:
    """Parse uncommitted working-tree changes into changed file/line groups."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--unified=0", "--no-color"],
        check=True,
        capture_output=True,
        text=True,
    )
    return _parse_diff_output(result.stdout)


def _parse_diff_output(diff_text: str) -> list[DiffFileChange]:
    changes_by_path: dict[str, set[int]] = {}
    current_path: str | None = None

    for line in diff_text.splitlines():
        file_match = DIFF_FILE_RE.match(line)
        if file_match:
            current_path = file_match.group("path")
            changes_by_path.setdefault(current_path, set())
            continue

        hunk_match = HUNK_RE.match(line)
        if hunk_match and current_path is not None:
            new_start = int(hunk_match.group("new_start"))
            new_count = int(hunk_match.group("new_count") or "1")

            if new_count == 0:
                changes_by_path[current_path].add(max(1, new_start))
                continue

            for line_number in range(new_start, new_start + new_count):
                changes_by_path[current_path].add(line_number)

    return [
        DiffFileChange(relative_path=path, changed_lines=tuple(sorted(line_numbers)))
        for path, line_numbers in sorted(changes_by_path.items())
        if line_numbers
    ]
