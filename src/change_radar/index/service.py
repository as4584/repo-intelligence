"""Top-level indexing workflow."""

from __future__ import annotations

from pathlib import Path

from change_radar.config import default_db_path
from change_radar.git.history import collect_recent_commit_counts
from change_radar.parsers.js_ts import extract_symbols_and_edges
from change_radar.scanner.repo import discover_source_files
from change_radar.storage.sqlite import (
    connect,
    initialize_schema,
    replace_edges,
    replace_files,
    replace_git_stats,
    replace_symbols,
)
from change_radar.types import EdgeRecord, IndexSummary, SymbolRecord


def index_repository(repo_root: Path, db_path: Path | None = None) -> IndexSummary:
    repo_root = repo_root.resolve()
    if db_path is None:
        db_path = default_db_path(repo_root)

    files = discover_source_files(repo_root)
    available_paths = {item.relative_path for item in files}
    recent_commit_counts = collect_recent_commit_counts(repo_root)
    filtered_commit_counts = {
        path: count for path, count in recent_commit_counts.items() if path in available_paths
    }
    symbols: list[SymbolRecord] = []
    edges: list[EdgeRecord] = []

    for item in files:
        source_text = Path(item.absolute_path).read_text(encoding="utf-8", errors="ignore")
        file_symbols, file_edges = extract_symbols_and_edges(item, source_text, available_paths)
        symbols.extend(file_symbols)
        edges.extend(file_edges)

    connection = connect(db_path)
    try:
        initialize_schema(connection)
        file_count = replace_files(connection, str(repo_root), files)
        symbol_count = replace_symbols(connection, str(repo_root), symbols)
        edge_count = replace_edges(connection, str(repo_root), edges)
        replace_git_stats(connection, str(repo_root), filtered_commit_counts)
    finally:
        connection.close()

    return IndexSummary(
        repo_root=str(repo_root),
        db_path=str(db_path),
        file_count=file_count,
        symbol_count=symbol_count,
        edge_count=edge_count,
    )
