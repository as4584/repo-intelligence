"""Diff-level preflight analysis."""

from __future__ import annotations

import re
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

TEST_TOKEN_RE = re.compile(r"[a-z0-9]+")
TEST_STEM_SUFFIXES = (".test", ".spec", "_test", "_spec", "-test", "-spec")
SOURCE_ROLE_SUFFIXES = (
    ".service",
    "_service",
    ".controller",
    "_controller",
    ".route",
    "_route",
    ".handler",
    "_handler",
)


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
    source_variants = _subject_variants(path.stem)
    source_tokens = _tokenize(path.stem)
    source_dir_tokens = {
        token
        for part in path.parts[:-1]
        for token in _tokenize(part)
        if token not in {"src", "lib", "app"}
    }

    scored_matches: list[tuple[int, str]] = []
    for candidate in all_paths:
        if not _is_test_path(candidate):
            continue
        score = _score_test_candidate(
            candidate,
            source_variants=source_variants,
            source_tokens=source_tokens,
            source_dir_tokens=source_dir_tokens,
        )
        if score <= 0:
            continue
        scored_matches.append((score, candidate))

    scored_matches.sort(
        key=lambda item: (
            -item[0],
            item[1].count("/"),
            item[1],
        )
    )

    deduped: list[str] = []
    for _score, match in scored_matches:
        if match in deduped:
            continue
        deduped.append(match)
        if len(deduped) >= limit:
            break
    return deduped


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
    lowered = relative_path.lower()
    return (
        ".test." in lowered
        or ".spec." in lowered
        or "/tests/" in lowered
        or "/test/" in lowered
        or "/__tests__/" in lowered
    )


def _score_test_candidate(
    relative_path: str,
    *,
    source_variants: set[str],
    source_tokens: set[str],
    source_dir_tokens: set[str],
) -> int:
    candidate_path = Path(relative_path)
    candidate_variants = _subject_variants(candidate_path.stem)
    candidate_tokens = _tokenize(candidate_path.stem)
    candidate_dir_tokens = {
        token
        for part in candidate_path.parts[:-1]
        for token in _tokenize(part)
        if token not in {"tests", "test", "__tests__"}
    }

    score = 0
    shared_variants = source_variants & candidate_variants
    if shared_variants:
        score += 8

    shared_tokens = source_tokens & candidate_tokens
    if shared_tokens:
        score += 3 * len(shared_tokens)

    shared_dir_tokens = source_dir_tokens & candidate_dir_tokens
    if shared_dir_tokens:
        score += 2 * len(shared_dir_tokens)

    parent_name = candidate_path.parent.name.lower()
    if parent_name in {"tests", "test", "__tests__"}:
        score += 1

    return score


def _subject_variants(stem: str) -> set[str]:
    variants = {stem.lower()}
    pending = list(variants)
    while pending:
        current = pending.pop()
        for suffix in (*TEST_STEM_SUFFIXES, *SOURCE_ROLE_SUFFIXES):
            if not current.endswith(suffix):
                continue
            trimmed = current[: -len(suffix)]
            if trimmed and trimmed not in variants:
                variants.add(trimmed)
                pending.append(trimmed)
        if current.startswith("test_"):
            trimmed = current[5:]
            if trimmed and trimmed not in variants:
                variants.add(trimmed)
                pending.append(trimmed)
    return variants


def _tokenize(value: str) -> set[str]:
    return {match.group(0) for match in TEST_TOKEN_RE.finditer(value.lower())}
