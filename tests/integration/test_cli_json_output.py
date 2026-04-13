from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def test_build_working_set_json_output_is_machine_readable(tmp_path: Path) -> None:
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
    (repo / "src" / "services" / "payment_service.ts").write_text(
        "export function processPayment() { return true; }\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = "/root/studio/testing/repo-intelligence/src"

    subprocess.run(
        ["python3", "-m", "change_radar.cli", "index", "."],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    result = subprocess.run(
        [
            "python3",
            "-m",
            "change_radar.cli",
            "build-working-set",
            ".",
            "--task",
            "payment",
            "--json",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    payload = json.loads(result.stdout)
    assert payload["task"] == "payment"
    assert payload["results"][0]["relative_path"] == "src/services/payment_service.ts"


def test_analyze_diff_json_output_is_machine_readable(tmp_path: Path) -> None:
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
    (repo / "src" / "services" / "payment_service.ts").write_text(
        "export function processPayment() {\n  return true;\n}\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

    (repo / "src" / "services" / "payment_service.ts").write_text(
        "export function processPayment() {\n  const updated = true;\n  return updated;\n}\n",
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["PYTHONPATH"] = "/root/studio/testing/repo-intelligence/src"

    result = subprocess.run(
        ["python3", "-m", "change_radar.cli", "analyze-diff", ".", "--json"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    payload = json.loads(result.stdout)
    assert payload["results"][0]["relative_path"] == "src/services/payment_service.ts"
    assert payload["results"][0]["changed_symbols"] == ["processPayment"]
