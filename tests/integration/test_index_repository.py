from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

from change_radar.index.service import index_repository


def test_index_repository_creates_database_and_records_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    (repo / "src").mkdir()
    (repo / "src" / "main.ts").write_text(
        'import { worker } from "./worker";\n'
        "export function main() { return worker(); }\n",
        encoding="utf-8",
    )
    (repo / "src" / "worker.ts").write_text(
        "export function worker() { return false; }\n", encoding="utf-8"
    )

    summary = index_repository(repo)

    connection = sqlite3.connect(summary.db_path)
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM files WHERE repo_root = ?", (summary.repo_root,)
        ).fetchone()[0]
        symbol_count = connection.execute(
            "SELECT COUNT(*) FROM symbols WHERE repo_root = ?", (summary.repo_root,)
        ).fetchone()[0]
        edge_count = connection.execute(
            "SELECT COUNT(*) FROM edges WHERE repo_root = ?", (summary.repo_root,)
        ).fetchone()[0]
        git_stat_count = connection.execute(
            "SELECT COUNT(*) FROM git_stats WHERE repo_root = ?", (summary.repo_root,)
        ).fetchone()[0]
    finally:
        connection.close()

    assert summary.file_count == 2
    assert summary.symbol_count == 2
    assert summary.edge_count == 1
    assert count == 2
    assert symbol_count == 2
    assert edge_count == 1
    assert git_stat_count == 0


def test_index_repository_supports_python_modules(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    (repo / "src").mkdir()
    (repo / "src" / "change_radar").mkdir()
    (repo / "src" / "change_radar" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "src" / "change_radar" / "service.py").write_text(
        "def build_service():\n"
        "    return True\n",
        encoding="utf-8",
    )
    (repo / "src" / "change_radar" / "cli.py").write_text(
        "from change_radar.service import build_service\n"
        "\n"
        "def main():\n"
        "    return build_service()\n",
        encoding="utf-8",
    )

    summary = index_repository(repo)

    connection = sqlite3.connect(summary.db_path)
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM files WHERE repo_root = ?", (summary.repo_root,)
        ).fetchone()[0]
        symbol_count = connection.execute(
            "SELECT COUNT(*) FROM symbols WHERE repo_root = ?", (summary.repo_root,)
        ).fetchone()[0]
        edge_count = connection.execute(
            "SELECT COUNT(*) FROM edges WHERE repo_root = ?", (summary.repo_root,)
        ).fetchone()[0]
        imported_by_cli = connection.execute(
            """
            SELECT COUNT(*)
            FROM edges
            WHERE repo_root = ? AND source_path = ? AND target_path = ?
            """,
            (
                summary.repo_root,
                "src/change_radar/cli.py",
                "src/change_radar/service.py",
            ),
        ).fetchone()[0]
    finally:
        connection.close()

    assert summary.file_count == 3
    assert summary.symbol_count == 2
    assert summary.edge_count == 1
    assert count == 3
    assert symbol_count == 2
    assert edge_count == 1
    assert imported_by_cli == 1
