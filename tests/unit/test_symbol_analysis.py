from __future__ import annotations

import subprocess
from pathlib import Path

from change_radar.analysis.symbol import analyze_symbol
from change_radar.index.service import index_repository


def test_analyze_symbol_returns_bounded_downstream_import_neighbors(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    (repo / "src").mkdir()
    (repo / "src" / "services").mkdir()
    (repo / "src" / "routes").mkdir()
    (repo / "src" / "controllers").mkdir()
    (repo / "src" / "services" / "payment_service.ts").write_text(
        "export function processPayment() { return true; }\n", encoding="utf-8"
    )
    (repo / "src" / "routes" / "checkout.ts").write_text(
        'import { processPayment } from "../services/payment_service";\n'
        "export function checkout() { return processPayment(); }\n",
        encoding="utf-8",
    )
    (repo / "src" / "controllers" / "checkout_controller.ts").write_text(
        'import { checkout } from "../routes/checkout";\n'
        "export function handleCheckout() { return checkout(); }\n",
        encoding="utf-8",
    )

    index_repository(repo)
    insights = analyze_symbol(repo, "processPayment")

    assert len(insights) == 1
    assert insights[0].relative_path == "src/services/payment_service.ts"
    assert insights[0].dependents == ("src/routes/checkout.ts",)
    assert insights[0].dependencies == ()
    assert insights[0].transitive_dependents == ("src/controllers/checkout_controller.ts",)
