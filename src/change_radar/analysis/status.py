"""Repository and index status analysis."""

from __future__ import annotations

from pathlib import Path

from change_radar.config import default_db_path
from change_radar.scanner.git import is_working_tree_dirty
from change_radar.scanner.repo import discover_source_files
from change_radar.storage.sqlite import (
    connect,
    load_index_file_metadata,
    load_latest_index_run,
)
from change_radar.types import RepoStatus


def get_repo_status(repo_root: Path) -> RepoStatus:
    repo_root = repo_root.resolve()
    db_path = default_db_path(repo_root)
    current_files = discover_source_files(repo_root)
    current_by_path = {item.relative_path: item.modified_at for item in current_files}
    git_dirty = is_working_tree_dirty(repo_root)

    if not db_path.exists():
        return RepoStatus(
            repo_root=str(repo_root),
            db_path=str(db_path),
            has_index=False,
            indexed_at=None,
            indexed_file_count=0,
            current_file_count=len(current_files),
            git_dirty=git_dirty,
            is_stale=True,
            stale_reasons=("index does not exist",),
        )

    connection = connect(db_path)
    try:
        indexed_by_path = load_index_file_metadata(connection, str(repo_root))
        latest_run = load_latest_index_run(connection, str(repo_root))
    finally:
        connection.close()

    if latest_run is None:
        return RepoStatus(
            repo_root=str(repo_root),
            db_path=str(db_path),
            has_index=False,
            indexed_at=None,
            indexed_file_count=0,
            current_file_count=len(current_files),
            git_dirty=git_dirty,
            is_stale=True,
            stale_reasons=("index metadata is missing",),
        )

    stale_reasons: list[str] = []
    indexed_paths = set(indexed_by_path)
    current_paths = set(current_by_path)

    added_paths = current_paths - indexed_paths
    removed_paths = indexed_paths - current_paths
    changed_paths = {
        path
        for path in current_paths & indexed_paths
        if current_by_path[path] != indexed_by_path[path]
    }

    if added_paths:
        stale_reasons.append(f"{len(added_paths)} new file(s) are not indexed")
    if removed_paths:
        stale_reasons.append(f"{len(removed_paths)} indexed file(s) no longer exist")
    if changed_paths:
        stale_reasons.append(f"{len(changed_paths)} file(s) changed since indexing")

    return RepoStatus(
        repo_root=str(repo_root),
        db_path=str(db_path),
        has_index=True,
        indexed_at=str(latest_run["indexed_at"]),
        indexed_file_count=int(latest_run["indexed_file_count"]),
        current_file_count=len(current_files),
        git_dirty=git_dirty,
        is_stale=bool(stale_reasons),
        stale_reasons=tuple(stale_reasons),
    )
