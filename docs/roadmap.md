# Roadmap

## Month 1: Build the spine

### Main goal

Create a usable local indexing pipeline and a trustworthy file discovery layer.

### Build

- repo scanner with `.gitignore` awareness
- JS/TS file filtering
- SQLite schema bootstrap
- initial CLI commands
- task eval list and benchmark fixture repos

### Learn

- repo scanning constraints
- subprocess-based Git integration
- SQLite schema design
- packaging a Python CLI

### End-of-month outcome

You can scan and index a real local repo and inspect a deterministic list of candidate files.

### Postpone

- Tree-sitter blast-radius logic
- MCP integration
- embeddings
- UI work

### Risks

- spending too long on parser setup
- overbuilding the schema before core workflows exist

### On-track check

- medium repo scans in under 60 seconds
- indexing is repeatable and deterministic
- test fixtures exist for scanner behavior

## Month 2: Deliver working-set value

### Main goal

Answer "what files matter for this task?" well enough to dogfood.

### Build

- structural extraction accuracy improvements
- symbol extraction
- import graph persistence
- candidate generation and ranking
- `build-working-set` command with explanations

### Learn

- parser tradeoffs and when syntax-aware parsing is worth it
- graph expansion heuristics
- ranking explanation design

### End-of-month outcome

Given a task like "add retry logic to payment calls," the tool returns a believable top file set with reasons.

### Postpone

- embeddings
- deep symbol resolution
- VS Code extension
- Tree-sitter unless eval misses clearly justify it

### Risks

- noisy ranking
- weak evaluation discipline
- spending too long on parser setup before it changes recall

### On-track check

- top 10 results contain most relevant files in curated test tasks

## Month 3: Deliver change preflight

### Main goal

Turn the tool into a real pre-edit guardrail.

### Build

- `git diff` parsing
- diff line to symbol mapping
- reverse dependency lookup
- test suggestion heuristics
- `analyze-symbol` and `analyze-diff`

### Learn

- diff parsing
- blast-radius heuristics
- failure analysis on false positives and false negatives

### End-of-month outcome

You can run Change Radar before a refactor and get actionable risk hints.

### Postpone

- graph visualization
- cloud features

### Risks

- pretending blast radius is more precise than it is
- building too much call-graph logic too soon

### On-track check

- the tool is useful on at least three real repos you care about

## Month 4: Productize and package

### Main goal

Make the project easy to run, demo, and extend.

### Build

- MCP wrapper
- better markdown and JSON reports
- stale-index detection
- install docs
- benchmark script
- demo scenarios and sample outputs

### Learn

- MCP server design
- packaging and release discipline
- portfolio-ready documentation

### End-of-month outcome

The project is a serious portfolio piece and a practical local tool.

### Postpone

- multi-language support beyond JS/TS and Python
- embeddings unless evaluation clearly justifies them

### Risks

- polishing output before core utility is solid
- adding infrastructure that is already good enough instead of improving evals

### On-track check

- a new user can install and run the tool in under 15 minutes
- you have a repeatable demo on a public repo
