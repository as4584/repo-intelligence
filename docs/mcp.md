# MCP Workflow

Change Radar's MCP server is meant to support a narrow local-first agent loop:

1. check repo freshness with `repo_status`
2. run `index_repository` if the index is missing or stale
3. use `build_working_set`, `analyze_symbol`, or `analyze_diff`
4. use `build_prompt_pack` when you want a copy-pasteable edit brief
5. use `evaluate_working_set` or `benchmark_working_set` when tuning retrieval quality

## Recommended agent sequence

1. Call `repo_status` first.
2. If `has_index` is `false` or `is_stale` is `true`, call `index_repository`.
3. For task scoping, call `build_working_set`.
4. For impact checks, call `analyze_symbol` or `analyze_diff`.
5. For offline tuning, call `benchmark_working_set` with a curated case file.

## Tool notes

- `build_working_set`, `analyze_symbol`, `analyze_diff`, and `evaluate_working_set` now return JSON text payloads.
- These payloads include `repo_status` and `warnings` where freshness matters.
- `benchmark_working_set` writes JSON and Markdown artifacts to disk and returns their paths.

## Example local config

Use [examples/mcp.json.example](/root/studio/testing/repo-intelligence/examples/mcp.json.example) as the starting point for a stdio MCP client.
