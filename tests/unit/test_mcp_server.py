from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

from change_radar.mcp_server import create_mcp_server


def test_mcp_server_lists_expected_tools() -> None:
    server = create_mcp_server()

    tool_names = [tool.name for tool in asyncio.run(server.list_tools())]

    assert tool_names == [
        "index_repository",
        "repo_status",
        "build_working_set",
        "build_prompt_pack",
        "analyze_symbol",
        "analyze_diff",
        "evaluate_working_set",
        "benchmark_working_set",
    ]


def test_mcp_server_build_working_set_tool_returns_structured_data(tmp_path: Path) -> None:
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

    server = create_mcp_server()
    content_blocks = asyncio.run(
        server.call_tool(
            "build_working_set",
            {
                "repo": str(repo),
                "task": "payment",
                "limit": 5,
            },
        )
    )
    text = content_blocks[0].text
    payload = json.loads(text)

    assert payload["task"] == "payment"
    assert len(payload["warnings"]) == 1
    assert payload["repo_status"]["has_index"] is False
    assert payload["results"][0]["relative_path"] == "src/services/payment_service.ts"


def test_mcp_server_benchmark_tool_writes_artifacts_and_returns_summary(
    tmp_path: Path,
) -> None:
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

    case_file = tmp_path / "cases.json"
    case_file.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "Payment flow",
                        "task": "payment",
                        "expected_files": ["src/services/payment_service.ts"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "benchmarks"

    server = create_mcp_server()
    content_blocks = asyncio.run(
        server.call_tool(
            "benchmark_working_set",
            {
                "repo": str(repo),
                "cases": str(case_file),
                "output_dir": str(output_dir),
                "limit": 5,
            },
        )
    )
    payload = json.loads(content_blocks[0].text)

    assert payload["summary"]["case_count"] == 1
    assert payload["summary"]["average_recall_at_10"] == 1.0
    assert Path(payload["artifacts"]["json"]).exists()
    assert Path(payload["artifacts"]["markdown"]).exists()


def test_mcp_server_evaluate_tool_returns_json_summary(tmp_path: Path) -> None:
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

    case_file = tmp_path / "cases.json"
    case_file.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "Payment flow",
                        "task": "payment",
                        "expected_files": ["src/services/payment_service.ts"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    server = create_mcp_server()
    content_blocks = asyncio.run(
        server.call_tool(
            "evaluate_working_set",
            {
                "repo": str(repo),
                "cases": str(case_file),
                "limit": 5,
            },
        )
    )
    payload = json.loads(content_blocks[0].text)

    assert payload["case_file"] == str(case_file)
    assert payload["summary"]["case_count"] == 1
    assert payload["summary"]["average_recall_at_10"] == 1.0
