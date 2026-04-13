# Change Radar

`Change Radar` is a local-first repo-intelligence tool for safer AI-assisted edits.

The initial product direction in this repo is:

- build a deterministic working-set recommender for code changes
- show likely blast radius before edits
- stay local-first, explainable, and solo-builder friendly

This repository currently contains:

- research synthesis in `docs/`
- product source-of-truth docs
- the first Python project scaffold
- a working repo scanner and SQLite index bootstrap

## Current status

The codebase is in the first implementation phase:

- JS/TS repo scanning
- `.gitignore`-aware file discovery
- SQLite index initialization
- lightweight JS/TS structural extraction for imports and top-level symbols
- recent Git hotness signals for ranking
- CLI commands for `scan`, `index`, `build-working-set`, `build-prompt-pack`, `analyze-symbol`, and `analyze-diff`

The current structural extractor uses conservative regex heuristics so the core workflows
can progress without blocking on parser dependencies. Tree-sitter-backed parsing,
diff blast-radius analysis, and MCP tools are planned next.

## Quick start

```bash
uv sync
uv run change-radar scan .
uv run change-radar index .
uv run change-radar analyze-symbol . --symbol processPayment
uv run change-radar build-working-set . --task "add retry logic to payment flow"
uv run change-radar build-prompt-pack . --task "add retry logic to payment flow"
uv run change-radar analyze-diff .
uv run change-radar evaluate-working-set . --cases docs/eval_cases.example.json
uv run pytest
```

## Source of truth

Use these docs before making architectural changes:

- `docs/product.md`
- `docs/roadmap.md`
- `docs/evals.md`
- `docs/adr/`
