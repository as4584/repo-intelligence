"""Command-line interface."""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path

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
from change_radar.scanner.repo import discover_source_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="change-radar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Discover candidate source files")
    scan_parser.add_argument("repo", help="Path to the repository root")
    scan_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="How many files to print in text mode",
    )
    scan_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full file list as JSON",
    )

    index_parser = subparsers.add_parser("index", help="Initialize the local index")
    index_parser.add_argument("repo", help="Path to the repository root")

    analyze_symbol_parser = subparsers.add_parser(
        "analyze-symbol",
        help="Inspect an indexed symbol and direct file-level neighbors",
    )
    analyze_symbol_parser.add_argument("repo", help="Path to the repository root")
    analyze_symbol_parser.add_argument("--symbol", required=True, help="Symbol name query")
    analyze_symbol_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of symbol matches to return",
    )
    analyze_symbol_parser.add_argument(
        "--json",
        action="store_true",
        help="Print symbol analysis as JSON",
    )

    analyze_diff_parser = subparsers.add_parser(
        "analyze-diff",
        help="Analyze the current working tree diff against the local index",
    )
    analyze_diff_parser.add_argument("repo", help="Path to the repository root")
    analyze_diff_parser.add_argument(
        "--json",
        action="store_true",
        help="Print diff analysis as JSON",
    )

    working_set_parser = subparsers.add_parser(
        "build-working-set",
        help="Rank likely relevant files for a task",
    )
    working_set_parser.add_argument("repo", help="Path to the repository root")
    working_set_parser.add_argument("--task", required=True, help="Task description")
    working_set_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of files to return",
    )
    working_set_parser.add_argument(
        "--json",
        action="store_true",
        help="Print working-set results as JSON",
    )

    prompt_pack_parser = subparsers.add_parser(
        "build-prompt-pack",
        help="Generate a copy-pasteable prompt pack from the ranked working set",
    )
    prompt_pack_parser.add_argument("repo", help="Path to the repository root")
    prompt_pack_parser.add_argument("--task", required=True, help="Task description")
    prompt_pack_parser.add_argument(
        "--limit",
        type=int,
        default=8,
        help="Maximum number of files to include",
    )

    eval_parser = subparsers.add_parser(
        "evaluate-working-set",
        help="Run recall metrics for working-set ranking against a case file",
    )
    eval_parser.add_argument("repo", help="Path to the repository root")
    eval_parser.add_argument(
        "--cases",
        required=True,
        help="Path to a JSON file describing evaluation cases",
    )
    eval_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum ranked files to evaluate per case",
    )
    eval_parser.add_argument(
        "--json",
        action="store_true",
        help="Print evaluation results as JSON",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        _run_scan(Path(args.repo), as_json=args.json, limit=args.limit)
        return

    if args.command == "index":
        _run_index(Path(args.repo))
        return

    if args.command == "analyze-symbol":
        _run_analyze_symbol(
            Path(args.repo), symbol=args.symbol, limit=args.limit, as_json=args.json
        )
        return

    if args.command == "analyze-diff":
        _run_analyze_diff(Path(args.repo), as_json=args.json)
        return

    if args.command == "build-working-set":
        _run_build_working_set(
            Path(args.repo), task=args.task, limit=args.limit, as_json=args.json
        )
        return

    if args.command == "build-prompt-pack":
        _run_build_prompt_pack(Path(args.repo), task=args.task, limit=args.limit)
        return

    if args.command == "evaluate-working-set":
        _run_evaluate_working_set(
            Path(args.repo), cases=Path(args.cases), limit=args.limit, as_json=args.json
        )
        return

    parser.error(f"Unknown command: {args.command}")


def _run_scan(repo_root: Path, *, as_json: bool, limit: int) -> None:
    files = discover_source_files(repo_root)
    if as_json:
        print(
            json.dumps(
                [
                    {
                        "relative_path": item.relative_path,
                        "suffix": item.suffix,
                        "size_bytes": item.size_bytes,
                        "modified_at": item.modified_at,
                    }
                    for item in files
                ],
                indent=2,
            )
        )
        return

    print(f"Discovered {len(files)} candidate source files in {repo_root.resolve()}")
    for item in files[:limit]:
        print(f"- {item.relative_path} ({item.size_bytes} bytes)")


def _run_index(repo_root: Path) -> None:
    summary = index_repository(repo_root)
    print(f"Indexed {summary.file_count} files")
    print(f"Symbols: {summary.symbol_count}")
    print(f"Edges:   {summary.edge_count}")
    print(f"Repo: {summary.repo_root}")
    print(f"DB:   {summary.db_path}")


def _run_build_working_set(repo_root: Path, *, task: str, limit: int, as_json: bool) -> None:
    ranked = build_working_set(repo_root, task, limit=limit)
    if as_json:
        _print_json(
            {
                "task": task,
                "results": ranked,
            }
        )
        return
    print(format_working_set(task, ranked))


def _run_analyze_symbol(repo_root: Path, *, symbol: str, limit: int, as_json: bool) -> None:
    insights = analyze_symbol(repo_root, symbol, limit=limit)
    if as_json:
        _print_json(
            {
                "symbol": symbol,
                "results": insights,
            }
        )
        return
    print(format_symbol_insights(symbol, insights))


def _run_analyze_diff(repo_root: Path, *, as_json: bool) -> None:
    insights = analyze_diff(repo_root)
    if as_json:
        _print_json({"results": insights})
        return
    print(format_diff_insights(insights))


def _run_build_prompt_pack(repo_root: Path, *, task: str, limit: int) -> None:
    ranked = build_working_set(repo_root, task, limit=limit)
    print(format_prompt_pack(task, ranked))


def _run_evaluate_working_set(
    repo_root: Path, *, cases: Path, limit: int, as_json: bool
) -> None:
    results = evaluate_working_set(repo_root, cases, limit=limit)
    if as_json:
        _print_json({"case_file": str(cases), "results": results})
        return
    print(format_working_set_eval(results))


def _print_json(payload: object) -> None:
    print(json.dumps(_to_jsonable(payload), indent=2))


def _to_jsonable(value: object) -> object:
    if is_dataclass(value):
        return {key: _to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    main()
