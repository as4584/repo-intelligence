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
