from __future__ import annotations

import subprocess
from pathlib import Path

from change_radar.analysis.status import get_repo_status
from change_radar.index.service import index_repository


def test_repo_status_reports_missing_index(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "index.ts").write_text("export const x = 1;\n", encoding="utf-8")

    status = get_repo_status(repo)

    assert status.has_index is False
    assert status.is_stale is True
    assert status.stale_reasons == ("index does not exist",)


def test_repo_status_reports_stale_after_file_change(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    (repo / "src").mkdir()
    (repo / "src" / "index.ts").write_text("export const x = 1;\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

    index_repository(repo)
    (repo / "src" / "index.ts").write_text("export const x = 2;\n", encoding="utf-8")

    status = get_repo_status(repo)

    assert status.has_index is True
    assert status.git_dirty is True
    assert status.is_stale is True
    assert any("changed since indexing" in reason for reason in status.stale_reasons)
