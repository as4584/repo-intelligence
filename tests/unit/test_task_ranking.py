from __future__ import annotations

import subprocess
from pathlib import Path

from change_radar.index.service import index_repository
from change_radar.ranking.task import build_working_set


def test_build_working_set_prioritizes_matching_paths(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    (repo / "src").mkdir()
    (repo / "src" / "payments").mkdir()
    (repo / "src" / "auth").mkdir()

    (repo / "src" / "payments" / "payment_service.ts").write_text(
        "export const paymentService = true;\n", encoding="utf-8"
    )
    (repo / "src" / "payments" / "checkout_route.ts").write_text(
        "export const checkoutRoute = true;\n", encoding="utf-8"
    )
    (repo / "src" / "auth" / "token_validation.ts").write_text(
        "export const tokenValidation = true;\n", encoding="utf-8"
    )

    ranked = build_working_set(repo, "add retry logic to payment flow", limit=2)

    assert [item.relative_path for item in ranked] == [
        "src/payments/payment_service.ts",
        "src/payments/checkout_route.ts",
    ]
    assert any("payment" in reason for reason in ranked[0].reasons)


def test_build_working_set_uses_indexed_import_neighbors(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    (repo / "src").mkdir()
    (repo / "src" / "routes").mkdir()
    (repo / "src" / "services").mkdir()

    (repo / "src" / "services" / "payment_service.ts").write_text(
        "export function processPayment() { return true; }\n", encoding="utf-8"
    )
    (repo / "src" / "routes" / "checkout.ts").write_text(
        'import { processPayment } from "../services/payment_service";\n'
        "export function checkout() { return processPayment(); }\n",
        encoding="utf-8",
    )

    index_repository(repo)
    ranked = build_working_set(repo, "payment", limit=2)

    assert [item.relative_path for item in ranked] == [
        "src/services/payment_service.ts",
        "src/routes/checkout.ts",
    ]
    assert "imported by matched file" in ranked[1].reasons or "imports matched file" in ranked[1].reasons


def test_build_working_set_uses_git_hotness_to_break_ties(tmp_path: Path) -> None:
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
    (repo / "src" / "auth").mkdir()
    alpha_path = repo / "src" / "auth" / "alpha.ts"
    zeta_path = repo / "src" / "auth" / "zeta.ts"

    alpha_path.write_text("export function alpha() { return true; }\n", encoding="utf-8")
    zeta_path.write_text("export function zeta() { return true; }\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

    zeta_path.write_text("export function zeta() { return 1; }\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "update zeta"], cwd=repo, check=True, capture_output=True)

    index_repository(repo)
    ranked = build_working_set(repo, "auth", limit=2)

    assert [item.relative_path for item in ranked] == [
        "src/auth/zeta.ts",
        "src/auth/alpha.ts",
    ]
    assert any("recently changed" in reason for reason in ranked[0].reasons)
