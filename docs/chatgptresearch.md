# Building a Focused Repo-Intelligence Tool for Developers

## Problem framing

Repo-intelligence tools exist because *understanding a codebase* is often the dominant cost of making changes safely. Classic maintenance research has repeatedly found program comprehension to be a major, time-consuming activity—sometimes reported as ~50–60% of maintenance effort/time. citeturn1search0turn1search20turn1search24

A “repo-intelligence” system, in practical terms, is any tool that precomputes or quickly infers **(a)** what’s in a repository (files, symbols, tests, configs), **(b)** how those things connect (imports, calls, references, data flow), and **(c)** how risky a change is (what else depends on it, what breaks first, what to test). Tools like GitNexus explicitly frame the problem as AI assistants making “blind edits” without understanding dependencies/call chains—and propose precomputing structural relationships at index time to fix that. citeturn3search3turn3search0turn3search21

Below is a grounded breakdown of the pain points you listed, from “human developer pain” to “AI coding assistant pain,” in the way a product engineer would frame scope.

**Onboarding pain (new dev → productive contributor)**  
The actual pain is not “reading code,” it’s building correct *mental models*: where responsibilities live, what patterns are standard, what is safe to change, and how runtime flows traverse modules. This maps directly to the high fraction of time spent understanding code before acting. citeturn1search0turn1search20  
A repo-intelligence wedge that helps onboarding usually wins by answering questions like: “Where is auth handled?” “What calls this?” “What’s the canonical pattern for error handling here?”—fast, with file-level grounding.

**Context-window pain (humans & LLMs have limited working memory)**  
Even with modern assistants, “what to include” is the struggle. GitHub Copilot guidance explicitly recommends providing helpful context (open relevant files, remove irrelevant context, restart chats when context becomes unhelpful). citeturn5search22turn5search2  
Inside the editor, Copilot supports explicit context attachment—files, folders, and symbols can be added via `#` mentions or drag-and-drop into chat. citeturn6search0turn6search12  
So the real opportunity: **help a developer (or agent) construct the *right working set*** deterministically and explainably.

**Repo navigation pain (finding the right place fast)**  
Most developers “navigate” by bouncing between symbol references and definitions. The Language Server Protocol formalizes these exact interactions (go-to definition, references, hover, etc.). citeturn1search2turn1search10turn1search18  
Repo-intelligence helps when navigation exceeds what LSP can do quickly (cross-language boundaries, config-to-code linkages, test mapping) or when you need *ranked* navigation (“top 5 files to read first to understand payment failures”).

**Unsafe edits / blast-radius pain (changes break things you didn’t realize existed)**  
Blast radius is basically “how many other things depend on the thing I’m touching?” GitNexus markets this explicitly: dependency/call-chain awareness before edits. citeturn3search3turn3search2  
For AI-assisted development, safety concerns become sharper because generated code quality and correctness are not guaranteed; empirical evaluations of AI code generators show meaningful gaps in correctness and other quality dimensions. citeturn3academia36  
In VS Code specifically, Copilot agents use multiple workspace tools (semantic search, grep, “usages”) to gather context iteratively, but that doesn’t eliminate the need for a *preflight* view of risk. citeturn6search2turn6search9

**Feature-planning pain (turn “idea/issue” into a safe plan)**  
Planning is often blocked on “Where do I make the change?” and “What else must change with it?” GitHub documentation on best practices for assigning tasks to agents explicitly calls out that broad, dependency-heavy refactors and legacy understanding can be poor fits for autonomous agents. citeturn5search30  
Separately, Microsoft’s “work context” direction for Copilot frames a gap: code is not enough—decisions live in docs, meetings, ownership contexts. citeturn3search9  
A focused repo-intelligence tool can help feature planning *without* needing to become a full project-management platform by staying anchored to repo facts: files, ownership signals, tests, change history.

**AI coding assistant pain (the agent needs the right tools + the right context + guardrails)**  
VS Code describes an explicit tool stack: semantic search, text search/grep, file search, and symbol “usages” tracing. citeturn6search2turn6search9  
Also, GitHub has written about “too many tools” hurting agent performance and the need for dynamic selection of a smaller toolset. citeturn3search16  
This is your wedge: **a small number of repo-specific, deterministic tools** that answer high-value questions like “what breaks if I change X?” or “what files should be in the working set for task Y?”—with explanations.

## Focused wedge ideas

