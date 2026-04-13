"""MCP server wrapper for Change Radar."""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from change_radar.analysis.diff import analyze_diff
from change_radar.analysis.preflight import build_index_warnings
from change_radar.analysis.status import get_repo_status
from change_radar.analysis.symbol import analyze_symbol
from change_radar.evals.working_set import evaluate_working_set
from change_radar.index.service import index_repository
from change_radar.ranking.task import build_working_set
from change_radar.reports.evals import (
    summarize_working_set_eval,
    write_working_set_eval_artifacts,
)
from change_radar.reports.markdown import (
    format_prompt_pack,
)
from change_radar.serialization import to_jsonable


def create_mcp_server() -> FastMCP:
    server = FastMCP(
        name="Change Radar",
        instructions=(
            "Use Change Radar to index a local repository, build an edit working set, "
            "inspect symbol neighbors, analyze the current diff, and evaluate retrieval quality."
        ),
    )

    @server.tool(
        name="index_repository",
        description="Index a local repository for Change Radar analysis.",
        structured_output=False,
    )
    def index_repository_tool(repo: str) -> str:
        summary = index_repository(Path(repo))
        return _json_text({"summary": summary})

    @server.tool(
        name="repo_status",
        description="Check whether the local index exists and whether it looks stale.",
        structured_output=False,
    )
    def repo_status_tool(repo: str) -> str:
        status = get_repo_status(Path(repo))
        return _json_text({"repo_status": status})

    @server.tool(
        name="build_working_set",
        description="Rank the most relevant files for a coding task.",
        structured_output=False,
    )
    def build_working_set_tool(repo: str, task: str, limit: int = 10) -> str:
        status = get_repo_status(Path(repo))
        warnings = build_index_warnings(
            status, command_name="build-working-set", requires_index=False
        )
        results = build_working_set(Path(repo), task, limit=limit)
        return _json_text(
            {
                "task": task,
                "repo_status": status,
                "warnings": warnings,
                "results": results,
            }
        )

    @server.tool(
        name="build_prompt_pack",
        description="Generate a copy-pasteable prompt pack for AI-assisted editing.",
        structured_output=False,
    )
    def build_prompt_pack_tool(repo: str, task: str, limit: int = 8) -> str:
        status = get_repo_status(Path(repo))
        warnings = build_index_warnings(
            status, command_name="build-prompt-pack", requires_index=False
        )
        ranked = build_working_set(Path(repo), task, limit=limit)
        prompt = format_prompt_pack(task, ranked)
        if not warnings:
            return prompt
        warning_lines = ["Warnings:", *[f"- {warning}" for warning in warnings], ""]
        return "\n".join(warning_lines) + prompt

    @server.tool(
        name="analyze_symbol",
        description="Inspect an indexed symbol and bounded downstream import impact.",
        structured_output=False,
    )
    def analyze_symbol_tool(
        repo: str, symbol: str, limit: int = 10, depth: int = 2
    ) -> str:
        status = get_repo_status(Path(repo))
        warnings = build_index_warnings(status, command_name="analyze-symbol", requires_index=True)
        results = analyze_symbol(Path(repo), symbol, limit=limit, max_depth=depth)
        return _json_text(
            {
                "symbol": symbol,
                "depth": depth,
                "repo_status": status,
                "warnings": warnings,
                "results": results,
            }
        )

    @server.tool(
        name="analyze_diff",
        description="Analyze the current working tree diff and bounded downstream impact.",
        structured_output=False,
    )
    def analyze_diff_tool(repo: str, depth: int = 2) -> str:
        status = get_repo_status(Path(repo))
        warnings = build_index_warnings(status, command_name="analyze-diff", requires_index=False)
        results = analyze_diff(Path(repo), max_depth=depth)
        return _json_text(
            {
                "depth": depth,
                "repo_status": status,
                "warnings": warnings,
                "results": results,
            }
        )

    @server.tool(
        name="evaluate_working_set",
        description="Evaluate working-set ranking against a JSON case file.",
        structured_output=False,
    )
    def evaluate_working_set_tool(repo: str, cases: str, limit: int = 10) -> str:
        status = get_repo_status(Path(repo))
        warnings = build_index_warnings(
            status, command_name="evaluate-working-set", requires_index=False
        )
        results = evaluate_working_set(Path(repo), Path(cases), limit=limit)
        summary = summarize_working_set_eval(results)
        return _json_text(
            {
                "case_file": cases,
                "repo_status": status,
                "warnings": warnings,
                "summary": summary,
                "results": results,
            }
        )

    @server.tool(
        name="benchmark_working_set",
        description="Run working-set evals and write benchmark artifacts to disk.",
        structured_output=False,
    )
    def benchmark_working_set_tool(
        repo: str, cases: str, output_dir: str | None = None, limit: int = 10
    ) -> str:
        repo_root = Path(repo)
        case_file = Path(cases)
        artifact_dir = Path(output_dir) if output_dir else (repo_root / ".change-radar" / "benchmarks")
        results = evaluate_working_set(repo_root, case_file, limit=limit)
        json_path, markdown_path, summary = write_working_set_eval_artifacts(
            artifact_dir,
            repo_root=repo_root,
            case_file=case_file,
            results=results,
        )
        status = get_repo_status(repo_root)
        warnings = build_index_warnings(
            status, command_name="benchmark-working-set", requires_index=False
        )
        return _json_text(
            {
                "case_file": cases,
                "output_dir": str(artifact_dir),
                "repo_status": status,
                "warnings": warnings,
                "summary": summary,
                "artifacts": {
                    "json": str(json_path),
                    "markdown": str(markdown_path),
                },
                "results": results,
            }
        )

    return server


def run_mcp_server() -> None:
    server = create_mcp_server()
    server.run(transport="stdio")


def _json_text(payload: object) -> str:
    return json.dumps(to_jsonable(payload), indent=2)
