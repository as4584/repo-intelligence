"""Core domain types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class FileRecord:
    repo_root: str
    relative_path: str
    absolute_path: str
    suffix: str
    size_bytes: int
    modified_at: str


@dataclass(slots=True, frozen=True)
class IndexSummary:
    repo_root: str
    db_path: str
    file_count: int
    symbol_count: int = 0
    edge_count: int = 0


@dataclass(slots=True, frozen=True)
class SymbolRecord:
    repo_root: str
    symbol_name: str
    symbol_kind: str
    relative_path: str
    start_line: int
    end_line: int


@dataclass(slots=True, frozen=True)
class EdgeRecord:
    repo_root: str
    source_path: str
    target_path: str
    edge_type: str


@dataclass(slots=True, frozen=True)
class RankedFile:
    relative_path: str
    score: float
    reasons: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class SymbolInsight:
    symbol_name: str
    symbol_kind: str
    relative_path: str
    start_line: int
    dependents: tuple[str, ...]
    dependencies: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class DiffFileChange:
    relative_path: str
    changed_lines: tuple[int, ...]


@dataclass(slots=True, frozen=True)
class DiffFileInsight:
    relative_path: str
    changed_lines: tuple[int, ...]
    changed_symbols: tuple[str, ...]
    dependents: tuple[str, ...]
    dependencies: tuple[str, ...]
    suggested_tests: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class RepoStatus:
    repo_root: str
    db_path: str
    has_index: bool
    indexed_at: str | None
    indexed_file_count: int
    current_file_count: int
    git_dirty: bool
    is_stale: bool
    stale_reasons: tuple[str, ...]
