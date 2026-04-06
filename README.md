# agent-loop-learning

A reference library and skill toolkit for auditing, reviewing, and improving LLM-based agent systems.

**Framework-agnostic** — works with Claude Code, Cursor, Windsurf, GitHub Copilot, OpenAI Codex CLI, Gemini CLI, Aider, Continue.dev, and any custom agent loop.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## What's included

### `best-practices/` — 9 reference documents

Compiled from production agentic system design patterns, peer-reviewed research, and industry benchmarks (April 2026). Each document includes benchmark numbers with primary sources.

| # | Document | Topic | Key number |
|---|----------|-------|------------|
| 01 | [multi-agent-orchestration.md](./best-practices/01-multi-agent-orchestration.md) | Coordinator/worker, concurrency, error amplification | 17.2× → 4.4× with centralized orchestration |
| 02 | [worker-prompting.md](./best-practices/02-worker-prompting.md) | Worker prompt structure, scaffold gain, stop conditions | +8 pp from agent engineering alone |
| 03 | [context-and-memory.md](./best-practices/03-context-and-memory.md) | 6-layer pipeline, 3-layer memory, agentic RAG | +26% accuracy, 90% fewer tokens vs traditional RAG |
| 04 | [tool-design.md](./best-practices/04-tool-design.md) | Tool classification, 6 security properties, streaming | — |
| 05 | [verification-and-testing.md](./best-practices/05-verification-and-testing.md) | Verification patterns, VCR fixtures, forced acknowledgment | Reflexion: 80% → 91% coding improvement |
| 06 | [security-and-permissions.md](./best-practices/06-security-and-permissions.md) | Denial circuit breakers, injection defense | 73% of prod deployments vulnerable → defense reduces to 8.7% |
| 07 | [prompt-engineering.md](./best-practices/07-prompt-engineering.md) | Cache boundaries, prompt anchors, DO NOT comments | 70–90% of system prompt cacheable |
| 08 | [performance-and-startup.md](./best-practices/08-performance-and-startup.md) | Circuit breakers, diminishing-returns detector | 3 failures max; 500 token/round threshold |
| 09 | [benchmarks-reference.md](./best-practices/09-benchmarks-reference.md) | All benchmark numbers with caveats and sources | All numbers |

---

## Agent integrations

### Three core workflows available in every agent

| Workflow | What it does |
|----------|-------------|
| **Review agent** | Full structured audit against all 9 dimensions. Scorecard (✅/⚠️/❌), top 3 improvements with benchmark citations, strengths. |
| **Improve agent** | Targeted recommendations for a specific component. Improvement cards: current state → change → benchmark → sketch → effort. Quick wins. |
| **Best practices** | Load a specific reference doc by topic. Key benchmarks + core principles + full doc + self-check questions. |

---

### Claude Code — `.claude/commands/`

```
/review-agent          → full audit against all 9 dimensions
/improve-agent [topic] → targeted improvement cards
/best-practices [topic] → load reference doc
```

Topics: `orchestration`, `memory`, `tools`, `security`, `performance`, `prompting`, `verification`, `benchmarks`

---

### Cursor — `.cursor/rules/`

Three `.mdc` rule files auto-loaded based on what the user asks:
- `review-agent.mdc` — triggers on "review / audit / check agent"
- `improve-agent.mdc` — triggers on "improve agent / improve [component]"
- `best-practices.mdc` — triggers on "best practices for [topic]"

---

### Windsurf — `.windsurf/rules.md`

Always-available context: doc mapping, review/improve/load workflows, key benchmarks to cite.

---

### GitHub Copilot — `.github/copilot-instructions.md`

Repo-wide instructions: when to read which doc, full review and improve workflows, citation rules.

---

### OpenAI Codex CLI — `AGENTS.md` + `codex/`

- `AGENTS.md` — top-level context loaded automatically by Codex CLI
- `codex/review-agent.md` — copy-paste system + user prompt for review
- `codex/improve-agent.md` — copy-paste system + user prompt for improvement

