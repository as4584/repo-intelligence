"""Minimal heuristic working-set ranking."""

from __future__ import annotations

import re
from pathlib import Path

from change_radar.config import default_db_path
from change_radar.scanner.repo import discover_source_files
from change_radar.storage.sqlite import connect, load_index_snapshot
from change_radar.types import RankedFile

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


def build_working_set(repo_root: Path, task_text: str, *, limit: int = 10) -> list[RankedFile]:
    """Rank files for a task using path, symbol, and import-neighbor heuristics."""
    repo_root = repo_root.resolve()
    tokens = _normalize_tokens(task_text)

    db_path = default_db_path(repo_root)
    if db_path.exists():
        return _build_from_index(repo_root, db_path, tokens, limit)

    files = discover_source_files(repo_root)
    ranked: list[RankedFile] = []
    for item in files:
        score, reasons = _score_file(item.relative_path, [], tokens)
        if score <= 0:
            continue
        ranked.append(
            RankedFile(
                relative_path=item.relative_path,
                score=score,
                reasons=tuple(reasons),
            )
        )

    ranked.sort(key=lambda item: (-item.score, item.relative_path.count("/"), item.relative_path))
    return ranked[:limit]


def _normalize_tokens(task_text: str) -> list[str]:
    tokens = [match.group(0).lower() for match in TOKEN_RE.finditer(task_text)]
    return [token for token in tokens if len(token) >= 3]


def _build_from_index(repo_root: Path, db_path: Path, tokens: list[str], limit: int) -> list[RankedFile]:
    connection = connect(db_path)
    try:
        file_paths, symbols_by_path, edges, git_stats = load_index_snapshot(
            connection, str(repo_root)
        )
    finally:
        connection.close()

    reverse_imports: dict[str, list[str]] = {}
    forward_imports: dict[str, list[str]] = {}
    for source_path, target_path in edges:
        forward_imports.setdefault(source_path, []).append(target_path)
        reverse_imports.setdefault(target_path, []).append(source_path)

    base_scores: dict[str, tuple[float, list[str]]] = {}
    seed_paths: set[str] = set()
    for relative_path in file_paths:
        symbols = symbols_by_path.get(relative_path, [])
        score, reasons = _score_file(relative_path, symbols, tokens)
        if score > 0:
            base_scores[relative_path] = (score, reasons)
            seed_paths.add(relative_path)

    boosted: dict[str, tuple[float, list[str]]] = {}
    for relative_path in file_paths:
        score, reasons = base_scores.get(relative_path, (0.0, []))
        has_lexical_match = relative_path in base_scores

        imported_seeds = [
            target for target in forward_imports.get(relative_path, []) if target in seed_paths
        ]
        if imported_seeds:
            edge_weight = 1.5 if has_lexical_match else 0.5
            score += edge_weight * len(imported_seeds)
            reasons.append("imports matched file")

        reverse_seed_neighbors = [
            source for source in reverse_imports.get(relative_path, []) if source in seed_paths
        ]
        if reverse_seed_neighbors:
            edge_weight = 2.0 if has_lexical_match else 0.75
            score += edge_weight * len(reverse_seed_neighbors)
            reasons.append("imported by matched file")

        degree = len(reverse_imports.get(relative_path, []))
        if degree > 0:
            degree_cap = 1.0 if has_lexical_match else 0.5
            degree_step = 0.2 if has_lexical_match else 0.1
            score += min(degree_cap, degree_step * degree)
            reasons.append("connected import hub")

        recent_commit_count = git_stats.get(relative_path, 0)
        if recent_commit_count > 0:
            hotness_cap = 1.5 if has_lexical_match else 0.5
            hotness_step = 0.25 if has_lexical_match else 0.1
            score += min(hotness_cap, hotness_step * recent_commit_count)
            reasons.append(f"recently changed {recent_commit_count} commit(s)")

        if score <= 0:
            continue
        boosted[relative_path] = (score, _dedupe(reasons))

    ranked = [
        RankedFile(relative_path=path, score=score, reasons=tuple(reasons))
        for path, (score, reasons) in boosted.items()
    ]
    ranked.sort(key=lambda item: (-item.score, item.relative_path.count("/"), item.relative_path))
    return ranked[:limit]


def _score_file(
    relative_path: str, symbols: list[str], tokens: list[str]
) -> tuple[float, list[str]]:
    normalized_path = relative_path.lower()
    path_parts = normalized_path.split("/")
    filename = path_parts[-1]
    stem = filename.rsplit(".", 1)[0]

    score = 0.0
    reasons: list[str] = []

    for token in tokens:
        if token == stem:
            score += 5.0
            reasons.append(f"filename exactly matches '{token}'")
            continue

        if token in stem:
            score += 3.0
            reasons.append(f"filename contains '{token}'")

        directory_hits = [part for part in path_parts[:-1] if token in part]
        if directory_hits:
            score += 1.5 * len(directory_hits)
            reasons.append(f"path contains '{token}'")

        if token in normalized_path and token not in stem and not directory_hits:
            score += 1.0
            reasons.append(f"filepath mentions '{token}'")

        for symbol in symbols:
            normalized_symbol = symbol.lower()
            if token == normalized_symbol:
                score += 4.0
                reasons.append(f"symbol exactly matches '{token}'")
                continue
            if token in normalized_symbol:
                score += 2.5
                reasons.append(f"symbol contains '{token}'")

    if "test" in filename or ".spec." in filename or ".test." in filename:
        if any(token in {"test", "tests", "spec"} for token in tokens):
            score += 2.0
            reasons.append("task explicitly mentions tests")

    return score, _dedupe(reasons)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
