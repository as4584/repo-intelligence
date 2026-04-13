"""Symbol-level analysis using the local index."""

from __future__ import annotations

from pathlib import Path

from change_radar.config import default_db_path
from change_radar.storage.sqlite import (
    connect,
    load_file_import_neighbors,
    search_symbols,
)
from change_radar.types import SymbolInsight


def analyze_symbol(repo_root: Path, symbol_query: str, *, limit: int = 10) -> list[SymbolInsight]:
    repo_root = repo_root.resolve()
    db_path = default_db_path(repo_root)
    if not db_path.exists():
        return []

    connection = connect(db_path)
    try:
        matches = search_symbols(connection, str(repo_root), symbol_query, limit=limit)
        insights: list[SymbolInsight] = []
        for match in matches:
            dependents, dependencies = load_file_import_neighbors(
                connection, str(repo_root), match["relative_path"]
            )
            insights.append(
                SymbolInsight(
                    symbol_name=match["symbol_name"],
                    symbol_kind=match["symbol_kind"],
                    relative_path=match["relative_path"],
                    start_line=int(match["start_line"]),
                    dependents=tuple(dependents),
                    dependencies=tuple(dependencies),
                )
            )
    finally:
        connection.close()

    return insights
