# Product

## Product name

Change Radar

## One-sentence pitch

Change Radar is a local-first repo-intelligence tool that tells a developer or AI coding assistant what files matter for a task, what may break if they change them, and what context to include before editing.

## Product direction

This repo's research converges on a specific wedge:

- not a general repo graph browser
- not a code generator
- not a GitNexus clone
- a preflight layer for safe AI-assisted edits

The strongest recurring insight from the research docs is that current AI tools are better at generating code than scoping code changes. The user pain is deciding:

- what files matter
- what else depends on the thing being changed
- what tests and nearby modules should be checked first

## Target user

- solo developers
- students working on medium-sized repos
- small teams using VS Code, Copilot, Codex, or Claude Code
- developers entering unfamiliar codebases and planning multi-file changes

## Primary jobs to be done

1. Before I edit code, tell me what files I should inspect or include in context.
2. Before I commit a change, tell me what may be affected downstream.
3. When I ask for a feature change, tell me where the work probably lives.

## Core workflow

1. User points Change Radar at a local repository.
2. Change Radar indexes files, symbols, import relationships, and selected Git metadata.
3. User asks one of three narrow questions:
   - what files matter for this task?
   - what depends on this file or symbol?
   - what is the likely impact of my current diff?
4. Change Radar returns:
   - a ranked working set
   - a blast-radius summary
   - suggested tests or nearby checks
   - a short explanation for each recommendation

## V1 scope

### Must have

- local-first CLI
- JS/TS repo support
- `.gitignore`-aware repo scanning
- Tree-sitter-based import and symbol extraction
- SQLite index
- deterministic ranking with explanations
- three commands:
  - `build-working-set`
  - `analyze-symbol`
  - `analyze-diff`

### Explicitly out of scope

- cloud sync
- multi-user auth
- full graph UI
- multi-repo intelligence
- full call-graph accuracy
- embeddings in v1
- full VS Code extension in v1

## Differentiation

Change Radar should be easy to explain in one sentence:

> Copilot is strong at coding but weak at scoping. Change Radar scopes the change first.

This keeps the product distinct from:

- GitNexus: broader repo graph and graph-RAG framing
- Cursor/Copilot: general-purpose AI editing experience
- Sourcegraph: enterprise code intelligence

## Product principles

- local-first by default
- deterministic before probabilistic
- explanations with every result
- one strong workflow before multiple weak ones
- visible user value over invisible infrastructure

## Success criteria

The product is useful when:

- the top 10 working-set results usually contain the files a human would actually inspect
- diff preflight catches nearby impact a user would otherwise forget
- the user can apply results immediately in an AI editing workflow
- the tool remains fast enough to run routinely, not just for demos
