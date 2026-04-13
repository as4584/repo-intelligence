from __future__ import annotations

import subprocess
from pathlib import Path

from change_radar.analysis.diff import analyze_diff


def test_analyze_diff_maps_changed_lines_to_symbols_and_bounded_impact(tmp_path: Path) -> None:
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
    (repo / "src" / "services").mkdir()
    (repo / "src" / "routes").mkdir()
    (repo / "src" / "controllers").mkdir()

    (repo / "src" / "services" / "payment_service.ts").write_text(
        "export function processPayment() {\n"
        "  return true;\n"
        "}\n",
        encoding="utf-8",
    )
    (repo / "src" / "services" / "payment_service.test.ts").write_text(
        "import { processPayment } from './payment_service';\n"
        "test('processPayment', () => expect(processPayment()).toBe(true));\n",
        encoding="utf-8",
    )
    (repo / "src" / "routes" / "checkout.ts").write_text(
        'import { processPayment } from "../services/payment_service";\n'
        "export function checkout() {\n"
        "  return processPayment();\n"
        "}\n",
        encoding="utf-8",
    )
    (repo / "src" / "routes" / "checkout.test.ts").write_text(
        'import { checkout } from "./checkout";\n'
        "test('checkout', () => expect(checkout()).toBe(true));\n",
        encoding="utf-8",
    )
    (repo / "src" / "controllers" / "checkout_controller.ts").write_text(
        'import { checkout } from "../routes/checkout";\n'
        "export function handleCheckout() {\n"
        "  return checkout();\n"
        "}\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

    (repo / "src" / "services" / "payment_service.ts").write_text(
        "export function processPayment() {\n"
        "  const updated = true;\n"
        "  return updated;\n"
        "}\n",
        encoding="utf-8",
    )

    insights = analyze_diff(repo)

    assert len(insights) == 1
    assert insights[0].relative_path == "src/services/payment_service.ts"
    assert insights[0].changed_symbols == ("processPayment",)
    assert insights[0].dependents == ("src/routes/checkout.ts",)
    assert insights[0].transitive_dependents == ("src/controllers/checkout_controller.ts",)
    assert insights[0].suggested_tests == (
        "src/services/payment_service.test.ts",
        "src/routes/checkout.test.ts",
    )
