"""Repository discovery and file filtering."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from change_radar.config import (
    FALLBACK_IGNORED_DIRECTORIES,
    MAX_FILE_SIZE_BYTES,
    SUPPORTED_SOURCE_SUFFIXES,
)
from change_radar.scanner.git import is_git_repository, list_repo_files
from change_radar.types import FileRecord


def discover_source_files(repo_root: Path) -> list[FileRecord]:
    """Discover source files for indexing.

    The first implementation uses Git when available to respect `.gitignore`.
    For non-Git directories, it falls back to a conservative filesystem walk.
    """
    repo_root = repo_root.resolve()
    if is_git_repository(repo_root):
        candidate_paths = list_repo_files(repo_root)
    else:
        candidate_paths = list(_walk_files(repo_root))

    records: list[FileRecord] = []
    seen_relative_paths: set[str] = set()

    for path in sorted(candidate_paths):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_SOURCE_SUFFIXES:
            continue

        stat = path.stat()
        if stat.st_size > MAX_FILE_SIZE_BYTES:
            continue

        relative_path = path.relative_to(repo_root).as_posix()
        if relative_path in seen_relative_paths:
            continue
        seen_relative_paths.add(relative_path)

        modified_at = datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat()
        records.append(
            FileRecord(
                repo_root=str(repo_root),
                relative_path=relative_path,
                absolute_path=str(path),
                suffix=suffix,
                size_bytes=stat.st_size,
                modified_at=modified_at,
            )
        )

    return records


def _walk_files(repo_root: Path) -> list[Path]:
    """Fallback file walk for non-Git directories."""
    results: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in FALLBACK_IGNORED_DIRECTORIES for part in path.parts):
            continue
        results.append(path)
    return results
