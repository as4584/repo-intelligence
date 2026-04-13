"""Dispatch structural extraction by file type."""

from __future__ import annotations

from change_radar.parsers.js_ts import extract_symbols_and_edges as extract_js_ts_symbols_and_edges
from change_radar.parsers.python import extract_symbols_and_edges as extract_python_symbols_and_edges
from change_radar.types import EdgeRecord, FileRecord, SymbolRecord


def extract_symbols_and_edges(
    file_record: FileRecord, source_text: str, available_paths: set[str]
) -> tuple[list[SymbolRecord], list[EdgeRecord]]:
    if file_record.suffix == ".py":
        return extract_python_symbols_and_edges(file_record, source_text, available_paths)
    return extract_js_ts_symbols_and_edges(file_record, source_text, available_paths)
