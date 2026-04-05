---
name: benchmarks-reference
description: Complete benchmark reference for AI agent systems — SWE-bench, GAIA, WebArena, multi-agent comparisons, context rot, memory augmentation, security, and self-correction. Use this to back up any agent design claim.
type: reference
---

# Agent Benchmarks Reference (2025–2026)

> All numbers sourced from primary leaderboards, peer-reviewed studies, and industry reports.
> See caveats section before citing.

---

## 1. SWE-bench: Coding Agent Performance

SWE-bench tests agents against 2,294 real GitHub issues requiring autonomous code changes and test passing. **SWE-bench Verified** (500 tasks, human-validated) is the most reliable comparison point. **SWE-bench Pro** is a harder variant.

### Performance Progression

| System | Score | Date |
|--------|-------|------|
| Devin (Cognition, original) | 13.86% | Mar 2024 — the starting baseline |
| Claude 3.5 Sonnet | 49.0% | Jan 2025 |
| Claude 3.7 Sonnet (no scaffold) | 62.3% | Feb 2025 |
| Claude 3.7 Sonnet (with scaffold) | 70.3% | Feb 2025 — +8pp from scaffolding alone |
| Claude Opus 4.1 | 74.5% | Aug 2025 |
| Claude Sonnet 4.5 | 77.2% | Oct 2025 |
| Claude Opus 4.5 | **80.9%** | Nov 2025 — first model to exceed 80% |
| Claude Opus 4.6 (with prompt mod) | **81.42%** | April 2026 — current top |

### Early 2026 Leaderboard

| System | SWE-bench Verified |
|--------|--------------------|
| Claude Opus 4.6 | 81.42% |
| Claude Opus 4.5 + Live-SWE-agent | 79.2% |
| GPT-5.4 | 78.20% |
| GPT-5.3 Codex | 78.00% |
| Gemini 3.1 Pro Preview | 78.80% |

**Key insight:** The 8 percentage point gap between Claude 3.7 Sonnet with and without scaffolding shows that agent engineering (tool design, context management, retry logic) is as important as the underlying model.

