# agent-loop-learning

A reference library and skill toolkit for auditing, reviewing, and improving LLM-based agent systems.

**Framework-agnostic** — works with any agent framework: LangChain, LangGraph, AutoGen, CrewAI, OpenAI Agents SDK, Semantic Kernel, custom loops, or any other.

---

## What's included

### `best-practices/` — 9 reference documents

Compiled from production agentic system design patterns, peer-reviewed research, and industry benchmarks (April 2026). Each document includes benchmark numbers with primary sources.

| # | Document | Topic | Headline number |
|---|----------|-------|-----------------|
| 01 | [multi-agent-orchestration.md](./best-practices/01-multi-agent-orchestration.md) | Coordinator/worker split, concurrency, error amplification | 17.2× → 4.4× error amplification with centralized orchestration |
| 02 | [worker-prompting.md](./best-practices/02-worker-prompting.md) | Worker prompt structure, scaffold gain, stop conditions | +8 pp gain from agent engineering alone |
| 03 | [context-and-memory.md](./best-practices/03-context-and-memory.md) | 6-layer context pipeline, 3-layer memory, agentic RAG | +26% accuracy, 90% fewer tokens vs traditional RAG |
| 04 | [tool-design.md](./best-practices/04-tool-design.md) | Tool classification, 6 security properties, streaming | — |
| 05 | [verification-and-testing.md](./best-practices/05-verification-and-testing.md) | Verification patterns, VCR fixtures, forced acknowledgment | Reflexion: 80% → 91% coding improvement |
| 06 | [security-and-permissions.md](./best-practices/06-security-and-permissions.md) | Denial circuit breakers, prompt injection defense | 73% of prod deployments vulnerable; defense → 8.7% attack success |
| 07 | [prompt-engineering.md](./best-practices/07-prompt-engineering.md) | Cache boundaries, prompt anchors, DO NOT comments | 70–90% of system prompt is cacheable |
| 08 | [performance-and-startup.md](./best-practices/08-performance-and-startup.md) | Circuit breakers, diminishing-returns detector, wake lock | 3 failures max; 500 token/round threshold |
| 09 | [benchmarks-reference.md](./best-practices/09-benchmarks-reference.md) | Complete benchmark table with caveats and sources | All numbers |

---

## Skills (for Claude Code local agents)

Three slash commands live in `.claude/commands/`. When this repo is open in Claude Code, they are available immediately.

### `/review-agent`
Full structured audit of any agent design against all 9 best-practice dimensions.

```
/review-agent
# Then paste your agent code, design doc, or architecture description
```

Output: dimension-by-dimension scorecard (✅/⚠️/❌), top 3 prioritized improvements with benchmark justifications, and callouts for what's already strong.

---

### `/improve-agent [topic]`
Targeted, benchmark-backed improvement recommendations for a specific component or the full system.

```
/improve-agent                  # full system pass
/improve-agent orchestration    # focus on multi-agent design
/improve-agent memory           # focus on context & memory
/improve-agent security         # focus on security & permissions
/improve-agent performance      # focus on startup & latency
/improve-agent prompting        # focus on prompt structure
/improve-agent tools            # focus on tool design
/improve-agent verification     # focus on testing patterns
```

Output: prioritized improvement cards with current state, recommended change, benchmark justification, implementation sketch, and effort estimate. Plus a quick-wins section.

---

### `/best-practices [topic]`
Load and present a specific reference doc by keyword.

```
/best-practices orchestration
/best-practices memory
/best-practices security
/best-practices benchmarks
/best-practices all
```

Output: key benchmarks table, core principles summary, full document, and "how to apply" self-check questions.

---

## Quick start

```bash
git clone https://github.com/sarkar-ai-taken/agent-loop-learning
cd agent-loop-learning
# Open in Claude Code
claude .
```

Then run:
```
/review-agent
# Paste your agent code or design
```

---

## Key benchmarks at a glance

| Claim | Number | Source |
|-------|--------|--------|
| Multi-agent error amplification (unstructured) | 17.2× | Google DeepMind, Dec 2025 |
| Multi-agent error amplification (centralized) | 4.4× | Google DeepMind, Dec 2025 |
| Single-agent wins across all benchmarks | 64% of tasks | Princeton NLP, 2025 |
| Scaffold gain from agent engineering alone | +8 pp | SWE-bench, Feb 2025 |
| Agentic RAG vs traditional RAG | +26% accuracy, 90% fewer tokens | Multiple, 2025 |
| Prompt injection in production deployments | 73% vulnerable | OWASP audits, 2025 |
| Enterprise agent failure rate (year 1) | 73% | Cleanlab, 2025 |
| Context degradation onset | 50K tokens even with 1M window | Chroma / Morph |
| Top SWE-bench Verified score | 81.42% | Claude Opus 4.6, April 2026 |
