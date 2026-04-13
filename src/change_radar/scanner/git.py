"""Git-aware file listing helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def is_git_repository(repo_root: Path) -> bool:
    """Return True when the path is inside a Git working tree."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False

    return result.returncode == 0 and result.stdout.strip() == "true"


def list_repo_files(repo_root: Path) -> list[Path]:
    """List tracked and unignored files via Git."""
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        check=True,
        capture_output=True,
    )
    entries = [item for item in result.stdout.decode("utf-8").split("\x00") if item]
    return [repo_root / entry for entry in entries]


def is_working_tree_dirty(repo_root: Path) -> bool:
    """Return True when the Git working tree has uncommitted changes."""
    if not is_git_repository(repo_root):
        return False

    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    return bool(result.stdout.strip())
