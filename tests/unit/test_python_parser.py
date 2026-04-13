from __future__ import annotations

from change_radar.parsers.python import extract_symbols_and_edges
from change_radar.types import FileRecord


def test_extract_symbols_and_edges_from_python() -> None:
    file_record = FileRecord(
        repo_root="/repo",
        relative_path="src/change_radar/cli.py",
        absolute_path="/repo/src/change_radar/cli.py",
        suffix=".py",
        size_bytes=100,
        modified_at="2026-01-01T00:00:00+00:00",
    )
    source_text = """
from change_radar.analysis.diff import analyze_diff
from change_radar.analysis import status
import change_radar.mcp_server


def main():
    return True


class Runner:
    pass
"""
    available_paths = {
        "src/change_radar/analysis/diff.py",
        "src/change_radar/analysis/__init__.py",
        "src/change_radar/mcp_server.py",
        "src/change_radar/cli.py",
    }

    symbols, edges = extract_symbols_and_edges(file_record, source_text, available_paths)

    assert [item.symbol_name for item in symbols] == ["main", "Runner"]
    assert [(item.source_path, item.target_path, item.edge_type) for item in edges] == [
        ("src/change_radar/cli.py", "src/change_radar/analysis/__init__.py", "imports"),
        ("src/change_radar/cli.py", "src/change_radar/analysis/diff.py", "imports"),
        ("src/change_radar/cli.py", "src/change_radar/mcp_server.py", "imports"),
    ]