Each wedge below is intentionally “small but sharp.” The goal is *one narrow repo problem* with a clean demo.

1) **Working-set recommender for Copilot Edits (task → files to include)**  
Who it helps: devs using multi-file edits (especially juniors). citeturn6search24turn6search11  
Exact problem: building the right set of files/symbols to include via `#` mentions/working set so edits stay scoped. citeturn6search0turn6search24  
Why easier than a full platform: you only need ranking + explanations, not a universal knowledge graph UI.  
Why impressive: deterministic “file shortlist + why” feels magical if it’s usually correct.  
Size: **MVP-sized** (can be hackathon-sized if you constrain to one language + import graph).

2) **Change preflight “blast radius” for the current Git diff**  
Who it helps: anyone before opening a PR; also AI-assisted workflows where you want guardrails. citeturn7search0turn6search9  
Exact problem: “I changed these lines—what else is likely impacted (callers, configs, tests)?”  
Why easier: input is bounded (changed files + symbols); you don’t need whole-repo semantics to start.  
Why impressive: produces a review-quality narrative plus “run these tests first.”  
Size: **hackathon-sized → MVP-sized** depending on depth.

3) **Onboarding “trace the flow” for one critical user journey** (e.g., login, checkout)  
Who it helps: new contributors and interns. citeturn1search0turn1search20  
Exact problem: follow a request from entrypoint → handlers → core logic → persistence.  
Why easier: pick one framework pattern (Express routes, FastAPI endpoints) and build only those edges.  
Why impressive: demoable as “type ‘login’ → get a readable map + top 8 files.”  
Size: **MVP-sized**.

4) **“Where is the pattern in *this* repo?” style matcher** (repo conventions finder)  
Who it helps: devs copying existing patterns (error handling, logging, retries). citeturn6search2turn6search0  
Exact problem: developers search keywords; they really want canonical examples.  
Why easier: start with grep + structural filters (Tree-sitter queries) rather than full semantic search. citeturn2search3turn0search2turn0search10  
Why impressive: returns a ranked “best 3 examples” + why they match.  
Size: **hackathon-sized**.

5) **Config-to-code linker (YAML/ENV → what code consumes this?)**  
Who it helps: devops-y teams; anyone touching CI, feature flags, env vars.  
Exact problem: config changes cause silent breakage; hard to locate consumers.  
Why easier: build a symbol index for env-var reads / config keys; no deep graph required.  
Why impressive: instant “if you change THIS var, these modules read it.”  
Size: **hackathon-sized** if limited to one config format.

6) **Test impact recommender (change → tests to run first)**  
Who it helps: teams with slow test suites.  
Exact problem: “What subset of tests covers this area?”  
Why easier: start heuristic (naming conventions + co-change history + import proximity).  
Why impressive: saves minutes/hours; very demoable.  
Size: **MVP-sized**.

7) **API surface map (endpoints → handlers → core modules)**  
Who it helps: backend devs.  
Exact problem: where to implement a new endpoint / modify response shape safely.  
Why easier: parse routes and map to handler symbols; ignore internal call graph initially.  
Why impressive: feels like “instant architecture map” but narrowly scoped.  
Size: **MVP-sized**.

8) **Rename/refactor guardrail assistant (symbol → references + risk flags)**  
Who it helps: juniors doing refactors; reviewers. citeturn1search2turn1search18  
Exact problem: refactors break downstream usage; you want “here are all references + related types.”  
Why easier: leverage language tooling (LSP-like capabilities) or conservative text+import heuristics first. citeturn1search2turn1search18  
Why impressive: “safe refactor checklist” is a strong demo.  
Size: **MVP-sized**.

9) **Repo-aware prompt pack generator (task → a compact, explainable context bundle)**  
Who it helps: anyone prompting Copilot/agents. citeturn6search2turn3academia35  
Exact problem: people don’t know what to paste/reference; agents waste time searching.  
Why easier: you don’t generate code; you generate *context*.  
Why impressive: improves downstream assistant results; matches research on repo-level prompt generation. citeturn3academia35  
Size: **hackathon-sized** if you skip embeddings; **MVP-sized** with hybrid retrieval.

10) **“Chokepoint detector” (what files are high-risk because many depend on them?)**  
Who it helps: maintainers and reviewers.  
Exact problem: identify files/modules where small edits cause large blast radius.  
Why easier: compute centrality over an import graph (not a full call graph).  
Why impressive: produces actionable “risk hotspots” and informs planning.  
Size: **hackathon-sized**.

