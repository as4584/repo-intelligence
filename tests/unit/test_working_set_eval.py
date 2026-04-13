from __future__ import annotations

import json
import subprocess
from pathlib import Path

from change_radar.evals.working_set import evaluate_working_set, load_eval_cases


def test_load_eval_cases_reads_flat_json_format(tmp_path: Path) -> None:
    case_file = tmp_path / "cases.json"
    case_file.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "Payment retry flow",
                        "task": "add retry logic",
                        "expected_files": ["src/services/payment_service.ts"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    cases = load_eval_cases(case_file)

    assert len(cases) == 1
    assert cases[0].name == "Payment retry flow"
    assert cases[0].expected_files == ("src/services/payment_service.ts",)


def test_evaluate_working_set_computes_recall(tmp_path: Path) -> None:
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

    results = evaluate_working_set(repo, case_file)

    assert len(results) == 1
    assert results[0].recall_at_5 == 1.0
    assert results[0].recall_at_10 == 1.0
    assert results[0].missing_from_top_10 == ()
