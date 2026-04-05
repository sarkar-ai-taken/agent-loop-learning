# Agent Loop Learning — Project Context

This repo is a reference library and skill toolkit for auditing, reviewing, and improving LLM-based agent systems.

## What's here

- `best-practices/` — 9 curated documents covering orchestration, prompting, memory, tools, verification, security, performance, and benchmarks. Each doc includes benchmark numbers with primary sources.
- `.claude/commands/` — Slash-command skills for local Claude Code agents:
  - `/review-agent` — Audit any agent design against all best-practice docs
  - `/improve-agent` — Targeted improvement recommendations for a specific agent component
  - `/best-practices` — Load a specific best-practice doc by topic keyword

## How to use this repo

1. **As an audit**: open a design doc, run `/review-agent` to get a structured gap analysis
2. **As a learning loop**: run `/improve-agent <component>` to get concrete, benchmark-backed improvement suggestions
3. **As a reference**: run `/best-practices <topic>` to pull the relevant doc into context

## Best practices index

| # | File | Topic |
|---|------|-------|
| 01 | `best-practices/01-multi-agent-orchestration.md` | Coordinator/worker split, four-phase model, concurrency |
| 02 | `best-practices/02-worker-prompting.md` | Worker prompt structure, scaffold design, stop conditions |
| 03 | `best-practices/03-context-and-memory.md` | 6-layer context pipeline, 3-layer memory, RAG patterns |
| 04 | `best-practices/04-tool-design.md` | Tool classification, security properties, streaming |
| 05 | `best-practices/05-verification-and-testing.md` | Verification patterns, VCR fixtures, forced acknowledgment |
| 06 | `best-practices/06-security-and-permissions.md` | Denial circuit breakers, injection defense, token hygiene |
| 07 | `best-practices/07-prompt-engineering.md` | Cache boundaries, prompt anchors, system prompt structure |
| 08 | `best-practices/08-performance-and-startup.md` | Circuit breakers, diminishing-returns detector, wake lock |
| 09 | `best-practices/09-benchmarks-reference.md` | All benchmark numbers with caveats and sources |
