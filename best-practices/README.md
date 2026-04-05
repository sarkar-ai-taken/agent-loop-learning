# Agent Best Practices — Reference Library

Compiled from: production agentic system design patterns + peer-reviewed research + industry benchmarks (April 2026).
Intended use: compare, audit, and improve any LLM-based agent system.

Each document includes a **Benchmarks at a Glance** table with sourced numbers.
For a complete benchmark dump with all numbers and caveats, see `09-benchmarks-reference.md`.

---

## Documents

| # | File | Category | Headline number |
|---|------|----------|----------------|
| 01 | [multi-agent-orchestration.md](./01-multi-agent-orchestration.md) | Architecture | 17.2× → 4.4× error amplification; proactive agent pattern; lifecycle hooks for hard enforcement |
| 02 | [worker-prompting.md](./02-worker-prompting.md) | Prompting | +8 pp scaffold gain; outcome-based stop conditions; reasoning depth framing |
| 03 | [context-and-memory.md](./03-context-and-memory.md) | Memory | 6-layer context pipeline; 3-layer memory (Index/Topic/Transcripts); 2-turn extraction efficiency |
| 04 | [tool-design.md](./04-tool-design.md) | Tools | 6 security classification properties per tool; streaming execution; sibling abort |
| 05 | [verification-and-testing.md](./05-verification-and-testing.md) | Quality | Verification = highest-leverage action; VCR fixture pattern; forced acknowledgment |
| 06 | [security-and-permissions.md](./06-security-and-permissions.md) | Security | Denial circuit breaker; anti-ptrace + token deletion; "may" not "will" warning language |
| 07 | [prompt-engineering.md](./07-prompt-engineering.md) | Prompting | Cache boundary; DANGEROUS_ uncached pattern; DO NOT comments as policy anchors |
| 08 | [performance-and-startup.md](./08-performance-and-startup.md) | Performance | Circuit breaker (3 failures max); diminishing-returns detector (500 token threshold); wake lock |
| 09 | [benchmarks-reference.md](./09-benchmarks-reference.md) | Reference | Complete numbered benchmark table with caveats and primary sources |

---

## Master Quick-Reference

| Claim | Number | Source |
|-------|--------|--------|
| Top SWE-bench Verified score | 81.42% | Claude Opus 4.6, April 2026 |
| Scaffold gain, same model | +8 pp (62.3% → 70.3%) | SWE-bench Feb 2025 |
| Devin original SWE-bench baseline | 13.86% | Cognition, Mar 2024 |
| GAIA human baseline | 92% | GAIA benchmark |
| WebArena top agent score | 61.7% | IBM CUGA, Feb 2025 |
| HumanEval frontier | ~93% | GPT-5.3 Codex, 2025–2026 |
| Multi-agent error amplification (unstructured) | 17.2× | Google DeepMind, Dec 2025 |
| Multi-agent error amplification (centralized) | 4.4× | Google DeepMind, Dec 2025 |
| Single-agent wins across all benchmarks | 64% of tasks | Princeton NLP |
| Multi-agent gain on parallelizable tasks | +81% | LangChain / Princeton |
| Multi-agent degradation on sequential tasks | −70% | LangChain / Princeton |
| Coordination benefit plateau | >4 agents | Multiple studies |
| Token usage explains performance variance | 80% | Google Research |
| Context rot — models tested | 18 LLMs (universal finding) | Chroma, 2025 |
| Context degradation onset | 50K tokens even with 1M window | Chroma / Morph |
| Lost-in-the-middle accuracy drop | ~30%+ | Liu et al., Stanford |
| Agentic RAG vs. traditional RAG | +26% accuracy, 90% fewer tokens | Multiple 2025 |
| Hindsight memory accuracy | 91.4% | Vectorize.io / Virginia Tech |
| Memory compression efficiency | 89–95% | Mem0 (arxiv 2504.19413) |
| Prompt injection in production deployments | 73% | OWASP audits, 2025 |
| Standard injection success rate | 50–84% | Security studies, 2025 |
| Defense reduces attack success | 73.2% → 8.7% | Security research |
| Self-Refine gain range | +5% to +40% | Madaan et al. |
| Reflexion GPT-4 coding improvement | 80% → 91% | Reflexion paper |
| Unguided self-reflection at frontier | +1.8 pp | 2025 refinement study |
| Guided external feedback | +80% within 5 turns | 2025 refinement study |
| Enterprise agent failure rate (year 1) | 73% | Cleanlab, 2025 |
| 20-step agent compounding (95% step rate) | 36% end-to-end success | Math |
| Single-agent latency | 2–4 s | Framework benchmarks, 2025 |
| Multi-agent latency | 8–15 s | Framework benchmarks, 2025 |
| Diminishing-returns threshold | 500 tokens/round × 3 rounds → stop early | Agentic loop design |
| Compaction failure circuit breaker | 3 consecutive failures → halt retries | Production incident data |
| Denial circuit breaker thresholds | 3 consecutive or 20 total → ask user | Classifier design |
| Max practical parallel agent sessions | 32 (coordination overhead beyond this) | Production agentic system design |
| Prompt cache stable prefix | 70–90% of system prompt cacheable | Production cost engineering |

---

## How to Use

**As an audit checklist:**
Load a document and ask: "Audit my agent's design against this. List any violations."

**As a design reference:**
Read the relevant section before designing a new agent component.

**As skill invocations:**
```
/best-practices orchestration  → 01-multi-agent-orchestration.md
/best-practices prompting      → 02-worker-prompting.md + 07-prompt-engineering.md
/best-practices memory         → 03-context-and-memory.md
/best-practices tools          → 04-tool-design.md
/best-practices verification   → 05-verification-and-testing.md
/best-practices security       → 06-security-and-permissions.md
/best-practices performance    → 08-performance-and-startup.md
/best-practices benchmarks     → 09-benchmarks-reference.md
```
