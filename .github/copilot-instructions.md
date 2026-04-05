# GitHub Copilot Instructions — Agent Loop Learning

This repo is a reference library for auditing, reviewing, and improving LLM-based agent systems. The best-practice docs in `best-practices/` are framework-agnostic and apply to any agent on any model.

## When to use the best-practice docs

Always read the relevant doc before answering questions about:
- Agent architecture or design patterns
- Prompt structure, system prompts, or worker prompts
- Memory, context windows, or RAG pipelines
- Tool design or function calling
- Testing or verification strategies
- Security, permissions, or prompt injection
- Performance, latency, or startup behavior

## Doc → topic mapping

| If user asks about... | Read this file |
|----------------------|----------------|
| Multi-agent systems, orchestration, coordinator/worker | `best-practices/01-multi-agent-orchestration.md` |
| Worker prompts, scaffolding, stop conditions | `best-practices/02-worker-prompting.md` |
| Memory, context management, RAG | `best-practices/03-context-and-memory.md` |
| Tool design, function calling | `best-practices/04-tool-design.md` |
| Testing, verification, self-reflection | `best-practices/05-verification-and-testing.md` |
| Security, injection, permissions | `best-practices/06-security-and-permissions.md` |
| Prompt engineering, cache, system prompts | `best-practices/07-prompt-engineering.md` |
| Performance, startup, circuit breakers | `best-practices/08-performance-and-startup.md` |
| Benchmark numbers, citations | `best-practices/09-benchmarks-reference.md` |

## Review workflow

When asked to review or audit an agent design:
1. Read all 9 docs.
2. Score each dimension: ✅ Solid / ⚠️ Partial / ❌ Gap.
3. Return scorecard, top 3 prioritized improvements (with benchmark citations), and callouts for what's strong.

## Improve workflow

When asked to improve an agent or a component:
1. Read the relevant doc(s).
2. Return improvement cards: current state → recommended change → benchmark justification → implementation sketch → effort.
3. End with quick wins (under 1 hour, high impact).

## Rules
- Cite benchmark numbers with source: e.g. "4.4× vs 17.2× error amplification — Google DeepMind, Dec 2025".
- Note which recommendations are model-specific vs. universal.
- Prefer minimal, targeted changes over adding frameworks or dependencies.
