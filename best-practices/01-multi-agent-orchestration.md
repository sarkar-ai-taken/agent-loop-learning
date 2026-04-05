---
name: multi-agent-orchestration
description: Best practices for designing and operating multi-agent LLM systems — coordinator/worker patterns, concurrency, phase model, failure handling.
type: reference
---

# Multi-Agent Orchestration Best Practices

## Benchmarks at a Glance

| Metric | Finding | Source |
|--------|---------|--------|
| Multi-agent gain on parallelizable tasks | **+81%** (Finance-Agent benchmark) | LangChain / Princeton NLP, 2025 |
| Multi-agent degradation on sequential tasks | **−70%** (PlanCraft benchmark) | LangChain / Princeton NLP, 2025 |
| Single-agent wins across all benchmarks | **64% of tasks** | Princeton NLP Group, 2025 |
| Error amplification — unstructured "bag of agents" | **17.2×** | Google DeepMind, Dec 2025 |
| Error amplification — centralized orchestration | **4.4×** (4× better than unstructured) | Google DeepMind, Dec 2025 |
| Coordination gains plateau above | **4 agents** | Multiple studies, 2025 |
| MIT: centralized multi-agent improvement | **+80.8%** over single-agent baseline | MIT, Dec 2025 |
| Token usage explains BrowseComp variance | **80%** | Google Research, 2025 |
| Latency: single-agent vs. multi-agent | 2–4 s vs. 8–15 s per task | Framework benchmarks, 2025 |
| Hybrid cascading improvement | +1.1–12% accuracy, −20% deployment cost | arxiv 2505.18286 |
| SWE-bench scaffold gain (same model) | +8 pp (62.3% → 70.3%) from agent engineering alone | SWE-bench, Feb 2025 |

**Key takeaway:** Multi-agent wins on parallelizable, broad tasks. Single-agent wins on 64% of sequential tasks. Adding agents beyond 4 adds coordination overhead without quality gains. Centralized orchestration reduces error amplification by 4× vs. an unstructured agent network.

---

## 1. The Coordinator/Worker Split

The most durable pattern in production multi-agent systems separates **orchestration** from **execution**:

- **Coordinator** — communicates with the user, decides what to do, synthesizes findings, directs workers. Never executes raw operations when a worker can.
- **Worker** — executes a bounded, self-contained task. Has no access to the conversation history. Gets everything it needs in its prompt.

### Why this works
- Coordinators carry conversation context; workers carry execution context. Mixing them pollutes both.
- Workers can be replaced, retried, or parallelized without affecting the coordinator's state.
- Research shows centralized coordination contains error amplification to 4.4× — a dramatic improvement over the 17.2× seen in independent (decentralized) multi-agent systems.

### Anti-pattern: the "do-everything agent"
A single agent that both reasons about a plan and executes every step serially is slow, prone to context pollution, and can't parallelize. Split as soon as complexity warrants it. Note that single-agent systems do outperform multi-agent on 64% of sequential tasks (Princeton NLP, 2025) — the split is only worth it for tasks that benefit from parallelism or specialization.

---

## 2. The Four-Phase Model

Every substantial task maps cleanly to four phases:

| Phase | Who | Purpose |
|-------|-----|---------|
| **Research** | Workers (parallel) | Explore the codebase/domain, find relevant information, understand problem shape |
| **Synthesis** | Coordinator | Read findings, understand the problem, write a precise implementation spec |
| **Implementation** | Workers (one per file group) | Apply targeted changes per spec, run tests, commit |
| **Verification** | Workers (fresh, independent) | Prove the change works — don't rubber-stamp |

**Never skip synthesis.** It is the coordinator's most important job. Research findings must be understood and converted into a specific spec before any implementation begins.

---

## 3. Parallelism Is the Superpower

**Rule:** Any two tasks with no shared write dependency can and should run simultaneously.

**Good — launch independent research workers at the same time:**
```
Spawn: "Investigate auth module in the codebase — find all session handling code, report file paths and function signatures."
Spawn: "Find all test files for authentication — report what's covered and any gaps around session expiry."
```

**Bad — serializing independent research:**
```
Wait for research worker 1 to finish before starting research worker 2.
```

### Concurrency rules
- **Read-only tasks (research):** Run as many in parallel as makes sense — no conflict risk.
- **Write-heavy tasks (implementation):** One worker per overlapping file set to avoid conflicts.
- **Verification:** Can run alongside implementation on different file areas.
- **Independent features:** Always parallelize across different modules.

Token usage explains 80% of performance variance in multi-agent evaluations (Google Research, BrowseComp 2025). Parallelism is the primary mechanism for spending enough tokens to solve hard problems within acceptable latency.

