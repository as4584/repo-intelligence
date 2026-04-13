"""SQLite persistence for the index spine."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from change_radar.types import EdgeRecord, FileRecord, SymbolRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    repo_root TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    absolute_path TEXT NOT NULL,
    suffix TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    modified_at TEXT NOT NULL,
    PRIMARY KEY (repo_root, relative_path)
);

CREATE TABLE IF NOT EXISTS symbols (
    repo_root TEXT NOT NULL,
    symbol_name TEXT NOT NULL,
    symbol_kind TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    PRIMARY KEY (repo_root, relative_path, symbol_name, start_line, end_line)
);

CREATE TABLE IF NOT EXISTS edges (
    repo_root TEXT NOT NULL,
    source_path TEXT NOT NULL,
    target_path TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    PRIMARY KEY (repo_root, source_path, target_path, edge_type)
);

CREATE TABLE IF NOT EXISTS git_stats (
    repo_root TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    recent_commit_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (repo_root, relative_path)
);

CREATE TABLE IF NOT EXISTS index_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_root TEXT NOT NULL,
    indexed_file_count INTEGER NOT NULL,
    indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_files_repo_root ON files (repo_root);
CREATE INDEX IF NOT EXISTS idx_symbols_repo_root ON symbols (repo_root);
CREATE INDEX IF NOT EXISTS idx_edges_repo_root ON edges (repo_root);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)
    connection.commit()


def replace_files(
    connection: sqlite3.Connection, repo_root: str, files: Iterable[FileRecord]
) -> int:
    connection.execute("DELETE FROM files WHERE repo_root = ?", (repo_root,))
    connection.executemany(
        """
        INSERT INTO files (
            repo_root,
            relative_path,
            absolute_path,
            suffix,
            size_bytes,
            modified_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item.repo_root,
                item.relative_path,
                item.absolute_path,
                item.suffix,
                item.size_bytes,
                item.modified_at,
            )
            for item in files
        ],
    )
    count = connection.execute(
        "SELECT COUNT(*) AS count FROM files WHERE repo_root = ?", (repo_root,)
    ).fetchone()["count"]
    connection.execute(
        """
        INSERT INTO index_runs (repo_root, indexed_file_count)
        VALUES (?, ?)
        """,
        (repo_root, count),
    )
    connection.commit()
    return int(count)


