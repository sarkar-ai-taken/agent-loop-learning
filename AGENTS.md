# Agent Loop Learning — OpenAI Codex CLI Context

This repo is a reference library and skill toolkit for auditing, reviewing, and improving LLM-based agent systems. The best-practice docs are framework-agnostic and apply to any agent built on any model.

## Best-practice docs

All reference material lives in `best-practices/`. Read the relevant doc(s) before answering any question about agent design.

| Keyword | File | Topic |
|---------|------|-------|
| orchestration | `best-practices/01-multi-agent-orchestration.md` | Coordinator/worker split, error amplification, concurrency |
| worker / prompting | `best-practices/02-worker-prompting.md` | Worker prompt structure, scaffold design, stop conditions |
| memory / context / rag | `best-practices/03-context-and-memory.md` | 6-layer context pipeline, 3-layer memory, agentic RAG |
| tools | `best-practices/04-tool-design.md` | Tool classification, 6 security properties, streaming |
| verification / testing | `best-practices/05-verification-and-testing.md` | Verification patterns, VCR fixtures, forced acknowledgment |
| security / permissions | `best-practices/06-security-and-permissions.md` | Denial circuit breakers, injection defense, token hygiene |
| prompt engineering | `best-practices/07-prompt-engineering.md` | Cache boundaries, prompt anchors, DO NOT comments |
| performance / startup | `best-practices/08-performance-and-startup.md` | Circuit breakers, diminishing-returns detector, wake lock |
| benchmarks | `best-practices/09-benchmarks-reference.md` | All benchmark numbers with caveats and sources |

## Workflows

### Review an agent design
When the user asks to "review", "audit", or "check" an agent:
1. **Explore the current repo first** — do not ask the user for anything. Search for agent-related files (`*agent*`, `*tool*`, `*prompt*`, `*chain*`, `*workflow*`), framework imports (`langchain`, `openai`, `anthropic`, `autogen`, `crewai`), system prompt definitions, and any `CLAUDE.md`, `AGENTS.md`, or README describing the architecture. Read the relevant files. Only ask if no agent code is found.
2. Read all 9 best-practice docs.
3. Score each dimension: ✅ Solid / ⚠️ Partial / ❌ Gap.
4. Return a scorecard table, top 3 prioritized improvements with benchmark citations, and what's already strong.

### Improve a specific component
When the user asks to "improve" or gives a topic keyword, **explore the current repo first** (same search as review above) before producing recommendations. Only ask if no agent code is found.
1. Read the relevant doc(s) from the table above.
2. Return improvement cards: current state → recommended change → benchmark justification → implementation sketch → effort (Low/Medium/High).
3. End with a Quick wins section (changes under 1 hour, high impact).

### Load a reference doc
When the user asks for "best practices on X":
1. Match X to the table above.
2. Read and return the doc with: key benchmarks table, 3–5 core principles, and self-check questions for the user to apply to their agent.

## Notes
- Always cite benchmark numbers (e.g. "centralized orchestration: 4.4× vs 17.2× error amplification — Google DeepMind, Dec 2025").
- If the user's agent uses a non-OpenAI model, note which practices are model-specific vs. universal.
- Prefer the simplest change that addresses a gap. Do not recommend adding frameworks unless necessary.
