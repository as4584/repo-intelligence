from __future__ import annotations

import subprocess
from pathlib import Path

from change_radar.scanner.repo import discover_source_files


def test_discover_source_files_respects_gitignore(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    (repo / ".gitignore").write_text("ignored.ts\nnode_modules/\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "app.ts").write_text("export const app = true;\n", encoding="utf-8")
    (repo / "ignored.ts").write_text("export const ignored = true;\n", encoding="utf-8")
    (repo / "node_modules").mkdir()
    (repo / "node_modules" / "dep.ts").write_text(
        "export const dep = true;\n", encoding="utf-8"
    )

    files = discover_source_files(repo)

    assert [item.relative_path for item in files] == ["src/app.ts"]


def test_discover_source_files_falls_back_without_git(tmp_path: Path) -> None:
    repo = tmp_path / "plain"
    repo.mkdir()

    (repo / "src").mkdir()
    (repo / "src" / "index.ts").write_text("export const x = 1;\n", encoding="utf-8")
    (repo / "node_modules").mkdir()
    (repo / "node_modules" / "skip.ts").write_text(
        "export const skip = 1;\n", encoding="utf-8"
    )
    (repo / "README.md").write_text("# plain\n", encoding="utf-8")

    files = discover_source_files(repo)

    assert [item.relative_path for item in files] == ["src/index.ts"]