## Technical building blocks

This section is deliberately practical: what you actually compute, what data you store, and how each term maps to code.

**Repo ingestion (turn a folder into an analyzable corpus)**  
At minimum: walk the directory tree, load text files, respect ignore rules, and record metadata (path, size, language guess, last modified). Many developer tools explicitly respect `.gitignore`; for example, ripgrep defaults to respecting `.gitignore` and skipping hidden/binary files, which is a good model for your indexer’s “what counts as repo content.” citeturn2search3

**File parsing (get structure, not just text)**  
Parsing means turning code text into a tree of syntactic constructs. Tree-sitter is widely used for this kind of tooling because it’s an incremental parsing library that produces a concrete syntax tree and can handle edits efficiently. citeturn0search2turn0search7turn0search18  
Practical implication: you can extract symbols and relationships in a language-aware way without building a compiler.

**ASTs (what they are, in plain terms)**  
An AST (abstract syntax tree) is a tree representation of code structure that typically removes some surface syntax details. In practice, you’ll often work with either an AST (compiler APIs) or a concrete syntax tree (Tree-sitter-style) depending on your tooling. Tree-sitter emphasizes editor-friendly parsing and robust results even with syntax errors. citeturn0search2turn0search18  
For an MVP, you don’t need “perfect AST fidelity.” You need consistent extraction of: functions/classes, imports, and identifiers.

**Symbol extraction (build a “repo dictionary”)**  
Symbols are named things: functions, classes, methods, constants, modules, routes, test cases. Symbol extraction means you create a table like:

- `UserService.validate` (kind=function, file=services/user.ts, range=lines 40–88)  
- `PaymentController` (kind=class, file=controllers/payment.ts, range=…)

If you plan to support multiple languages cheaply, Tree-sitter queries are a pragmatic approach. Tools like ast-grep explicitly build structural matching on top of Tree-sitter, showing this is a proven direction for “structure-aware” queries without full semantic compilation. citeturn0search10turn0search2

**Call graphs (who calls whom)**  
A call graph is a directed graph where nodes are callables (functions/methods) and edges represent calls. If you ever want deeper “blast radius,” call graphs are the backbone. CodeQL documentation shows how call graphs are represented for languages like Java/Kotlin, with explicit classes for callables and calls. citeturn1search5  
For a student MVP, full call graphs across languages are expensive—treat this as optional depth, not day-one scope.

**Import graphs (file/module dependencies)**  
Import graphs are easier and extremely useful. Node = file/module; edge = “A imports B.”  
Example (TypeScript): `src/routes/user.ts` imports `src/services/user.ts` → edge `routes/user.ts -> services/user.ts`.  
Import graphs power: working set recommendation, chokepoint detection, and first-pass blast radius (“neighbors of a changed file”).

**Dependency graphs (package/system-level dependencies)**  
This is “which packages depend on which.” In JS, it’s `package.json`; in Python, `pyproject.toml`; in monorepos it can be workspace manifests. Dependency graphs are valuable for “change might break builds” and “which package owns this surface,” but can be deferred until your wedge needs it.

**Language intelligence via LSP (outsourcing symbol resolution)**  
Instead of implementing symbol resolution yourself, you can leverage language servers. The LSP spec defines requests like “go to definition,” “find references,” “go to implementation.” citeturn1search2turn1search10  
This matters because “true blast radius” often requires symbol resolution (which `foo()` does this call refer to?), and LSP-backed data can get you partway there without writing compilers. citeturn1search18turn1search26

**Embeddings vs graph structure (two different signals)**  
Graphs encode **hard relationships** (imports, calls, references). Embeddings encode **soft semantic similarity** (“this file is about auth” even if it doesn’t contain the word “auth”).  
OpenAI’s embeddings docs define embeddings as vectors where distance reflects relatedness, commonly used for search and retrieval. citeturn2search2turn2search6  
In code, embeddings matter because developers ask *natural language* questions. CodeSearchNet is a major dataset/benchmark for semantic code search (NL → code) and highlights the challenge of bridging natural language and code structure. citeturn2search0turn2search4  
Pretrained models like CodeBERT were built specifically to learn representations across natural language and programming language and are commonly used in code search/summarization research. citeturn2search1turn2search9