**Leaderboards:**
- [swebench.com](https://www.swebench.com/) — official
- [llm-stats.com](https://llm-stats.com/benchmarks/swe-bench-verified)
- [Epoch AI tracker](https://epoch.ai/benchmarks/swe-bench-verified/)
- [Scale Labs SWE-bench Pro](https://labs.scale.com/leaderboard/swe_bench_pro_public)

---

## 2. GAIA: General AI Assistants

Tests 466 real-world tasks requiring web search, document reading, multi-step reasoning, and tool chaining. Three difficulty levels.

| System | Score |
|--------|-------|
| Human baseline | 92% |
| GPT-4 with plugins (first attempt) | 15% |
| H2O.ai agent (Claude 3.7 Sonnet) — Level 1 | 86% |
| H2O.ai agent (Claude 3.7 Sonnet) — overall | ~74% |
| Current top agents — Level 1 | >85% |
| Current top agents — overall | ~90% |

**Leaderboard:** [HAL Princeton](https://hal.cs.princeton.edu/gaia) | [Hugging Face](https://huggingface.co/spaces/gaia-benchmark/leaderboard)

---

## 3. WebArena: Autonomous Web Navigation

| System | Score | Date |
|--------|-------|------|
| Baseline agents | ~14% | 2022 |
| IBM CUGA (single agent) | **61.7%** | Feb 2025 — record |

The jump from 14% to 62% in two years came from a converging architectural pattern: Planner + specialized Executor + structured Memory.

---

## 4. HumanEval: Python Programming

| System | Score |
|--------|-------|
| Current frontier models (GPT-5.3 Codex et al.) | ~93% |

Largely saturated at the frontier. Training contamination is well-documented for this benchmark. Use SWE-bench Verified for more meaningful comparisons.

---

## 5. AgentBench: Multi-Environment

8 environments: OS, Database, Knowledge Graph, Digital Card Game, Lateral Thinking Puzzles, Householding, Web Shopping, Web Browsing.

- GPT-4: 78% success on Householding; best on 6/8 datasets.
- Open-source <70B models: large performance gap vs. frontier.
- Key obstacles: long-term reasoning, decision-making, instruction following.

**Holistic leaderboard:** [HAL — hal.cs.princeton.edu](https://hal.cs.princeton.edu/)

---

## 6. Multi-Agent vs. Single-Agent

| Metric | Number | Source |
|--------|--------|--------|
| Single-agent beats multi-agent | 64% of benchmarked tasks | Princeton NLP, 2025 |
| Multi-agent gain on parallelizable tasks (Finance-Agent) | **+81%** | LangChain / Princeton, 2025 |
| Multi-agent degradation on sequential tasks (PlanCraft) | **-70%** | LangChain / Princeton, 2025 |
| Error amplification — unstructured "bag of agents" | **17.2×** | Google DeepMind, Dec 2025 |
| Error amplification — centralized orchestration | **4.4×** | Google DeepMind, Dec 2025 |
| Coordination gains plateau above | **4 agents** | Multiple studies, 2025 |
| MIT study: centralized multi-agent improvement | **+80.8%** over single-agent | MIT, Dec 2025 |
| Token usage explains BrowseComp variance | **80%** | Google Research, 2025 |
| Single-agent latency | 2–4 seconds | Framework benchmarks, 2025 |
| Multi-agent latency | 8–15 seconds | Framework benchmarks, 2025 |

**Key insight:** Multi-agent wins on parallelizable tasks; single-agent wins on 64% of sequential tasks. Centralized orchestration with a coordinator reduces error amplification by 4× vs. an unstructured agent network.

**Sources:**
- [LangChain: Benchmarking Multi-Agent Architectures](https://blog.langchain.com/benchmarking-multi-agent-architectures/)
- [Google Research: Towards a Science of Scaling Agent Systems](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/)
- [The 17× Error Trap — Towards Data Science](https://towardsdatascience.com/why-your-multi-agent-system-is-failing-escaping-the-17x-error-trap-of-the-bag-of-agents/)
- [arxiv 2505.18286: Single-agent or Multi-agent? Why Not Both?](https://arxiv.org/abs/2505.18286)

---

## 7. Context Window / Context Rot

| Metric | Number | Source |
|--------|--------|--------|
| Models studied | 18 frontier LLMs | Chroma (Hong et al., 2025) |
| Context rot onset | Every model tested | Chroma, 2025 — universal, not model-specific |
| Degradation despite large window | At 50K tokens even with 1M window | Chroma / Morph, 2025 |
| Effective range — Gemini 2.5 Pro, GPT-5 | ~200K tokens | Benchmark data, early 2026 |
| Effective range — Claude Sonnet 4 (Thinking) | ~60K–120K tokens | Benchmark data, early 2026 |
| General rule | Degrade at 30–50% of advertised window | Empirical consensus |
| Lost-in-the-middle accuracy drop | 30%+ for middle content | Liu et al. (Stanford), 2024 |
| 20-step agent at 95% per-step reliability | **36% end-to-end success** | Compounding math |

**Key insight:** Context rot is an architectural property of transformer attention, not a training gap. Larger windows delay but do not prevent degradation.

**Sources:**
- [Chroma: Context Rot](https://research.trychroma.com/context-rot)
- [Morph: Context Rot guide](https://www.morphllm.com/context-rot)
- [Anthropic Engineering: Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Factory.ai: The Context Window Problem](https://factory.ai/news/context-window-problem)

---

## 8. Memory Augmentation

| Metric | Number | Source |
|--------|--------|--------|
| Agentic RAG vs. traditional RAG accuracy | **+26%** | Multiple 2025 sources |
| Agentic RAG token reduction | **90% fewer tokens** | Multiple 2025 sources |
| Hindsight agentic memory accuracy | **91.4%** on LongMemEval | Vectorize.io / Virginia Tech / Washington Post, 2025 |
| Observational memory vs. RAG | +4.18 pp, **~10× cost reduction** | VentureBeat / 2025 study |
| LongMemEval commercial systems drop (hard setting) | **30–60% performance drop** | LongMemEval (ICLR 2025) |
| Memory compression efficiency | **89–95%** while maintaining correctness | Mem0 (arxiv 2504.19413) |
| Zep temporal knowledge graph vs. baseline | 94.8% vs. 93.4% on DMR | Zep research, 2025 |

**Sources:**
- [LongMemEval — arxiv 2410.10813](https://arxiv.org/abs/2410.10813)
- [VentureBeat: Observational memory cuts costs 10×](https://venturebeat.com/data/observational-memory-cuts-ai-agent-costs-10x-and-outscores-rag-on-long)
- [VentureBeat: Hindsight memory 91% accuracy](https://venturebeat.com/data/with-91-accuracy-open-source-hindsight-agentic-memory-provides-20-20-vision)
- [Mem0: Production memory arxiv 2504.19413](https://arxiv.org/pdf/2504.19413)
- [AWS AgentCore memory research](https://aws.amazon.com/blogs/machine-learning/building-smarter-ai-agents-agentcore-long-term-memory-deep-dive/)

---

## 9. Security / Prompt Injection

| Metric | Number | Source |
|--------|--------|--------|
| Prompt injection present in production deployments | **73%** | Security audits, 2025 |
| Agent frameworks with exploitable tool-execution flaws | **40%** | OWASP / security research, 2025 |
| Standard prompt injection success rate | **50–84%** | Multiple security studies, 2025 |
| Advanced/adaptive injection success rate | **>85%** | Multiple security studies, 2025 |
| RAG poisoning with 5 crafted documents | **~90% manipulation rate** | Palo Alto Unit 42, 2025 |
| Defense layers reduce attack success | 73.2% → **8.7%** | Security research, 2025 |
| AI firewalls detect known patterns | **~80%** | Security benchmarks, 2025 |
| Organizations with dedicated injection defenses | **34.7%** | Survey, 2025 |
| Organizations planning agentic AI deployment | **83%** | Cisco State of AI Security 2026 |
| Organizations that feel ready to secure it | **29%** | Cisco State of AI Security 2026 |
| First real-world zero-click prompt injection | EchoLeak (CVE-2025-32711), CVSS 9.3 | 2025 |

**Sources:**
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [SQ Magazine: Prompt injection statistics 2026](https://sqmagazine.co.uk/prompt-injection-statistics/)
- [Lakera: Q4 2025 agent attack analysis](https://www.lakera.ai/blog/the-year-of-the-agent-what-recent-attacks-revealed-in-q4-2025-and-what-it-means-for-2026)
- [Microsoft Security: Secure agentic AI end-to-end, March 2026](https://www.microsoft.com/en-us/security/blog/2026/03/20/secure-agentic-ai-end-to-end/)

---

## 10. Agentic Framework Latency (LangGraph vs. LangChain vs. AutoGen vs. CrewAI)

| Framework | Simple task latency | Token efficiency | Best for |
|-----------|---------------------|-----------------|----------|
| LangChain | <5 s, <900 prompt tokens | High (most efficient) | Integration breadth, RAG |
| LangGraph | <5 s, <900 prompt tokens | High (state management) | Production agent workflows |
| AutoGen | Slightly above LangChain | Moderate | Multi-agent conversations, human-in-the-loop |
| CrewAI | Moderate | Moderate | Structured workflow prototyping |

- **LangGraph overhead:** ~14ms per query vs. LangChain (~10ms) — negligible vs. LLM API latency >1s.
- **LangChain:** 600+ LLMs and tools; complexity leads to **+25% debugging time** per user reports.
- **AutoGen:** Asynchronous event loop; **+25% automation productivity** per Microsoft internal benchmarks.
- **Single-agent latency:** 2–4 seconds. **Multi-agent equivalent:** 8–15 seconds.

**Sources:**
- [Instinctools: AutoGen vs LangChain vs CrewAI](https://www.instinctools.com/blog/autogen-vs-langchain-vs-crewai/)
- [Latenode: LangGraph vs AutoGen vs CrewAI 2025](https://latenode.com/blog/platform-comparisons-alternatives/automation-platform-comparisons/langgraph-vs-autogen-vs-crewai-complete-ai-agent-framework-comparison-architecture-analysis-2025)
- [Markaicode: LangGraph vs CrewAI production 2026](https://markaicode.com/vs/langgraph-vs-crewai-multi-agent-production/)

---

## 11. Verification and Self-Correction

| Metric | Number | Source |
|--------|--------|--------|
| Self-Refine improvement over direct generation | **+5% to +40%** (7 tasks) | Madaan et al. — Self-Refine paper |
| Reflexion: GPT-4 coding improvement | 80% → **91%** (+11 pp) | Reflexion framework paper |
| Unguided self-reflection at the frontier | **+1.8 pp or less** over 5 iterations | 2025 refinement study (1,000 problems, 11 domains) |
| Guided external feedback within 5 turns | **+80% gains** | 2025 refinement study |
| Enterprise AI agent failure rate (first year) | **73%** | Cleanlab: AI Agents in Production, 2025 |
| Teams with "elite" evaluation coverage (>90%) | **15%** | Cleanlab, 2025 |
| Well-implemented agents with structured verification | **85–95% autonomous completion** | Industry benchmarks, 2025 |
| 20-step agent, 95% per-step reliability | **36% end-to-end success** | Compounding math |

**Key insight:** Unguided self-reflection adds little at the frontier (+1.8 pp). External structured verification with distinct detection mechanisms is required for meaningful quality improvement (+80% with guided feedback).

**Sources:**
- [Self-Refine paper](https://selfrefine.info/)
- [Reflexion framework (OpenReview)](https://openreview.net/pdf?id=vAElhFcKW6)
- [Nature npj AI: Self-reflection study](https://www.nature.com/articles/s44387-025-00045-3)
- [Cleanlab: AI Agents in Production 2025](https://cleanlab.ai/ai-agents-in-production-2025/)
- [arxiv: Science of AI Agent Reliability](https://arxiv.org/html/2602.16666v1)

---

## Master Quick-Reference Table

| Claim | Number | Source |
|-------|--------|--------|
| Claude Opus 4.5 SWE-bench Verified | 80.9% | Anthropic, Nov 2025 |
| Claude 3.7 Sonnet scaffold gain | +8 pp (62.3% → 70.3%) | SWE-bench, Feb 2025 |
| Devin original SWE-bench | 13.86% | Cognition, Mar 2024 |
| GAIA human baseline | 92% | GAIA benchmark |
| WebArena IBM CUGA | 61.7% | IBM, Feb 2025 |
| HumanEval frontier | ~93% | GPT-5.3 Codex, 2025–2026 |
| Multi-agent error amplification (unstructured) | 17.2× | Google DeepMind, Dec 2025 |
| Multi-agent error amplification (centralized) | 4.4× | Google DeepMind, Dec 2025 |
| Single-agent beats multi-agent rate | 64% of tasks | Princeton NLP |
| Parallelizable task multi-agent gain | +81% | LangChain / Princeton |
| Sequential task multi-agent degradation | -70% | LangChain / Princeton |
| Coordination benefit plateau | >4 agents | Multiple studies |
| Token usage explains performance variance | 80% | Google Research |
| Context rot — models tested | 18 LLMs | Chroma, 2025 |
| Degradation despite large window | 50K tokens even with 1M window | Chroma / Morph |
| Lost-in-the-middle accuracy drop | ~30%+ | Liu et al., Stanford |
| Agentic RAG vs. traditional RAG | +26% accuracy, 90% fewer tokens | Multiple 2025 |
| Hindsight memory accuracy | 91.4% | Vectorize.io / Virginia Tech |
| Memory compression efficiency | 89–95% | Mem0, arxiv 2504.19413 |
| Prompt injection in production | 73% of deployments | OWASP audits, 2025 |
| Standard injection success rate | 50–84% | Security studies, 2025 |
| Defense reduces attack success | 73.2% → 8.7% | Security research |
| Self-Refine gain range | +5% to +40% | Madaan et al. |
| Reflexion GPT-4 coding | 80% → 91% | Reflexion paper |
| Unguided self-reflection at frontier | +1.8 pp | 2025 refinement study |
| Guided external feedback | +80% within 5 turns | 2025 refinement study |
| Enterprise agent failure rate (year 1) | 73% | Cleanlab, 2025 |
| 20-step agent compounding (95% step rate) | 36% success | Math |

---

## Caveats for Citation

1. **SWE-bench scores are scaffold-dependent** — always specify "base model" vs. "with agent framework." The gap can be 8+ percentage points.
2. **SWE-bench Verified** (500 tasks, human-validated) is the most trustworthy leaderboard. Self-reported scores from vendors on their own infrastructure should be treated cautiously.
3. **Context rot thresholds** are empirical estimates that vary by model and task type. "Degrades at 50K" is a rough guide, not an absolute number.
4. **Security statistics** (73% of deployments, etc.) come from security audit surveys with inherent selection bias — organizations seeking audits are not representative of all deployments.
5. **Self-correction numbers** vary widely by task type. The +5–40% Self-Refine range reflects genuine variation across diverse task categories, not a single number.
