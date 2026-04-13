"""MCP server wrapper for Change Radar."""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from change_radar.analysis.diff import analyze_diff
from change_radar.analysis.symbol import analyze_symbol
from change_radar.evals.working_set import evaluate_working_set
from change_radar.index.service import index_repository
from change_radar.ranking.task import build_working_set
from change_radar.reports.evals import format_working_set_eval
from change_radar.reports.markdown import (
    format_diff_insights,
    format_prompt_pack,
    format_symbol_insights,
    format_working_set,
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
        name="build_working_set",
        description="Rank the most relevant files for a coding task.",
        structured_output=False,
    )
    def build_working_set_tool(repo: str, task: str, limit: int = 10) -> str:
        results = build_working_set(Path(repo), task, limit=limit)
        return _json_text({"task": task, "results": results})

    @server.tool(
        name="build_prompt_pack",
        description="Generate a copy-pasteable prompt pack for AI-assisted editing.",
        structured_output=False,
    )
    def build_prompt_pack_tool(repo: str, task: str, limit: int = 8) -> str:
        ranked = build_working_set(Path(repo), task, limit=limit)
        return format_prompt_pack(task, ranked)

    @server.tool(
        name="analyze_symbol",
        description="Inspect an indexed symbol and bounded downstream import impact.",
        structured_output=False,
    )
    def analyze_symbol_tool(
        repo: str, symbol: str, limit: int = 10, depth: int = 2
    ) -> str:
        results = analyze_symbol(Path(repo), symbol, limit=limit, max_depth=depth)
        return _json_text({"symbol": symbol, "depth": depth, "results": results})

    @server.tool(
        name="analyze_diff",
        description="Analyze the current working tree diff and bounded downstream impact.",
        structured_output=False,
    )
    def analyze_diff_tool(repo: str, depth: int = 2) -> str:
        results = analyze_diff(Path(repo), max_depth=depth)
        return _json_text({"depth": depth, "results": results})

    @server.tool(
        name="evaluate_working_set",
        description="Evaluate working-set ranking against a JSON case file.",
        structured_output=False,
    )
    def evaluate_working_set_tool(repo: str, cases: str, limit: int = 10) -> str:
        results = evaluate_working_set(Path(repo), Path(cases), limit=limit)
        return format_working_set_eval(results)

    return server


def run_mcp_server() -> None:
    server = create_mcp_server()
    server.run(transport="stdio")


def _json_text(payload: object) -> str:
    return json.dumps(to_jsonable(payload), indent=2)
