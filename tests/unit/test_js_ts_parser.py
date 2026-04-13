from __future__ import annotations

from change_radar.parsers.js_ts import extract_symbols_and_edges
from change_radar.types import FileRecord


def test_extract_symbols_and_edges_from_js_ts() -> None:
    file_record = FileRecord(
        repo_root="/repo",
        relative_path="src/routes/checkout.ts",
        absolute_path="/repo/src/routes/checkout.ts",
        suffix=".ts",
        size_bytes=100,
        modified_at="2026-01-01T00:00:00+00:00",
    )
    source_text = """
import { paymentService } from "../services/payment_service";
export function checkoutRoute() { return true; }
const handleRetry = () => true;
export class CheckoutController {}
"""
    available_paths = {
        "src/routes/checkout.ts",
        "src/services/payment_service.ts",
    }

    symbols, edges = extract_symbols_and_edges(file_record, source_text, available_paths)

    assert [item.symbol_name for item in symbols] == [
        "checkoutRoute",
        "handleRetry",
        "CheckoutController",
    ]
    assert [(item.source_path, item.target_path, item.edge_type) for item in edges] == [
        ("src/routes/checkout.ts", "src/services/payment_service.ts", "imports")
    ]
