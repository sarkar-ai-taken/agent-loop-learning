# Windsurf Rules — Agent Loop Learning

This repo is a reference library for auditing and improving LLM-based agent systems. All best-practice docs are framework-agnostic.

## Core behavior

When the user asks about agent design, architecture, prompting, memory, tools, security, or performance:
1. Read the relevant best-practice doc from `best-practices/` (see mapping below).
2. Base your response on the doc content — cite benchmark numbers with source and date.
3. Keep recommendations minimal and targeted; prefer simple changes over new frameworks.

## Doc mapping

| Topic | File |
|-------|------|
| orchestration, multi-agent, coordinator/worker | `best-practices/01-multi-agent-orchestration.md` |
| worker prompts, scaffolding | `best-practices/02-worker-prompting.md` |
| memory, context, RAG | `best-practices/03-context-and-memory.md` |
| tools, function calling | `best-practices/04-tool-design.md` |
| verification, testing | `best-practices/05-verification-and-testing.md` |
| security, permissions, injection | `best-practices/06-security-and-permissions.md` |
| prompt engineering, caching, system prompts | `best-practices/07-prompt-engineering.md` |
| performance, startup, latency | `best-practices/08-performance-and-startup.md` |
| benchmarks, numbers | `best-practices/09-benchmarks-reference.md` |

## Workflows

**Review / audit**: Read all 9 docs → scorecard (✅/⚠️/❌ per dimension) → top 3 improvements with benchmark citations → strengths.

**Improve [component]**: Read relevant doc(s) → improvement cards (current state / change / benchmark / sketch / effort) → quick wins.

**Best practices on [topic]**: Read matched doc → key benchmarks + core principles + full doc + self-check questions.

## Benchmark citations to include

Always cite these when relevant:
- "17.2× → 4.4× error amplification: centralized vs unstructured orchestration (Google DeepMind, Dec 2025)"
- "Single-agent wins 64% of sequential tasks (Princeton NLP, 2025)"
- "Agentic RAG: +26% accuracy, 90% fewer tokens (Multiple, 2025)"
- "73% of prod deployments vulnerable to prompt injection (OWASP, 2025)"
- "Context degrades at 50K tokens even with 1M window (Chroma / Morph)"
- "Enterprise agent failure rate year 1: 73% (Cleanlab, 2025)"
