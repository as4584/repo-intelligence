"""Helpers for bounded import-graph impact analysis."""

from __future__ import annotations

from collections import deque


def build_import_maps(
    edges: list[tuple[str, str]],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    forward_imports: dict[str, list[str]] = {}
    reverse_imports: dict[str, list[str]] = {}

    for source_path, target_path in edges:
        forward_imports.setdefault(source_path, []).append(target_path)
        reverse_imports.setdefault(target_path, []).append(source_path)

    for mapping in (forward_imports, reverse_imports):
        for path, neighbors in mapping.items():
            mapping[path] = sorted(set(neighbors))

    return forward_imports, reverse_imports


def find_transitive_dependents(
    reverse_imports: dict[str, list[str]],
    relative_path: str,
    *,
    max_depth: int,
    limit: int,
) -> tuple[list[str], list[str]]:
    """Return direct and transitive reverse-import neighbors up to ``max_depth``."""
    if max_depth < 1 or limit <= 0:
        return [], []

    direct_dependents = list(reverse_imports.get(relative_path, []))
    if max_depth == 1:
        return direct_dependents[:limit], []

    seen: set[str] = {relative_path}
    queue = deque((item, 1) for item in direct_dependents)
    collected_direct: list[str] = []
    transitive_dependents: list[str] = []

    while queue:
        current_path, depth = queue.popleft()
        if current_path in seen:
            continue

        seen.add(current_path)
        if depth == 1:
            collected_direct.append(current_path)
        else:
            transitive_dependents.append(current_path)

        if len(collected_direct) + len(transitive_dependents) >= limit:
            continue

        if depth >= max_depth:
            continue

        for neighbor in reverse_imports.get(current_path, []):
            if neighbor in seen:
                continue
            queue.append((neighbor, depth + 1))

    return collected_direct, transitive_dependents
