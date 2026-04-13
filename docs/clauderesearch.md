# Building a repo-intelligence tool that actually matters

**The biggest opportunity in developer tooling right now sits in a gap between enterprise code intelligence platforms (Sourcegraph at $49/user/month) and basic AI assistants that see only your open files.** A solo builder can fill this gap with a local-first code intelligence engine that gives AI assistants structural understanding of an entire codebase — and the demand is proven. GitNexus, built by a single developer, hit 25,000 GitHub stars after going viral in early 2026. Developers spend **58–70% of their time reading code**, not writing it, and the #1 complaint across every survey is outdated or missing documentation about how systems actually connect. The tools exist at the extremes — grep on one end, enterprise graph databases on the other — but nothing polished exists for the solo dev or small team who just wants to understand a repo fast and give their AI the context it needs.

---

## Developers lose hours daily to context-gathering, not coding

The pain is quantifiable. The Cortex 2024 State of Developer Productivity report found **48% of developers** without internal platforms cite "time to find context" as their primary productivity killer. Engineers estimate **5–15 hours per week lost** to unproductive work that better tooling could eliminate. New hires take **3–6 months** to reach full productivity, with **22% leaving within 90 days** without structured onboarding — each departure costing $65K–$260K.

The AI era has intensified these problems rather than solving them. While **82% of developers** now use AI coding tools daily, **66% say the biggest frustration is results that are "almost right, but not quite"** — a context problem, not a model problem. AI tools analyze functions in isolation, missing cross-file dependencies. Only **68.3% of AI-generated projects** execute successfully, and **67% of engineering leaders** report spending more time debugging AI code than writing it manually. The "Lost in the Middle" phenomenon means LLM performance degrades sharply when relevant code is buried in noise — making what you feed the model as important as which model you use.

The five sharpest pain points, ranked by developer frustration:

- **Context retrieval for AI assistants** — models see open files, not system architecture. Changing a function without knowing 47 others depend on it is the norm.
- **Onboarding to unfamiliar codebases** — no tool auto-generates "here's how this system works" from actual code structure and git history.
- **Blast radius blindness** — developers cannot easily answer "what breaks if I change this?" before making changes.
- **Knowledge entropy** — understanding is scattered across code, commits, PRs, docs, wikis, and Slack threads with no unified view.
- **Feature planning in complex repos** — "what files do I need to touch to add feature X?" has no good automated answer.

---

## The existing tool landscape has clear gaps at every tier

### Enterprise tools dominate but exclude individual developers