**Retrieval (how you select the “right files” for a task)**  
Retrieval isn’t one thing; it’s usually a *pipeline*:

- **Lexical retrieval**: exact tokens via grep/ripgrep-style search (fast, high precision when you know names). citeturn2search3turn6search2  
- **Structural retrieval**: graph neighbors, symbol references, import distance. citeturn6search2turn1search2  
- **Semantic retrieval**: embeddings (“meaning match”), which Copilot describes as part of workspace understanding, via semantic search indexes. citeturn6search2turn5search32

A key research point: repo-level prompt construction can improve completion by selecting context across the repository (imports, parent classes, relevant files) even without access to model weights—this directly supports your “rank relevant files then assist the assistant” framing. citeturn3academia35

**Code summarization (compress files into stable, reusable context)**  
Summaries are context compression: “what does this file do” in ~5–15 lines. Summaries become valuable when context windows are constrained or sessions are long (and Copilot’s own tooling discusses context windows and compaction in long sessions). citeturn5search2turn5search9  
For MVP: summarize only *retrieved* files, not the whole repo.

**Change-impact analysis (blast radius in practice)**  
There are “levels”:

- Level 0: import neighbors + tests in same folder  
- Level 1: symbol reference search (find who calls/uses a symbol)  
- Level 2: resolved call graph / data flow graph (hard)  

CodeQL distinguishes AST structure from data flow graphs (data flow graphs model how data moves at runtime-ish, not just syntax). citeturn1search9turn1search1  
For your scope: Level 0–1 can be impressive if explainable.

**How MCP fits (and why it’s useful for you)**  
Model Context Protocol (MCP) is an open protocol to connect LLM clients to external tools/data sources. citeturn0search13turn0search32  
VS Code explicitly supports MCP servers and describes them as providers of tools/resources/prompts/apps; MCP configuration lives in `mcp.json` (workspace `.vscode/mcp.json` or user profile). citeturn4search3turn4search22  
VS Code’s AI extensibility overview draws a clean line:

- **Extension tools / chat participants** run in the extension host and can access VS Code APIs.  
- **MCP tools** run outside VS Code (local or remote) and can be reused across MCP clients but do not get VS Code API access. citeturn4search6turn4search0

This is ideal for a solo builder: build your intelligence engine as a local process first, then expose it via MCP into agent mode later.

**VS Code integration options (practical choices)**  
VS Code provides a Chat Participant API (custom assistants invoked by `@mention`) and Language Model/Tool APIs for AI-powered features. citeturn6search7turn4search4turn4search1  
Copilot also has explicit “working set” semantics in Copilot Edits: users specify a set of files to edit, and the tool emphasizes staying within that set. citeturn6search24turn6search9  
A strong wedge is to compute the working set deterministically, then let Copilot do generation.

**Git integration (high-signal metadata with almost no ML)**  
Git gives you:  
- **What changed** (`git diff`). citeturn7search0  
- **What changed historically and when** (`git log`). citeturn7search1turn7search15  
- **Who last touched lines** (`git blame`). citeturn7search2  
These signals are cheap and often correlate with risk (“hot files,” frequently changed modules, refactor-prone zones).

## Simplest possible architecture and concrete data flow

This is a “one motivated student” architecture optimized for Ubuntu, low cost, and demo value. It assumes your wedge is **preflight working set + blast radius** for safe AI edits.

**Minimal architecture (components you actually need)**

**Local indexer (CLI)**
- Input: repo root (local path), optionally current branch/diff.  
- Output: a small local index (SQLite or JSONL).  
- Jobs:
  - enumerate files (respect ignore rules) citeturn2search3  
  - parse for imports + symbol definitions (Tree-sitter) citeturn0search2turn0search7  
  - store a lightweight graph (import edges; optional symbol edges)

**Query layer**
- A library you can call from anywhere: `rank_files(task_text, changed_files, focused_symbol)`  
- Produces: ranked list of files + “why” traces (explainability)

**Integration surface (pick one for MVP)**
- **Option A: MCP server** that wraps your query layer and exposes 2–4 tools. VS Code supports adding MCP servers (local or remote) and using them in agent mode. citeturn4search3turn4search6turn4search22  
- **Option B: VS Code extension command** (“Analyze blast radius”) that prints results and copies a “prompt pack” to clipboard.

