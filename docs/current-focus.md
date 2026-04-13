# Current Focus

## This week

1. Add benchmark runs and real fixture repos for `evaluate-working-set`.
2. Improve test suggestion heuristics for impacted dependents and common layouts.
3. Warn more aggressively when commands are using a stale or missing index.
4. Tighten MCP docs and examples around the current local-first workflow.
5. Only pursue Tree-sitter if evaluation misses show the regex extractor is the bottleneck.

## Definition of done for current focus

- `change-radar index <repo>` writes a consistent SQLite index
- `change-radar scan <repo>` is stable on fixture repos
- `change-radar analyze-diff <repo>` returns changed symbols and bounded downstream impact
- scanner, indexer, ranking, and diff tests pass
- at least one public-repo eval run is recorded in `docs/evals.md`
