"""Symbol-level analysis using the local index."""

from __future__ import annotations

from pathlib import Path

from change_radar.analysis.impact import build_import_maps, find_transitive_dependents
from change_radar.config import default_db_path
from change_radar.storage.sqlite import (
    connect,
    load_file_import_neighbors,
    load_import_edges,
    search_symbols,
)
from change_radar.types import SymbolInsight


def analyze_symbol(
    repo_root: Path, symbol_query: str, *, limit: int = 10, max_depth: int = 2
) -> list[SymbolInsight]:
    repo_root = repo_root.resolve()
    db_path = default_db_path(repo_root)
    if not db_path.exists():
        return []

    connection = connect(db_path)
    try:
        matches = search_symbols(connection, str(repo_root), symbol_query, limit=limit)
        _forward_imports, reverse_imports = build_import_maps(
            load_import_edges(connection, str(repo_root))
        )
        insights: list[SymbolInsight] = []
        for match in matches:
            dependents, dependencies = load_file_import_neighbors(
                connection, str(repo_root), match["relative_path"]
            )
            direct_dependents, transitive_dependents = find_transitive_dependents(
                reverse_imports,
                match["relative_path"],
                max_depth=max_depth,
                limit=10,
            )
            insights.append(
                SymbolInsight(
                    symbol_name=match["symbol_name"],
                    symbol_kind=match["symbol_kind"],
                    relative_path=match["relative_path"],
                    start_line=int(match["start_line"]),
                    dependents=tuple(direct_dependents or dependents),
                    dependencies=tuple(dependencies),
                    transitive_dependents=tuple(transitive_dependents),
                )
            )
    finally:
        connection.close()

    return insights