For hackathon speed, Option A is surprisingly clean: MCP is designed to connect tools to agent workflows, and VS Code has a developer guide specifically for MCP servers. citeturn4search0turn4search6

**Local-first vs cloud tradeoffs (what matters early)**  
Local-first wins early because:
- no hosting cost  
- easier privacy story (code stays on the machine)  
- simpler demo (“clone repo → run indexer → ask Copilot using my MCP tools”) citeturn4search3turn4search7  

Cloud becomes attractive later mainly for huge repos and team sharing, but it’s a scope bomb for a solo MVP (auth, storage, multi-tenant security, indexing infra).

**What to hardcode at first (and why it’s okay)**  
Hardcode to reduce surface area:
- Support **1–2 languages** you personally use (e.g., TypeScript + Python). Tree-sitter supports many languages, but multi-language correctness is where time disappears. citeturn0search2turn0search7  
- Implement **import graph + symbol definitions** only; skip full call graph.  
- Provide **3 tools max** (see below) to align with “less tools can be better.” citeturn3search16

**What to defer (common scope creep)**  
Defer:
- full semantic indexing & embeddings store  
- cross-repo indexing  
- rich graph visualization UI  
- IDE-agnostic “universal platform” packaging

You can still be impressive without these if your wedge nails one pain point.

**Data flow (repo → index → query → results)**
1) **Repo input**: local filesystem path + git metadata (current branch, uncommitted diff). citeturn7search0turn7search18  
2) **Indexing**
   - file scan (apply ignore rules) citeturn2search3  
   - parse each code file → extract:
     - imports (file A imports B)
     - symbol definitions (function/class names + locations) citeturn0search2turn0search7  
   - persist:
     - `files` table (path, lang, size, modified time)
     - `imports` edges
     - `symbols` table  
3) **Task input**
   - user text (“add retry logic to payment calls”)  
   - optional: focused file/symbol (current editor selection)  
   - optional: git diff changed files/symbols citeturn6search11turn7search0  
4) **Retrieval/ranking**
   - candidates from lexical search + symbol match  
   - expand via import-neighborhood BFS  
   - apply weights (recency, centrality, test proximity)  
5) **Output**
   - “Working set” list (top N files) + reasons  
   - “Blast radius” narrative (what depends on what)  
   - “Prompt pack” snippet that tells Copilot which files to include via `#file` context or working set citeturn6search0turn6search24turn6search9  

## Algorithms and heuristics you can use before real ML

Start with “boring” heuristics because (a) they’re fast, (b) they’re explainable, and (c) they often beat naive embedding retrieval on small repos where names are meaningful.

**Heuristics that often work shockingly well**
- **Symbol name match > keyword match**: If the task mentions “PaymentService” or “validateUser,” prioritize files defining that symbol (from your symbols table).  
- **Import graph distance**: If a changed file imports `X`, `X` is higher priority than a random semantic match. (“Closest neighbors first.”)  
- **Changed-file neighbors**: For a diff touching `A.ts`, include:
  - direct imports of `A.ts`  
  - files that import `A.ts` (reverse edges)  
  - tests with similar basename (`A.test.ts`, `test_A.py`)  
- **Git recency and hotness**: If a file has frequent recent commits, it’s both (a) likely relevant and (b) potentially risky (high churn). Use `git log` output at file granularity. citeturn7search1turn7search15  
- **Ownership/risk signals**: `git blame` hotspots (many authors/touch points) can indicate fragile zones. citeturn7search2  
- **File centrality (import graph choke points)**: compute a simple centrality score on import graph to flag “core” modules (useful for risk warnings).  
- **Path priors**: `src/routes/*` matters for endpoint tasks; `db/*` matters for schema tasks; `docs/*` matters for planning tasks. This is biased but explainable.

**Where embeddings/ML actually become useful (and why)**
Embeddings shine when the question is **natural language** and repo naming is inconsistent: “payment failures,” “rate limiting,” “authentication,” “retry,” etc. Copilot itself describes semantic search as matching meaning rather than exact keywords and notes it relies on workspace indexes. citeturn6search2turn5search32  
Research benchmarks like CodeSearchNet exist precisely because NL→code retrieval is hard and benefits from learned representations. citeturn2search0turn2search4  
If you add embeddings later, the clean approach is **hybrid retrieval**:
- candidates from heuristics + lexical search  
- rerank with embeddings similarity  
- then expand with graph neighborhood  
This is aligned with retrieval-augmented generation ideas: retrieve relevant support docs/code and then generate grounded output. citeturn1search3turn1search11turn2search2

