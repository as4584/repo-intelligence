# Working-set benchmark

- Generated at: 2026-04-13T09:37:12Z
- Repo: /root/studio/testing/repo-intelligence
- Case file: docs/eval_cases.change_radar.json
- Cases: 5
- Average Recall@5: 0.93
- Average Recall@10: 1.00

Working-set evaluation

Average Recall@5:  0.93
Average Recall@10: 1.00

- Repo status stale-index flow
  task: repo status stale index detection
  recall@5: 1.00
  recall@10: 1.00
  predicted: src/change_radar/types.py, tests/unit/test_repo_status.py, src/change_radar/index/service.py, src/change_radar/cli.py, src/change_radar/analysis/status.py, tests/integration/test_index_repository.py, src/change_radar/scanner/repo.py, src/change_radar/storage/sqlite.py, tests/unit/test_preflight.py, src/change_radar/mcp_server.py
  missing: none
- MCP repo-status tool
  task: mcp server repo status tool
  recall@5: 1.00
  recall@10: 1.00
  predicted: src/change_radar/mcp_server.py, tests/unit/test_mcp_server.py, tests/unit/test_repo_status.py, src/change_radar/analysis/status.py, src/change_radar/types.py, src/change_radar/cli.py, src/change_radar/scanner/repo.py, src/change_radar/index/service.py, src/change_radar/reports/markdown.py, tests/integration/test_index_repository.py
  missing: none
- Diff preflight test suggestions
  task: diff preflight test suggestions
  recall@5: 1.00
  recall@10: 1.00
  predicted: src/change_radar/types.py, src/change_radar/analysis/diff.py, tests/integration/test_diff_analysis.py, tests/unit/test_preflight.py, tests/integration/test_cli_json_output.py, src/change_radar/index/service.py, tests/unit/test_git_diff.py, tests/unit/test_scanner.py, tests/unit/test_task_ranking.py, tests/unit/test_prompt_pack.py
  missing: none
- Benchmark artifact generation
  task: benchmark artifact eval generation
  recall@5: 1.00
  recall@10: 1.00
  predicted: src/change_radar/evals/working_set.py, src/change_radar/reports/evals.py, tests/unit/test_working_set_eval.py, src/change_radar/cli.py, tests/integration/test_benchmark_working_set.py, src/change_radar/mcp_server.py, src/change_radar/index/service.py, src/change_radar/ranking/task.py, src/change_radar/serialization.py, src/change_radar/reports/markdown.py
  missing: none
- Python parser support
  task: python parser support
  recall@5: 0.67
  recall@10: 1.00
  predicted: src/change_radar/types.py, src/change_radar/parsers/python.py, tests/unit/test_python_parser.py, src/change_radar/index/service.py, src/change_radar/parsers/js_ts.py, tests/integration/test_index_repository.py, src/change_radar/scanner/repo.py, src/change_radar/parsers/service.py, tests/unit/test_js_ts_parser.py, src/change_radar/cli.py
  missing: none
