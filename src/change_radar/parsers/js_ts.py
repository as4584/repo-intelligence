"""Lightweight JS/TS structural extraction.

This module intentionally uses conservative regex heuristics for the current phase.
It gives the project structural signals now and is designed to be replaced by a
Tree-sitter-backed implementation later without changing the storage or ranking APIs.
"""

from __future__ import annotations

import posixpath
import re
from pathlib import PurePosixPath

from change_radar.config import SUPPORTED_SOURCE_SUFFIXES
from change_radar.types import EdgeRecord, FileRecord, SymbolRecord

IMPORT_FROM_RE = re.compile(
    r"""^\s*import(?:[\s\w{},*$]+from\s+)?["'](?P<spec>[^"']+)["']""",
    re.MULTILINE,
)
EXPORT_FROM_RE = re.compile(
    r"""^\s*export[\s\w{},*$]*from\s+["'](?P<spec>[^"']+)["']""",
    re.MULTILINE,
)
REQUIRE_RE = re.compile(r"""require\(\s*["'](?P<spec>[^"']+)["']\s*\)""")

FUNCTION_RE = re.compile(
    r"""^(?:export\s+)?(?:async\s+)?function\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(""",
    re.MULTILINE,
)
CLASS_RE = re.compile(
    r"""^(?:export\s+)?class\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b""",
    re.MULTILINE,
)
ARROW_CONST_RE = re.compile(
    r"""^(?:export\s+)?const\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_][A-Za-z0-9_]*)\s*=>""",
    re.MULTILINE,
)


def extract_symbols_and_edges(
    file_record: FileRecord, source_text: str, available_paths: set[str]
) -> tuple[list[SymbolRecord], list[EdgeRecord]]:
    symbols = _extract_symbols(file_record, source_text)
    edges = _extract_import_edges(file_record, source_text, available_paths)
    return symbols, edges


def _extract_symbols(file_record: FileRecord, source_text: str) -> list[SymbolRecord]:
    symbols: list[SymbolRecord] = []
    seen: set[tuple[str, str, int]] = set()

    for pattern, symbol_kind in (
        (FUNCTION_RE, "function"),
        (CLASS_RE, "class"),
        (ARROW_CONST_RE, "const"),
    ):
        for match in pattern.finditer(source_text):
            name = match.group("name")
            start_line = source_text.count("\n", 0, match.start()) + 1
            key = (name, symbol_kind, start_line)
            if key in seen:
                continue
            seen.add(key)
            symbols.append(
                SymbolRecord(
                    repo_root=file_record.repo_root,
                    symbol_name=name,
                    symbol_kind=symbol_kind,
                    relative_path=file_record.relative_path,
                    start_line=start_line,
                    end_line=start_line,
                )
            )

    symbols.sort(key=lambda item: (item.start_line, item.symbol_name))
    if not symbols:
        return []

    total_lines = source_text.count("\n") + 1
    ranged_symbols: list[SymbolRecord] = []
    for index, symbol in enumerate(symbols):
        next_start = symbols[index + 1].start_line if index + 1 < len(symbols) else total_lines + 1
        ranged_symbols.append(
            SymbolRecord(
                repo_root=symbol.repo_root,
                symbol_name=symbol.symbol_name,
                symbol_kind=symbol.symbol_kind,
                relative_path=symbol.relative_path,
                start_line=symbol.start_line,
                end_line=max(symbol.start_line, next_start - 1),
            )
        )
    return ranged_symbols


def _extract_import_edges(
    file_record: FileRecord, source_text: str, available_paths: set[str]
) -> list[EdgeRecord]:
    edges: list[EdgeRecord] = []
    seen: set[tuple[str, str, str, str]] = set()

    for pattern in (IMPORT_FROM_RE, EXPORT_FROM_RE, REQUIRE_RE):
        for match in pattern.finditer(source_text):
            spec = match.group("spec")
            resolved = _resolve_relative_import(file_record.relative_path, spec, available_paths)
            if resolved is None:
                continue

            key = (file_record.repo_root, file_record.relative_path, resolved, "imports")
            if key in seen:
                continue
            seen.add(key)
            edges.append(
                EdgeRecord(
                    repo_root=file_record.repo_root,
                    source_path=file_record.relative_path,
                    target_path=resolved,
                    edge_type="imports",
                )
            )

    edges.sort(key=lambda item: (item.source_path, item.target_path))
    return edges


def _resolve_relative_import(
    source_path: str, spec: str, available_paths: set[str]
) -> str | None:
    if not spec.startswith("."):
        return None

    source_parent = PurePosixPath(source_path).parent
    normalized_text = posixpath.normpath(str(source_parent / spec))
    raw_target = PurePosixPath(normalized_text)
    candidates = _candidate_paths(raw_target)
    for candidate in candidates:
        candidate_text = str(candidate)
        if candidate_text in available_paths:
            return candidate_text
    return None


def _candidate_paths(raw_target: PurePosixPath) -> list[PurePosixPath]:
    normalized = PurePosixPath(raw_target)
    if normalized.suffix:
        return [normalized]

    candidates: list[PurePosixPath] = []
    for suffix in sorted(SUPPORTED_SOURCE_SUFFIXES):
        candidates.append(normalized.with_suffix(suffix))
    for suffix in sorted(SUPPORTED_SOURCE_SUFFIXES):
        candidates.append(normalized / f"index{suffix}")
    return candidates
