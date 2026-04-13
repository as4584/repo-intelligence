"""Diff-level preflight analysis."""

from __future__ import annotations

from pathlib import Path

from change_radar.analysis.impact import build_import_maps, find_transitive_dependents
from change_radar.config import default_db_path
from change_radar.git.diff import parse_working_tree_diff
from change_radar.index.service import index_repository
from change_radar.storage.sqlite import (
    connect,
    load_all_file_paths,
    load_file_import_neighbors,
    load_import_edges,
    load_symbols_for_file,
)
from change_radar.types import DiffFileInsight


def analyze_diff(
    repo_root: Path,
    *,
    refresh_index: bool = True,
    limit_tests: int = 5,
    max_depth: int = 2,
) -> list[DiffFileInsight]:
    repo_root = repo_root.resolve()
    if refresh_index:
        index_repository(repo_root)

    diff_changes = parse_working_tree_diff(repo_root)
    if not diff_changes:
        return []

    db_path = default_db_path(repo_root)
    if not db_path.exists():
        return []

    connection = connect(db_path)
    try:
        all_paths = load_all_file_paths(connection, str(repo_root))
        _forward_imports, reverse_imports = build_import_maps(
            load_import_edges(connection, str(repo_root))
        )
        insights: list[DiffFileInsight] = []
        for change in diff_changes:
            symbols = load_symbols_for_file(connection, str(repo_root), change.relative_path)
            changed_symbols = _match_symbols(change.changed_lines, symbols)
            dependents, dependencies = load_file_import_neighbors(
                connection, str(repo_root), change.relative_path
            )
            direct_dependents, transitive_dependents = find_transitive_dependents(
                reverse_imports,
                change.relative_path,
                max_depth=max_depth,
                limit=10,
            )
            non_test_dependents = [item for item in dependents if not _is_test_path(item)]
            non_test_direct_dependents = [
                item for item in direct_dependents if not _is_test_path(item)
            ]
            non_test_transitive_dependents = [
                item for item in transitive_dependents if not _is_test_path(item)
            ]
            suggested_tests = _suggest_tests_for_paths(
                [
                    change.relative_path,
                    *non_test_direct_dependents,
                    *non_test_transitive_dependents,
                ],
                all_paths,
                limit=limit_tests,
            )
            for dependent in (*direct_dependents, *transitive_dependents):
                if _is_test_path(dependent) and dependent not in suggested_tests:
                    suggested_tests.append(dependent)
            insights.append(
                DiffFileInsight(
                    relative_path=change.relative_path,
                    changed_lines=change.changed_lines,
                    changed_symbols=tuple(changed_symbols),
                    dependents=tuple(non_test_direct_dependents or non_test_dependents),
                    dependencies=tuple(dependencies),
                    suggested_tests=tuple(suggested_tests[:limit_tests]),
                    transitive_dependents=tuple(non_test_transitive_dependents),
                )
            )
    finally:
        connection.close()

    return insights


def _match_symbols(changed_lines: tuple[int, ...], symbols: list[object]) -> list[str]:
    matched: list[str] = []
    for line_number in changed_lines:
        for symbol in symbols:
            if int(symbol["start_line"]) <= line_number <= int(symbol["end_line"]):
                name = str(symbol["symbol_name"])
                if name not in matched:
                    matched.append(name)
                break
    return matched


def _suggest_tests(relative_path: str, all_paths: list[str], *, limit: int) -> list[str]:
    path = Path(relative_path)
    stem = path.stem
    basename_candidates = {
        f"{stem}.test",
        f"{stem}.spec",
        stem.replace(".service", ""),
        stem.replace("_service", ""),
    }

    matches: list[str] = []
    for candidate in all_paths:
        candidate_name = Path(candidate).name
        candidate_stem = Path(candidate).stem
        if not _is_test_path(candidate):
            continue
        if stem in candidate_name or candidate_stem in basename_candidates:
            matches.append(candidate)
            continue
        if path.parent.name and path.parent.name in candidate:
            matches.append(candidate)

    deduped: list[str] = []
    seen: set[str] = set()
    for match in matches:
        if match in seen:
            continue
        seen.add(match)
        deduped.append(match)
    return deduped[:limit]


def _suggest_tests_for_paths(
    relative_paths: list[str], all_paths: list[str], *, limit: int
) -> list[str]:
    suggested: list[str] = []
    for relative_path in relative_paths:
        for match in _suggest_tests(relative_path, all_paths, limit=limit):
            if match in suggested:
                continue
            suggested.append(match)
            if len(suggested) >= limit:
                return suggested
    return suggested


def _is_test_path(relative_path: str) -> bool:
    return ".test." in relative_path or ".spec." in relative_path or "/tests/" in relative_path