## MVP recommendation for your level

You asked for something ambitious but finishable, practical, explainable, demoable, and original in angle.

### Best MVP concept

**“Copilot Change Radar”: a preflight working-set + blast-radius explainer for the current change/task.**

Core idea: before you (or Copilot) edits across files, your tool computes:
- the **best working set** (top 8–15 files)  
- the **probable blast radius** (direct dependents + neighbor modules + likely tests)  
- a **copy-pasteable prompt pack** that attaches those files via `#file`/working set conventions

Why this fits the environment you care about:
- VS Code already has workflows for *explicit* context and working sets (chat context attachments; Copilot Edits working set). citeturn6search0turn6search24turn6search11  
- Copilot agent mode describes automatic context gathering via tools; you’re building a deterministic “fast lane” for the most important context + risk explanations. citeturn6search2turn6search9  
- It’s local-first and cheap: Tree-sitter + Git metadata + simple ranking. citeturn0search2turn7search0turn7search1

### Best stack for this MVP (Ubuntu-friendly, low-cost)

- **Language**: TypeScript + Node.js (keeps VS Code integration and indexer in one ecosystem).  
- **Parsing**: Tree-sitter (node bindings) for imports + symbol definitions. citeturn0search2turn0search7  
- **Storage**: SQLite (simple tables) or even JSONL for prototype.  
- **Git metadata**: shell out to `git diff`, `git log`, `git blame` as needed. citeturn7search0turn7search1turn7search2  
- **Integration** (choose one):
  - MCP server v1 (fast hackathon demo in agent mode) citeturn4search0turn4search3turn4search22  
  - or VS Code extension command palette + webview/markdown output

### Narrowest feature set worth shipping

- Support 1 language well (TypeScript *or* Python).  
- Build import graph + symbol definitions table. citeturn0search2turn0search7  
- Implement 3 user-facing actions only:
  1) **Analyze current diff** → blast radius + tests suggestions  
  2) **Analyze current file/symbol** → “who depends on this”  
  3) **Build working set for task text** → ranked file list + “why”

Everything else is optional.

### Two-minute demo flow (very demoable)

1) Open a medium repo. Make a small change in a core function.  
2) Run `Change Radar: Analyze diff`.  
3) Show output:
   - “Top impacted files” (reverse import edges + symbol name hits)  
   - “Suggested working set” (8–12 files)  
   - “Suggested tests” (naming + proximity + co-change heuristics)  
4) Click “Copy prompt pack,” open Copilot Edits, paste prompt, and add the recommended files to the working set using the `#` context picker. citeturn6search0turn6search24turn6search9  
5) Let Copilot propose changes constrained to the working set (your tool made that set intelligently). citeturn6search24turn6search9

### Clearest way to explain value

“Copilot is strong at coding, but weak at *scoping*. This tool scopes the change—what to include and what could break—so edits stay safe and reviewable.”

## Build plan, common traps, and differentiation

### Build plan in phases

**Phase one: prototype (1–3 days of focused work)**
- Build: CLI that
  - scans repo
  - extracts imports + symbol definitions
  - prints a ranked file list for a given query  
- Learn: Tree-sitter extraction patterns; stable file filtering; basic ranking. citeturn0search2turn0search7turn2search3  
- Postpone: MCP/VS Code UI; embeddings; call graph.

**Phase two: usable MVP (1–2 weeks part-time)**
- Build:
  - persist index (SQLite/JSON)
  - “analyze diff” using `git diff --name-only` + optional symbol extraction
  - reverse import graph lookup
  - generate prompt pack + reasons  
- Learn: turning git history into risk signals; designing explainable scoring. citeturn7search0turn7search1  
- Postpone: deep symbol resolution; fancy UI.

**Phase three: polished demo (2–5 days)**
- Build:
  - MCP server wrapper exposing 2–3 tools (or a VS Code command)
  - tight output formatting (markdown), stable caching, “index stale” detection  
- Learn: tool ergonomics in agent workflows (and keeping tool count small). citeturn3search16turn4search3turn4search22  
- Postpone: generalized multi-language support.