```bash
codex --full-auto "$(cat codex/review-agent.md)" -- your-agent-file.py
```

---

### Gemini CLI — `GEMINI.md`

Top-level context file loaded automatically by Gemini CLI. Includes doc mapping, workflows, and key benchmarks.

---

### Aider — `CONVENTIONS.md`

Convention file with context patterns, output format, and benchmark citation style.

```bash
# Review workflow
aider best-practices/*.md your-agent-file.py
# Then: "Review my agent against the best-practice docs"
```

---

### Continue.dev — `.continue/config.json`

Three custom slash commands pre-configured:

```
/review-agent [paste code]
/improve-agent [component keyword]
/best-practices [topic keyword]
```

Copy the `customCommands` array into your existing `.continue/config.json` if you already have one.

---

## Quick start

### Option A — Use directly in this repo

Clone and open in your agent. All commands and best-practice docs are already in place.

```bash
git clone https://github.com/sarkar-ai-taken/agent-loop-learning
cd agent-loop-learning

# Claude Code
claude .
# then run: /review-agent  →  paste your agent design

# Codex CLI
codex --full-auto "$(cat codex/review-agent.md)" -- your-agent.py

# Aider
aider best-practices/01-multi-agent-orchestration.md your-agent.py
# then: "Review my orchestration against the best-practice doc"
```

---

### Option B — Add skills to your own project

Copy two folders into your project root. The commands reference `best-practices/` by relative path, so both are required.

**Claude Code**
```bash
cp -r .claude/commands /your-project/.claude/commands
cp -r best-practices   /your-project/best-practices
```
Then open your project in Claude Code and run `/review-agent`.

**Cursor**
```bash
cp -r .cursor/rules  /your-project/.cursor/rules
cp -r best-practices /your-project/best-practices
```

**Windsurf**
```bash
cp .windsurf/rules.md /your-project/.windsurf/rules.md
cp -r best-practices  /your-project/best-practices
```

**GitHub Copilot**
```bash
cp .github/copilot-instructions.md /your-project/.github/copilot-instructions.md
cp -r best-practices                /your-project/best-practices
```

**Codex CLI**
```bash
cp AGENTS.md         /your-project/AGENTS.md
cp -r codex          /your-project/codex
cp -r best-practices /your-project/best-practices
```

**Gemini CLI**
```bash
cp GEMINI.md         /your-project/GEMINI.md
cp -r best-practices /your-project/best-practices
```

**Aider**
```bash
cp CONVENTIONS.md    /your-project/CONVENTIONS.md
cp -r best-practices /your-project/best-practices
```

**Continue.dev**
```bash
cp -r best-practices /your-project/best-practices
```
Then merge the `customCommands` array from `.continue/config.json` into your project's existing `.continue/config.json`.

---

## Key benchmarks

| Claim | Number | Source |
|-------|--------|--------|
| Multi-agent error amplification (unstructured) | 17.2× | Google DeepMind, Dec 2025 |
| Multi-agent error amplification (centralized) | 4.4× | Google DeepMind, Dec 2025 |
| Single-agent wins across benchmarks | 64% of tasks | Princeton NLP, 2025 |
| Scaffold gain from agent engineering alone | +8 pp | SWE-bench, Feb 2025 |
| Agentic RAG vs traditional RAG | +26% accuracy, 90% fewer tokens | Multiple, 2025 |
| Prompt injection in production deployments | 73% vulnerable | OWASP audits, 2025 |
| Defense reduces attack success | 73.2% → 8.7% | Security research |
| Enterprise agent failure rate (year 1) | 73% | Cleanlab, 2025 |
| Context degradation onset | 50K tokens even with 1M window | Chroma / Morph |
| Top SWE-bench Verified score | 81.42% | Claude Opus 4.6, April 2026 |

---

## License

[MIT](./LICENSE)
