# Evals

## Purpose

This file is the source of truth for whether Change Radar is becoming useful.

No ranking feature should be added without a task case here or a failure case discovered during dogfooding.

## Core metrics

- `Recall@5`
- `Recall@10`
- query latency
- index latency
- false positives in top 10
- subjective usefulness score from 1 to 5

## Good-enough targets

- medium repo indexing in under 60 seconds
- query latency under 3 seconds after indexing
- `Recall@10 >= 0.70` on curated tasks
- every returned file includes a clear explanation

## Test repo categories

1. small Node API
2. medium TypeScript backend
3. React frontend
4. monorepo-lite with shared package
5. one unfamiliar open-source repo

## Initial task cases

### Task 1

- Query: `add retry logic to payment API calls`
- Expected files:
  - payment service
  - HTTP client wrapper
  - payment route or handler
  - payment tests

### Task 2

- Query: `what breaks if I change auth token validation`
- Expected files:
  - auth middleware
  - login route
  - session or cookie logic
  - auth tests

### Task 3

- Query: `where should I add a billing endpoint`
- Expected files:
  - router
  - billing service
  - controller or handler
  - request/response types

### Task 4

- Query: `rename shared date formatting utility safely`
- Expected files:
  - utility module
  - reverse import callers
  - tests

## Evaluation routine

1. Run the command on each curated task.
2. Compare top 10 output against expected files.
3. Record misses and why they happened.
4. Only add heuristics that address an observed miss.

## Recording runs

Use the benchmark command when you want a saved artifact instead of terminal-only output:

```bash
uv run change-radar benchmark-working-set . --cases docs/eval_cases.example.json
```

This writes JSON and Markdown reports under `.change-radar/benchmarks/` by default.