**Optional future phase**
- Add:
  - hybrid retrieval (embeddings rerank) citeturn2search2turn2search0  
  - LSP-backed “find references” for more accurate blast radius citeturn1search2turn1search18  
  - path-specific instruction generation (integrate with `.github` instructions files), if you want to influence assistant behavior consistently. citeturn5search21turn6search10turn6search17

### Risks and traps beginners hit

**Over-engineering the index**  
Trying to build a universal knowledge graph across all languages is how you accidentally rebuild a platform. Your wedge should constrain what edges you compute (imports + symbols are enough early). citeturn3search16turn0search2

**Indexing too much (and making the system slow)**  
Users will forgive “only TypeScript” in an MVP; they won’t forgive a tool that takes 5 minutes to run or breaks on syntax errors. Tree-sitter’s robustness is part of why it’s used for editor tooling. citeturn0search2turn0search18

**Weak retrieval quality because you skipped explainability**  
The secret isn’t “use embeddings.” It’s: always show *why* a file was selected (“imports changed file,” “defines symbol,” “recently edited,” etc.). This also makes debugging your ranking possible.

**Bad UX caused by fighting existing workflows**  
VS Code already supports context attachment (`#` mentions/drag-drop) and has working set semantics in Copilot Edits. If your tool outputs in those terms, it feels native instead of “another dashboard.” citeturn6search0turn6search24turn6search11

**Building infrastructure nobody understands**  
Keep the core deterministic and inspectable (SQLite tables, printed edges). Save complicated distributed systems for later.

**Accidentally cloning instead of differentiating**  
If your product is “a repo knowledge graph,” it will be compared directly to GitNexus-like systems. If your product is “the best working-set + change-risk preflight for Copilot Edits,” you’re playing a different game.

### Ten differentiation angles that feel original and honest

1) **Preflight, not platform**: “risk + scope before edits,” not “browse a full knowledge graph.”  
2) **Working-set first**: optimize for selecting the right files to include in AI-assisted multi-file edits. citeturn6search24turn6search9  
3) **Explainable scores**: every recommendation includes a short causal trace (“import distance 1,” “reverse import count 12,” “recent churn”).  
4) **Diff-first intelligence**: start from *what changed* (bounded input) rather than indexing everything equally. citeturn7search0  
5) **Small-repo excellence**: tuned for 5–200k LOC repos where naming conventions and import graphs are strong signals.  
6) **Low tool count by design**: expose 2–3 tools only, aligning with the idea that too many tools can degrade agent performance. citeturn3search16  
7) **“Risk hotspots” lens**: find chokepoints (central modules) and warn explicitly.  
8) **Config + code linkage**: treat config changes as first-class blast radius (where many tools ignore config).  
9) **Offline-capable mode**: no external calls needed to get value (parsing + git + graphs). citeturn0search2turn7search1  
10) **Prompt-pack output format**: your “product” is a context bundle that makes downstream assistants perform better—supported by repo-level prompt generation research. citeturn3academia35turn6search2

## What you should build first

**Single best focused version for you to build first**  
**Copilot Change Radar**: a local-first “analyze diff / analyze symbol” tool that outputs (1) blast radius, (2) recommended working set (files + symbols), and (3) a copy-paste prompt pack formatted for VS Code chat context attachments.

**One-sentence pitch**  
“Before you (or Copilot) touch a file, Change Radar tells you what else it affects and gives you the exact working set to keep multi-file edits safe and reviewable.”

**Starter repo structure**

```text
copilot-change-radar/
  README.md
  LICENSE
  package.json
  pnpm-lock.yaml

  apps/
    indexer-cli/
      src/
        main.ts
        scan/
          walkRepo.ts
          ignore.ts
        parse/
          detectLanguage.ts
          treesitter/
            initParsers.ts
            extractImports.ts
            extractSymbols.ts
        git/
          diff.ts
          log.ts
          blame.ts
        graph/
          buildImportGraph.ts
          reverseIndex.ts
        rank/
          scoreCandidates.ts
          explainScore.ts
        output/
          formatMarkdown.ts
          formatPromptPack.ts

    mcp-server/
      src/
        server.ts
        tools/
          analyzeDiff.ts
          analyzeSymbol.ts
          buildWorkingSet.ts
        schema/
          types.ts

  packages/
    core/
      src/
        types.ts
        storage/
          sqlite.ts
          schema.sql
        retrieval/
          lexical.ts
          graphExpand.ts

  examples/
    vscode/
      mcp.json.example
      demo-script.md
```