**Sourcegraph** was the gold standard for universal code search across massive codebases (54B+ lines indexed), but discontinued its free and Pro tiers in mid-2025. Only Cody Enterprise remains at **$49/user/month**, effectively abandoning individual developers. Their research (RecSys '24 paper) confirmed the core challenge: LLMs are not trained on your code, so context retrieval quality determines everything.

**Cursor** leads the AI editor market (**$29.3B valuation, $1B+ ARR**) with excellent codebase context indexing, multi-file editing via Composer, and background agents. But it requires switching editors entirely ($20/month Pro), and its context is proprietary — you cannot extend or customize what it sees.

**GitHub Copilot** has **76% developer name recognition** and deployment at 90% of Fortune 100 companies. At $10/month it is excellent value, but its multi-file editing and codebase understanding lag behind Cursor, and its agentic capabilities are still catching up.

### Open-source tools fill pieces but not the whole picture

**Aider** is the most architecturally instructive project for a solo builder. Its repo-map system uses tree-sitter to parse every file, extracts definitions and references, builds a directed graph, runs **PageRank** to identify the most important code, then generates a token-budgeted context summary — all with zero ML. This pure-heuristic approach is the gold standard for "how much can you achieve without embeddings."

**Continue.dev** (32.5K stars, Apache 2.0) provides the best reference architecture for a VS Code extension with codebase-aware context. It supports `@Codebase` semantic search, `@Code` ripgrep-based search, configurable embedding/reranking models, and MCP server support. Its modular architecture for swapping LLM and embedding providers is worth studying closely.

**GitNexus** proves the market exists for exactly the tool described in this brief. It parses codebases using tree-sitter into a knowledge graph mapping every dependency, call chain, and execution flow. Its Graph RAG claims **95% refactoring accuracy** versus 60–70% with vector-only approaches. Critical weaknesses: PolyForm Noncommercial license (not truly open source), no incremental indexing, and support for only ~8-9 languages.

**Greptile** pivoted from a general "repo understanding API" to AI code review, achieving an **82% bug catch rate** (41% higher than Cursor's 58%) by building a complete repository graph. They raised a $25M Series A in September 2025.

**CodeSee** (auto-generated code maps and PR visualization) was acquired by GitKraken in May 2024 and appears to have stalled as a standalone product. **Bloop** (AI code search, 9.5K stars) shut down entirely — "the vast majority are free users and we couldn't find a business model." **Swimm** (code-coupled documentation that auto-updates when code changes) occupies a unique niche but depends on team-wide adoption to deliver value.

### The gap map

| Need | Best existing tool | Gap |
|------|-------------------|-----|
| Full-repo AI context | Sourcegraph Cody | Enterprise-only pricing |
| Blast radius analysis | GitNexus | PolyForm license, no incremental updates |
| Onboarding intelligence | CodeScene (enterprise) | Nothing lightweight exists |
| Architecture visualization | CodeSee (acquired) | No maintained open alternative |
| Local-first code intelligence | Aider repo-map | CLI-only, no visualization, no search |
| "What files for this feature?" | Nothing | Completely unserved |
| Multi-signal context (code + git + docs) | Nothing | No tool unifies all signals |

---

## The technical building blocks are mature and well-documented

### AST parsing with tree-sitter is the foundation

Tree-sitter is an incremental parsing library that builds concrete syntax trees, efficiently updating them as code changes. It supports **40+ languages** through community-maintained grammars, handles malformed code gracefully (error-tolerant parsing), and is fast enough for real-time use. Python bindings are straightforward:

```python
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)
tree = parser.parse(bytes(source_code, "utf8"))
# Walk tree.root_node.children to extract functions, classes, imports
```

The key packages are `py-tree-sitter` (Python) and `tree-sitter` (npm). For symbol extraction, walk the AST to find `function_definition`, `class_definition`, and `import_statement` nodes, recording their names, line ranges, and parent scopes. Store these in SQLite for fast structured queries.

**LSP (Language Server Protocol)** complements tree-sitter by providing higher-level intelligence: go-to-definition, find-all-references, call hierarchy, and rename refactoring. Notable servers include pyright (Python), typescript-language-server, gopls (Go), and rust-analyzer. For a solo builder, tree-sitter is sufficient for v1 — LSP integration adds complexity but can be layered on later.

### Dependency graph construction follows a clear algorithm

The approach is deterministic and requires no ML:

1. Parse all source files with tree-sitter to extract function/class definitions and import statements
2. Build nodes (files, classes, functions) and directed edges (imports, calls, defines)
3. Store in NetworkX (Python) or a simple adjacency list in SQLite
4. Run graph algorithms: PageRank for importance, shortest path for relationship discovery, community detection (Louvain) for module clustering

Key tools for Python specifically include **PyCG** (state-of-the-art call graph generation), **pyan3** (static analysis for call dependencies with GraphViz output), and **libcst** (for more precise AST manipulation). For multi-language support, **Graphify** uses tree-sitter to extract structural nodes, call-graph edges, and import edges across 19 languages.

### Code embeddings: spend wisely, start cheap

The embedding landscape has matured significantly. Here is what matters for a solo builder:

| Model | Dimensions | Context | Cost | Best for |
|-------|-----------|---------|------|----------|
| **text-embedding-3-small** (OpenAI) | 1536 | 8K tokens | $0.02/1M tokens | Best cost-performance ratio |
| **Voyage Code-3** | 256–2048 | 32K tokens | $0.06/1M tokens | Highest code retrieval accuracy (97.3% MRR) |
| **all-MiniLM-L6-v2** | 384 | 512 tokens | Free (local) | Good enough for prototyping, runs on CPU |
| **Nomic Embed Code** | Variable | 2048 tokens | Free (Apache 2.0) | Best open-source code embedding |
| **Jina Code V2** | 768 | 8K tokens | Free (Apache 2.0) | Good balance of quality and size |

**CodeBERT** (Microsoft, 125M params) is frequently mentioned but performs poorly without fine-tuning (MRR ~0.117 zero-shot). Modern models like Voyage Code-3 outperform it by an order of magnitude. For a prototype, **all-MiniLM-L6-v2 runs locally with zero cost** and is sufficient to demonstrate semantic search. Upgrade to text-embedding-3-small or Voyage Code-3 when you need production quality.

**Chunking strategy matters**: Use tree-sitter to split code at function/class boundaries rather than arbitrary line counts. This preserves structural coherence and dramatically improves retrieval quality compared to naive 200-line windows.

### Hybrid retrieval is the consensus best practice

Every serious code search system — Cursor, Continue.dev, Sourcegraph — uses hybrid retrieval combining keyword and semantic search. The architecture:

1. **BM25 keyword search** (using SQLite FTS5 or the `bm25s` Python library) catches exact matches: function names, error codes, API paths
2. **Semantic embedding search** (using ChromaDB or FAISS) catches conceptual matches: "where is authentication handled?" when the code uses `verify_token`
3. **Reciprocal Rank Fusion** merges results: `score = Σ 1/(60 + rank_position)` — about 20 lines of Python
4. **Optional cross-encoder reranking** (`BAAI/bge-reranker-v2-m3`) improves precision on the top-20 merged results

Cursor's internal A/B testing found semantic search provides **12.5% higher accuracy** for answering questions, with gains up to **23.5%** on some models. The effect increases on larger codebases (1000+ files). But a key nuance: LLM-expanded grep (using an LLM to generate keywords before grepping) nearly matches embedding quality for many queries, showing the real competition is embedding search versus agentic grep, not embedding versus raw grep.

### MCP is the right integration layer — when you need it

Model Context Protocol (open-sourced by Anthropic, November 2024, now hosted by the Linux Foundation) standardizes how LLM applications connect to external tools. It uses JSON-RPC over stdio or HTTP/SSE, with three primitives: **Tools** (functions the LLM can call), **Resources** (data the app exposes), and **Prompts** (templates for workflows).

**Use MCP when** you want your tool to work with multiple AI clients (Claude Desktop, Cursor, VS Code Copilot) without building separate integrations for each. The official Python SDK (`pip install mcp`) and TypeScript SDK (`@modelcontextprotocol/sdk`) make server implementation straightforward.

**Skip MCP for v1** if you're building a standalone VS Code extension that talks directly to your own backend via HTTP. Add MCP as a second integration layer once the core engine works — it takes about a day to wrap an existing API as an MCP server, and it immediately makes your tool accessible to Claude Code and Cursor users.

---

## Heuristics handle 70% of the value; embeddings handle the last 30%

This is the most important architectural insight for a solo builder. **Most code intelligence features work well with pure deterministic heuristics**, and you should build these first.

### What works without any ML

**Symbol extraction** via tree-sitter AST parsing is deterministic, fast, and covers 40+ languages. **Import/dependency graphs** built by parsing import statements are fully reliable. **File importance ranking** via PageRank on the dependency graph — Aider's core innovation — requires zero ML and produces genuinely useful results. **Git churn and recency** signals (`git log` analysis) are deterministic and highly predictive: files changed most recently and frequently are the most likely to be relevant. **Complexity metrics** (cyclomatic complexity, nesting depth) computed from AST analysis are exact. **Blast radius** via transitive closure on the dependency graph is an algorithm, not a model.

This heuristic foundation is what Aider's repo-map uses, and it is sufficient to build an impressive, useful tool.

### Where ML genuinely helps

The semantic gap between natural language and code cannot be bridged by heuristics. "Where is authentication handled?" when the code uses `verify_token`, `login_handler`, and `session_middleware` requires embedding-based semantic search. **Code similarity beyond text matching** — two functions that do the same thing with different names and patterns — needs embeddings. **Cross-language search** (finding equivalent implementations in Python and JavaScript) fails entirely with text matching.

Martin Fowler's framework distinguishes "computational sensors" (deterministic: tests, linters, structural analysis — cheap and fast enough to run on every change) from "inferential sensors" (AI/ML: semantic analysis — slower, more expensive, non-deterministic). **Build the computational layer first, then add the inferential layer.**

---

## A realistic architecture for one person on Linux

### The stack

```
┌──────────────────────────────────────────────┐
│              VS Code Extension                │
│  TypeScript, Webview (React/Svelte), TreeView │
│  Chat UI, file rankings, graph visualization  │
└─────────────────────┬────────────────────────┘
                      │ HTTP (localhost:8000)
┌─────────────────────▼────────────────────────┐
│              FastAPI Backend                   │
│  /index → trigger repo parsing                │
│  /search → hybrid BM25 + semantic             │
│  /graph → dependency graph JSON               │
│  /impact → blast radius for a symbol          │
│  /rankings → PageRank file importance         │
└───┬──────────────┬───────────────┬───────────┘
    │              │               │
┌───▼────┐  ┌─────▼──────┐  ┌────▼────────┐
│ SQLite │  │  ChromaDB   │  │ Tree-sitter │
│ FTS5   │  │  (vectors)  │  │  (parsing)  │
│- files │  │- code chunks│  │- AST nodes  │
│- symbols│ │- embeddings │  │- defs/refs  │
│- deps  │  │- metadata   │  │             │
│- git   │  │             │  │             │
└────────┘  └─────────────┘  └─────────────┘
```

**FastAPI** is the clear backend choice: native async support (critical for concurrent file I/O and LLM calls), auto-generated Swagger docs (instant portfolio demo), and Pydantic validation. Performance is **5–7x Flask** at 15,000–20,000 req/s.

**SQLite** handles all structured data: file metadata, symbol tables, dependency edges, git statistics. Use **FTS5** (SQLite's built-in full-text search) for BM25 keyword search with zero additional infrastructure. This eliminates the need for a separate search engine.

**ChromaDB** stores vector embeddings for semantic search. It is embedded (no server process), has the simplest API of any vector DB, and performs well under 10M vectors. Its 2025 Rust rewrite improved speed 4x. For a prototype, start with `all-MiniLM-L6-v2` embeddings (free, runs on CPU). LanceDB is a strong alternative if you need disk-backed storage for larger repos.

**The VS Code extension** communicates with the FastAPI backend via HTTP on localhost. Use the Webview API for rich visualization (D3.js force-directed graphs, chat interfaces) and the TreeView API for sidebar file rankings. The `yo code` Yeoman generator scaffolds the project. The extension makes `fetch` calls to `localhost:8000` endpoints.

### Key repos to study and borrow from

| Project | What to learn | Stars |
|---------|--------------|-------|
| **Aider** (aider-chat/aider) | Repo-map algorithm, PageRank for code, tree-sitter usage | 30K+ |
| **Continue.dev** (continuedev/continue) | VS Code extension architecture, embedding pipeline, MCP integration | 32.5K |
| **GitNexus** | Knowledge graph construction, MCP server for code, blast radius | 25K+ |
| **RepoMapper MCP** (pdavis68/RepoMapper) | Standalone extraction of Aider's repo-map as MCP server | Smaller |
| **Emerge** (glato/emerge) | Dependency visualization, code metrics, Louvain modularity | ~2K |
| **Beacon** (Claude Code plugin) | Hybrid search implementation, grep interception with semantic fallback | Newer |

---

## The differentiation that matters: local-first context for AI

The strongest differentiation combines several underserved angles into one coherent product:

**"A local-first code intelligence engine that gives your AI assistant structural understanding of your entire codebase."** This means blast radius analysis ("what breaks if I change this?"), file importance ranking ("what are the most critical files?"), architecture visualization ("how does this system connect?"), and onboarding intelligence ("new to this repo — here's how it works") — all running locally, all available as context for Claude, Cursor, or Copilot via MCP.

This positioning works because: (1) Sourcegraph abandoned individual developers, leaving the market open; (2) GitNexus proves demand (25K stars from a single developer's project) but has licensing and technical limitations; (3) **92% of developers use AI tools** but the #1 frustration is insufficient context; (4) local-first is a genuine competitive advantage — "every time I mention 'runs locally,' developers get excited"; (5) the MCP ecosystem is exploding and needs quality servers.

The features with the highest wow-to-effort ratio are: a **live demo analyzing a well-known open-source repo** (zero effort for the viewer, maximum impact), a **"what files would I need to touch for feature X?"** query (natural language → ranked file list), a **blast radius visualization** showing a PR's downstream impact, and a **"bus factor" alert** highlighting files only understood by contributors who have left.

---

## Build phasing: from weekend to portfolio piece

### Weekend prototype (~20 hours)

Build a CLI that parses a JavaScript/TypeScript repo with tree-sitter, constructs an import dependency graph, runs PageRank, and outputs the **top 20 most important files** with a brief explanation of why each matters. Add entry-point detection (find `main`, `index`, `app`, route handlers). Store everything in SQLite. Produce a 30-second GIF demo analyzing a real open-source repo like Express.js or Fastify.

**This alone is impressive.** It demonstrates understanding of AST parsing, graph algorithms, and developer experience. No ML required.

### Two-week MVP (~60–80 hours)

Add a FastAPI backend and a basic VS Code extension with a TreeView sidebar showing ranked files and a simple Webview for blast radius visualization. Implement hybrid search: SQLite FTS5 for keywords plus ChromaDB with `all-MiniLM-L6-v2` for semantic queries. Add git history analysis: identify hot files (most frequently changed), detect files with a bus factor of one. Support Python alongside JS/TS.

The key architectural decision: **build as a CLI first, then wrap with the VS Code extension**. This gives you a CLI tool, an extension, and MCP server potential from the same core engine. Each layer is independently demo-able.

### Polished portfolio project (~6–8 weeks)

Add MCP server integration so Claude Desktop and Cursor can query your engine directly. Build interactive architecture visualization with D3.js force-directed graphs in the Webview — zoomable, filterable, with community detection coloring. Implement PR impact analysis: given a git diff, highlight all transitively affected files. Create an "onboarding mode" that auto-generates an architecture tour from code structure and git history. Support 3+ languages. Write a blog post explaining the technical decisions. Publish to the VS Code Marketplace.

**The polished version should ship with**: Docker Compose for one-command setup, a README with GIF demos and architecture diagrams, a project landing page on GitHub Pages, and the tool pre-loaded with analysis of a well-known open-source repo for instant demonstration.

### What to avoid

Do not try to support every language from day one — start with JS/TS and Python. Do not build a cloud backend — local-first is both simpler and a genuine differentiator. Do not over-engineer the graph database — SQLite with adjacency lists outperforms custom solutions for repos under 100K files. Do not spend more than one week on visualization polish before the core engine works reliably. The first version of DevUtils, which eventually reached $45K/month, was built in two weeks. **A well-executed focused tool with clean code is more impressive than a sprawling half-finished platform.**