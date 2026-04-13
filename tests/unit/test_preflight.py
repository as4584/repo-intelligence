from __future__ import annotations

from change_radar.analysis.preflight import build_index_warnings
from change_radar.types import RepoStatus


def test_build_index_warnings_reports_missing_required_index() -> None:
    status = RepoStatus(
        repo_root="/tmp/example",
        db_path="/tmp/example/.change-radar/index.db",
        has_index=False,
        indexed_at=None,
        indexed_file_count=0,
        current_file_count=3,
        git_dirty=False,
        is_stale=True,
        stale_reasons=("index does not exist",),
    )

    warnings = build_index_warnings(
        status, command_name="analyze-symbol", requires_index=True
    )

    assert len(warnings) == 1
    assert "depends on the local index" in warnings[0]
    assert "change-radar index /tmp/example" in warnings[0]


def test_build_index_warnings_reports_stale_index() -> None:
    status = RepoStatus(
        repo_root="/tmp/example",
        db_path="/tmp/example/.change-radar/index.db",
        has_index=True,
        indexed_at="2026-04-13T12:00:00Z",
        indexed_file_count=10,
        current_file_count=10,
        git_dirty=True,
        is_stale=True,
        stale_reasons=("2 file(s) changed since indexing",),
    )

    warnings = build_index_warnings(
        status, command_name="build-working-set", requires_index=False
    )

    assert len(warnings) == 1
    assert "looks stale" in warnings[0]
    assert "2 file(s) changed since indexing" in warnings[0]
