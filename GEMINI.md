# Agent Loop Learning — Gemini CLI Context

This repo is a reference library and skill toolkit for auditing, reviewing, and improving LLM-based agent systems. All best-practice docs are framework-agnostic.

## Best-practice docs

All reference material lives in `best-practices/`. Read the relevant doc(s) before answering any question about agent design or architecture.

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

### "Review my agent" / "Audit this design"
1. Read all 9 best-practice docs.
2. Produce a dimension-by-dimension scorecard: ✅ Solid / ⚠️ Partial / ❌ Gap.
3. List top 3 prioritized improvements with benchmark justifications.
4. Call out what's already strong.

### "Improve [component]" / "How do I improve [X]?"
1. Read the relevant doc(s) from the table above based on the component keyword.
2. Produce improvement cards: current state → recommended change → benchmark citation → implementation sketch → effort.
3. End with a Quick wins section.

### "Best practices for [topic]"
1. Match the topic to the table above.
2. Read and present the doc: key benchmarks, core principles, full content, self-check questions.

## Key numbers to cite
- Error amplification: 17.2× (unstructured) vs 4.4× (centralized) — Google DeepMind, Dec 2025
- Single-agent wins 64% of sequential tasks — Princeton NLP, 2025
- Agentic RAG: +26% accuracy, 90% fewer tokens — Multiple, 2025
- 73% of prod deployments vulnerable to prompt injection — OWASP, 2025
- Context degradation onset at 50K tokens even with 1M window — Chroma / Morph
- Enterprise agent failure rate year 1: 73% — Cleanlab, 2025

## Notes
- Always cite benchmark numbers with source and date.
- Gemini-specific optimizations (context caching, grounding) should be called out separately from universal patterns.
- Do not recommend adding frameworks unless directly needed. Prefer minimal changes.
