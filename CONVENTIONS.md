# Aider Conventions — Agent Loop Learning

## Purpose

This repo is a reference library for auditing, reviewing, and improving LLM-based agent systems. All best-practice docs are framework-agnostic.

## Aider usage patterns

### Review an agent design
Add the relevant files to context, then ask:
```
aider best-practices/01-multi-agent-orchestration.md \
      best-practices/02-worker-prompting.md \
      best-practices/03-context-and-memory.md \
      best-practices/04-tool-design.md \
      best-practices/05-verification-and-testing.md \
      best-practices/06-security-and-permissions.md \
      best-practices/07-prompt-engineering.md \
      best-practices/08-performance-and-startup.md \
      best-practices/09-benchmarks-reference.md \
      <your-agent-file>
```
Then: "Review my agent against the best-practice docs. Score each dimension ✅/⚠️/❌, list top 3 improvements with benchmark citations, and call out what's strong."

### Improve a component
Add only the relevant doc + your agent file:
```
aider best-practices/03-context-and-memory.md <your-agent-file>
```
Then: "Improve the memory handling based on the best-practice doc."

### Learn a topic
```
aider best-practices/06-security-and-permissions.md
```
Then: "Summarize the key security practices with benchmark citations."

## Review output format

When reviewing, always produce:

1. Scorecard table (8 dimensions, ✅/⚠️/❌)
2. Top 3 improvements: What / Why (cite benchmark) / How (sketch)
3. Strengths: 2–3 callouts

## Benchmark citation format

Always include source and date: e.g.
- "17.2× → 4.4× error amplification — Google DeepMind, Dec 2025"
- "Agentic RAG: +26% accuracy, 90% fewer tokens — Multiple, 2025"
- "73% of prod deployments vulnerable to injection — OWASP, 2025"

## Conventions for this repo

- Do not modify best-practice docs unless explicitly asked.
- Framework-agnostic by default. Note model-specific advice separately.
- Prefer minimal, targeted changes over new frameworks.
