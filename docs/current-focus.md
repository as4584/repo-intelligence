# Current Focus

## This week

1. Replace the lightweight JS/TS extractor with Tree-sitter-backed parsing.
2. Improve diff analysis beyond file-level import neighbors.
3. Add better test suggestion heuristics.
4. Add benchmark runs to `docs/evals.md`.
5. Start the MCP wrapper once core output stabilizes.

## Definition of done for current focus

- `change-radar index <repo>` writes a consistent SQLite index
- `change-radar scan <repo>` is stable on fixture repos
- `change-radar analyze-diff <repo>` returns changed symbols and likely impacted files
- scanner, indexer, ranking, and diff tests pass