---

## 4. Continue vs. Spawn

After a worker completes, choose deliberately:

| Situation | Action | Why |
|-----------|--------|-----|
| Research explored exactly the files that need editing | **Continue** with synthesized spec | Worker already has files in context |
| Research was broad, implementation is narrow | **Spawn fresh** | Avoid dragging exploration noise |
| Correcting a failure | **Continue** | Worker has full error context |
| Verifying another worker's output | **Spawn fresh** | Verifier must see code with fresh eyes |
| Implementation used the wrong approach entirely | **Spawn fresh** | Wrong-approach context anchors bad retries |
| Completely unrelated task | **Spawn fresh** | No context overlap |

**The test:** does the worker's existing context help or hurt the next task? High overlap → continue. Low overlap → spawn fresh.

---

## 5. Task Lifecycle Management

### Stopping workers
If requirements change mid-flight or a worker is headed in the wrong direction, stop it immediately. A running worker consuming tokens toward the wrong goal is pure waste.

### Handling failures
When a worker fails:
1. **Continue the same worker** with corrected instructions — it has full error context.
2. If a correction attempt fails, try a fundamentally different approach.
3. If the approach is wrong at the root, spawn fresh with a new strategy.
4. Only escalate to the user after investigation.

**Never retry the identical prompt blindly.** Diagnose first.

### Worker results protocol
Worker results should arrive as structured, parseable notifications. The coordinator must:
- Distinguish them from user messages
- Extract the result and synthesize it before acting
- Never acknowledge workers as conversation partners — only the user sees coordinator output

---

## 6. Scratchpad for Cross-Worker Knowledge

When workers need to share durable knowledge (discovered patterns, API signatures, partial plans), a shared **scratchpad** avoids redundant re-discovery. Workers read and write freely within the scratchpad without permission friction.

Best practices:
- Structure by concern (e.g., `auth-findings.md`, `affected-files.txt`)
- Write conclusions, not raw output — other workers shouldn't have to re-parse shell output
- Clear stale entries when the task is done

---

## 7. What Real Verification Looks Like

Verification is not "run the tests and say they pass." It is **proving the change works**:

- Run tests **with the specific feature enabled** — not just the default suite
- Run type checks and **investigate** errors — don't dismiss as "unrelated"
- Test edge cases and error paths the implementation worker did not test
- Try to falsify the change — act as an adversary
- Report specific evidence, not vague summaries

A separate verification worker with fresh context is the second layer of QA; the implementation worker's self-test is the first.

---

## 8. The Proactive Agent Pattern

Standard agents are reactive: they wait for a user message. A proactive agent architecture separates **initiative** from **execution**, enabling always-on background behavior.

**Core pattern (KAIROS-style):**
1. A lightweight "heartbeat" agent receives periodic check-in prompts ("Anything worth doing right now?")
2. The heartbeat agent scans context, recent activity, or a watch list
3. It decides: act, queue a suggestion, or stay silent
4. If acting, it spawns a separate execution agent to do the actual work

**Why separate initiative from execution:**
- The decision about *whether* to act (initiative) is a cheap reasoning operation
- The *execution* may require expensive tool use — don't pay that cost for a "no action needed" decision
- Bugs in execution can't corrupt the initiative logic if they're separated

**When to use:**
- Background monitoring (failing tests, security alerts, depleted resources)
- Periodic maintenance (memory consolidation, documentation updates)
- Anticipatory work (pre-fetching likely next context)
- Watch conditions ("alert me when deployment finishes")

**Implementation constraint:** the heartbeat agent must have a well-defined short-circuit for "no action needed" — otherwise it spawns work on every heartbeat.

---

## 9. Parallel Tool Calls Require Explicit Signaling

Agents default to sequential tool execution unless independence is explicitly signaled. The choice of connective language determines whether operations parallelize or serialize.

**Triggers parallelism:**
```
"Read file A and file B at the same time."
"Fetch both the user record and the session record."
"Search for X while also scanning for Y."
```

**Triggers sequential execution:**
```
"Read file A, then read file B."
"First fetch the user record, then get their sessions."
"After finding X, look for Y."
```

This applies at every level — worker prompts, tool call arrays, and subagent spawning. Use conjunction ("and", "simultaneously", "at the same time") for parallel work. Reserve sequence language ("then", "after", "first...then") for genuinely dependent operations.

---

## 10. Lifecycle Hooks: Enforcement Over Instruction

System prompt rules are soft — the agent can follow or violate them. Lifecycle hooks are hard — they execute regardless of what the agent decides.

