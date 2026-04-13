from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def test_benchmark_working_set_writes_artifacts(tmp_path: Path) -> None:
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
    (repo / "src" / "services" / "payment_service.ts").write_text(
        "export function processPayment() { return true; }\n", encoding="utf-8"
    )
    (repo / "src" / "routes" / "checkout.ts").write_text(
        'import { processPayment } from "../services/payment_service";\n'
        "export function checkout() { return processPayment(); }\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

    case_file = tmp_path / "cases.json"
    case_file.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "Payment flow",
                        "task": "payment",
                        "expected_files": [
                            "src/services/payment_service.ts",
                            "src/routes/checkout.ts",
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "benchmarks"

    env = dict(os.environ)
    env["PYTHONPATH"] = "/root/studio/testing/repo-intelligence/src"

    result = subprocess.run(
        [
            "python3",
            "-m",
            "change_radar.cli",
            "benchmark-working-set",
            ".",
            "--cases",
            str(case_file),
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    json_reports = sorted(output_dir.glob("working-set-benchmark-*.json"))
    markdown_reports = sorted(output_dir.glob("working-set-benchmark-*.md"))

    assert "Recorded working-set benchmark" in result.stdout
    assert len(json_reports) == 1
    assert len(markdown_reports) == 1

    payload = json.loads(json_reports[0].read_text(encoding="utf-8"))
    assert payload["summary"]["case_count"] == 1
    assert payload["summary"]["average_recall_at_10"] == 1.0
    assert payload["results"][0]["name"] == "Payment flow"