def replace_symbols(
    connection: sqlite3.Connection, repo_root: str, symbols: Iterable[SymbolRecord]
) -> int:
    connection.execute("DELETE FROM symbols WHERE repo_root = ?", (repo_root,))
    connection.executemany(
        """
        INSERT INTO symbols (
            repo_root,
            symbol_name,
            symbol_kind,
            relative_path,
            start_line,
            end_line
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item.repo_root,
                item.symbol_name,
                item.symbol_kind,
                item.relative_path,
                item.start_line,
                item.end_line,
            )
            for item in symbols
        ],
    )
    count = connection.execute(
        "SELECT COUNT(*) AS count FROM symbols WHERE repo_root = ?", (repo_root,)
    ).fetchone()["count"]
    connection.commit()
    return int(count)


def replace_edges(
    connection: sqlite3.Connection, repo_root: str, edges: Iterable[EdgeRecord]
) -> int:
    connection.execute("DELETE FROM edges WHERE repo_root = ?", (repo_root,))
    connection.executemany(
        """
        INSERT INTO edges (
            repo_root,
            source_path,
            target_path,
            edge_type
        ) VALUES (?, ?, ?, ?)
        """,
        [
            (
                item.repo_root,
                item.source_path,
                item.target_path,
                item.edge_type,
            )
            for item in edges
        ],
    )
    count = connection.execute(
        "SELECT COUNT(*) AS count FROM edges WHERE repo_root = ?", (repo_root,)
    ).fetchone()["count"]
    connection.commit()
    return int(count)


def replace_git_stats(
    connection: sqlite3.Connection, repo_root: str, recent_commit_counts: dict[str, int]
) -> int:
    connection.execute("DELETE FROM git_stats WHERE repo_root = ?", (repo_root,))
    connection.executemany(
        """
        INSERT INTO git_stats (
            repo_root,
            relative_path,
            recent_commit_count
        ) VALUES (?, ?, ?)
        """,
        [
            (
                repo_root,
                relative_path,
                commit_count,
            )
            for relative_path, commit_count in sorted(recent_commit_counts.items())
        ],
    )
    count = connection.execute(
        "SELECT COUNT(*) AS count FROM git_stats WHERE repo_root = ?", (repo_root,)
    ).fetchone()["count"]
    connection.commit()
    return int(count)


def load_index_snapshot(
    connection: sqlite3.Connection, repo_root: str
) -> tuple[list[str], dict[str, list[str]], list[tuple[str, str]], dict[str, int]]:
    file_rows = connection.execute(
        "SELECT relative_path FROM files WHERE repo_root = ? ORDER BY relative_path",
        (repo_root,),
    ).fetchall()
    symbol_rows = connection.execute(
        """
        SELECT relative_path, symbol_name
        FROM symbols
        WHERE repo_root = ?
        ORDER BY relative_path, symbol_name
        """,
        (repo_root,),
    ).fetchall()
    edge_rows = connection.execute(
        """
        SELECT source_path, target_path
        FROM edges
        WHERE repo_root = ? AND edge_type = 'imports'
        ORDER BY source_path, target_path
        """,
        (repo_root,),
    ).fetchall()
    git_rows = connection.execute(
        """
        SELECT relative_path, recent_commit_count
        FROM git_stats
        WHERE repo_root = ?
        ORDER BY relative_path
        """,
        (repo_root,),
    ).fetchall()

    file_paths = [row["relative_path"] for row in file_rows]
    symbols_by_path: dict[str, list[str]] = {}
    for row in symbol_rows:
        symbols_by_path.setdefault(row["relative_path"], []).append(row["symbol_name"])
    edges = [(row["source_path"], row["target_path"]) for row in edge_rows]
    git_stats = {row["relative_path"]: int(row["recent_commit_count"]) for row in git_rows}
    return file_paths, symbols_by_path, edges, git_stats


def search_symbols(
    connection: sqlite3.Connection, repo_root: str, query: str, *, limit: int = 10
) -> list[sqlite3.Row]:
    normalized = query.lower()
    return connection.execute(
        """
        SELECT
            symbol_name,
            symbol_kind,
            relative_path,
            start_line,
            CASE
                WHEN LOWER(symbol_name) = ? THEN 2
                WHEN LOWER(symbol_name) LIKE ? THEN 1
                ELSE 0
            END AS match_rank
        FROM symbols
        WHERE repo_root = ? AND LOWER(symbol_name) LIKE ?
        ORDER BY match_rank DESC, relative_path ASC, start_line ASC
        LIMIT ?
        """,
        (normalized, f"%{normalized}%", repo_root, f"%{normalized}%", limit),
    ).fetchall()


def load_file_import_neighbors(
    connection: sqlite3.Connection, repo_root: str, relative_path: str
) -> tuple[list[str], list[str]]:
    dependent_rows = connection.execute(
        """
        SELECT source_path
        FROM edges
        WHERE repo_root = ? AND edge_type = 'imports' AND target_path = ?
        ORDER BY source_path
        """,
        (repo_root, relative_path),
    ).fetchall()
    dependency_rows = connection.execute(
        """
        SELECT target_path
        FROM edges
        WHERE repo_root = ? AND edge_type = 'imports' AND source_path = ?
        ORDER BY target_path
        """,
        (repo_root, relative_path),
    ).fetchall()

    dependents = [row["source_path"] for row in dependent_rows]
    dependencies = [row["target_path"] for row in dependency_rows]
    return dependents, dependencies


def load_symbols_for_file(
    connection: sqlite3.Connection, repo_root: str, relative_path: str
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT symbol_name, symbol_kind, start_line, end_line
        FROM symbols
        WHERE repo_root = ? AND relative_path = ?
        ORDER BY start_line ASC, symbol_name ASC
        """,
        (repo_root, relative_path),
    ).fetchall()


def load_all_file_paths(connection: sqlite3.Connection, repo_root: str) -> list[str]:
    rows = connection.execute(
        """
        SELECT relative_path
        FROM files
        WHERE repo_root = ?
        ORDER BY relative_path
        """,
        (repo_root,),
    ).fetchall()
    return [row["relative_path"] for row in rows]


def load_index_file_metadata(
    connection: sqlite3.Connection, repo_root: str
) -> dict[str, str]:
    rows = connection.execute(
        """
        SELECT relative_path, modified_at
        FROM files
        WHERE repo_root = ?
        ORDER BY relative_path
        """,
        (repo_root,),
    ).fetchall()
    return {row["relative_path"]: row["modified_at"] for row in rows}


def load_latest_index_run(
    connection: sqlite3.Connection, repo_root: str
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT indexed_file_count, indexed_at
        FROM index_runs
        WHERE repo_root = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (repo_root,),
    ).fetchone()