The distinction matters for rules that must never be violated:

| Rule type | Via system prompt | Via hook |
|-----------|------------------|----------|
| "Don't push to main" | Agent may comply | `pre_tool_use` hook blocks the push command |
| "Add license headers to new files" | Agent may forget | `post_tool_use` hook adds it automatically |
| "Notify when session ends" | Agent may miss | `session_end` hook sends notification |
| "Validate before destructive ops" | Agent may skip | `pre_tool_use` hook runs validator |

**Core hook events to implement:**

```
pre_tool_use      — intercept any tool call before execution (return deny to block)
post_tool_use     — react to tool results (log, validate, auto-fix)
pre_tool_use_failure  — handle tool errors with custom logic
session_start     — initialize context, load workspace state
session_end       — flush logs, send summaries, release locks
subagent_start    — inject context into new workers
subagent_stop     — collect results, update shared state
```

Hook responses can be:
- **Synchronous JSON** — immediate allow/deny decision
- **Async JSON** — long-running validation (file scan, external check)
- **Prompt request** — ask the user interactively before proceeding

**Session end is the only phase with the full transcript.** `session_start` does not have access to prior conversation history. If you need to generate a session summary, write a completion report, or trigger memory consolidation based on what actually happened, hook into `session_end` — not `session_start`. This is a critical data-availability distinction that breaks many hook implementations when ignored.

**Hook profile switching:** rather than binary on/off hooks, expose runtime profiles via environment variable:

```
HOOK_PROFILE=minimal   → only blocking/safety hooks active
HOOK_PROFILE=standard  → safety + logging + auto-formatting
HOOK_PROFILE=strict    → all hooks including style enforcement, review gates
```

A profile variable lets developers switch behavior per project or per session without editing config files. This prevents merge conflicts when hooks are updated and makes CI/CD environments easy to configure (CI typically runs `minimal`; local dev runs `standard` or `strict`).

**Design principle:** put rules that must never be broken into hooks. Reserve the system prompt for guidelines, preferences, and context. This is the difference between advice and enforcement.

---

## 11. Coordinator Answers Directly When Possible

The most common coordinator anti-pattern is over-delegation: spawning a worker to answer a question the coordinator could answer from its own context.

**Rule: if the coordinator can answer without tools, answer — don't delegate.**

```
User: "What's the syntax for a TypeScript generic constraint?"
Bad: Spawn research worker to investigate TypeScript syntax
Good: Answer directly from knowledge

User: "What did the last worker find?"
Bad: Spawn worker to summarize the previous worker's output
Good: Read the result yourself and summarize

User: "Is the session expiry bug in the auth module?"
Bad: Spawn worker to check
Good: If you have the code in context, answer. If not, spawn.
```

The threshold: if answering requires tools or context the coordinator doesn't have, delegate. If it's in working memory or general knowledge, just answer. Spurious worker spawns add latency, consume tokens, and create failure points.

---

## 12. Coordinator System Prompt Essentials

A well-designed coordinator system prompt must include:

1. **Role definition** — what the coordinator is and is not responsible for
2. **Available tools** — exact names, what each does, when to use each
3. **Worker capabilities** — what tools workers have access to
4. **Phase model** — explicit research → synthesis → implement → verify steps
5. **Concurrency guidance** — explicit instruction to parallelize independent work
6. **Prompt quality standards** — what makes a good vs. bad worker prompt
7. **Result handling** — how to interpret worker notifications
8. **Failure handling** — what to do when workers fail

The examples section of a coordinator prompt is not optional decoration — it is where the most impactful behavioral shaping happens. Concrete good/bad examples outperform abstract rules at shaping model behavior.

---

## Sources

- [Benchmarking Multi-Agent Architectures — LangChain Blog](https://blog.langchain.com/benchmarking-multi-agent-architectures/)
- [Evaluating Multi-Agent Systems in Enterprise Tool Use — Snorkel AI](https://snorkel.ai/blog/multi-agents-in-the-context-of-enterprise-tool-use/)
- [Single-agent or Multi-agent Systems? Why Not Both? — arxiv 2505.18286](https://arxiv.org/abs/2505.18286)
- [Towards a Science of Scaling Agent Systems — Google Research](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/)
- [Multi-Agent LLM Orchestration Achieves Deterministic Results — arxiv 2511.15755](https://arxiv.org/abs/2511.15755)
- [Multi-agent LLMs in 2026 — SuperAnnotate](https://www.superannotate.com/blog/multi-agent-llms)
- [OpenAI Agents SDK — Multi-agent orchestration](https://openai.github.io/openai-agents-python/multi_agent/)
