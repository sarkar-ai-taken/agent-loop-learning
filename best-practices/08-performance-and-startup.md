---
name: performance-and-startup
description: Best practices for agent startup latency, token efficiency, parallel prefetching, and runtime performance.
type: reference
---

# Performance and Startup Best Practices

## Benchmarks at a Glance

| Metric | Finding | Source |
|--------|---------|--------|
| LangGraph vs LangChain throughput | LangGraph executes fastest with most efficient state management; LangChain consumes more tokens due to heavier memory handling | Multi-agent frameworks benchmark, 2025 |
| CrewAI latency | Longest delays due to autonomous deliberation before tool calls | Multi-agent frameworks benchmark, 2025 |
| Single-agent latency | 2–4 seconds per task | Multi-agent framework analysis, 2025 |
| Multi-agent latency | 8–15 seconds per task | Multi-agent framework analysis, 2025 |
| Memory compression efficiency | 89–95% compression achievable while maintaining correctness | Mem0 production study (arxiv 2504.19413) |
| Context rot performance threshold | Models may degrade at 50k tokens even with a 1M token window | Morph LLM Research / Chroma, 2025 |
| Token budget explains variance | Token usage explains 80% of BrowseComp performance variance | Google Research, 2025 |

---

## 1. Startup Latency: Parallelize Everything

Startup is where most interactive agent UX latency lives. The principle: **fire every I/O operation that can possibly run in parallel before you need its result.**

Key startup operations to parallelize:
- Configuration file reads (MDM, env files)
- Credential/auth prefetch (keychain, OAuth token refresh)
- Feature flag initialization
- Plugin/tool registry fetch
- Bootstrap API calls

**Pattern: fire-and-await**
```
# At startup — fire immediately, don't await yet
credential_future = prefetch_credentials()
flags_future = initialize_feature_flags()
registry_future = prefetch_tool_registry()

# Complete synchronous init work while I/O runs...

# Await only when the value is actually needed
credentials = await credential_future
```

On macOS, keychain accesses and system config reads are synchronous subprocess calls that would otherwise block for 50–100ms each when serialized. Parallelizing them with module load time makes them nearly "free."

---

## 2. Prefetch Everything You'll Need in the First 30 Seconds

Don't wait until a resource is needed to fetch it. Prefetch speculatively.

Resources worth prefetching at startup:
- **Feature flags** — before any gate check can occur
- **Plugin/MCP registry URLs** — before the user might try to add a plugin
- **Cloud credentials** — for users with cloud auth configured
- **Bootstrap data** — session initialization metadata
- **Model availability** — whether preferred models are accessible

**Rule:** if something will probably be needed in the first 30 seconds of a session, start fetching it at startup — don't wait for the moment it's needed.

---

## 3. Feature Flag Caching

Feature flags queried on every request or turn must be cached. Never hit the flag service on each inference turn.

A recommended pattern is to name cache-read functions with an explicit staleness signal:

```
checkFeatureGate_CACHED_MAY_BE_STALE("my_feature")  # fast, ~0ms, reads cache
```

vs.

```
await initializeFeatureFlags()  # slow, network call, only at startup/refresh
```

**Rule:** feature flags read per-turn must use a local cache. Refresh the cache asynchronously in the background, not inline during a turn.

**Rule:** never cache security-critical decisions (permissions, authorization). The slight performance cost of a live check is worth it.

---

## 4. Token Efficiency

Every token has a cost — both monetary and in reasoning quality. Optimize across four areas:

### System prompt
- Remove boilerplate and filler sentences
- Use lists instead of paragraphs for rules
- Don't repeat the same rule in different phrasings
- Exclude sections that don't apply to the current session mode

### Tool definitions
- Defer tools not needed for the current task to a lazy-load pool
- Provide a search/discovery mechanism for the long tail of tools
- Keep tool descriptions precise, not verbose — every sentence in a description consumes context budget on every turn

### Conversation history
- Summarize turns older than N; keep recent N verbatim
- Tool results are almost always compressible — summarize raw output
- Don't re-include full file contents in history if the file hasn't changed

### Tool output
- Return only what the agent needs from each call
- Truncate with a clear message: "Output truncated at 5000 chars. Use offset/limit to page."
- Omit redundant metadata (file permissions, ownership, etc.) unless explicitly requested

### File editing strategy
Prefer diff-based (string replacement) editing over full-file rewrites. Full rewrites send the entire file on every edit; string replacements send only the changed portion. The tradeoff: string replacement requires an exact match, which fails on whitespace or indentation mismatches. **Fix:** always read the file immediately before editing complex sections to ensure the match string is current.

Token usage explains 80% of BrowseComp performance variance (Google Research, 2025) — this means intelligent token budgeting is the primary lever for improving agent quality at a given model capability level.

---

## 5. Background and Forked Agents

Heavy work that doesn't need to block the user should run as a **background forked agent**:

**Context inheritance efficiency:** forked subagents inherit the parent's context as a byte-identical copy — which means they share the same prompt cache prefix. Spawning 5 forked subagents costs barely more in tokens than spawning 1, because the shared prefix is only charged once by the cache. This makes parallelism via forking dramatically cheaper than sequential execution with fresh contexts.

**Good pattern — fork heavy work:**
```
Spawn background agent for:
- Memory consolidation (runs after N sessions)
- Documentation auto-updates (runs after content is read)
- Speculative pre-generation (runs after each assistant turn)
- Analytics processing
- Any heuristic-triggered work
```

The user's session continues unblocked while background work runs. A progress indicator in the UI keeps the user informed without blocking them.

**When to fork:**
- Memory consolidation (periodic, triggered by time + session count)
- Auto-updating documents
- Speculative response generation
- Any work triggered by a heuristic rather than a direct user request

---

## 6. Model Routing by Task Type

Not every task needs the most capable (and most expensive) model. Routing tasks to appropriately-sized models reduces cost without sacrificing quality on tasks that don't require deep reasoning.

**Routing tiers:**

| Task type | Examples | Model tier |
|-----------|----------|-----------|
| Deep reasoning | Architecture design, complex debugging, security analysis | Frontier (Opus-class) |
| Standard coding | Feature implementation, refactoring, test writing | Mid-tier (Sonnet-class) |
| Mechanical / boilerplate | Formatting, renaming, simple edits, config changes | Fast/cheap (Haiku-class) |
| Classification | Is this safe? Is this relevant? Route this request | Smallest viable |

**Implementation:** the orchestrator classifies the task before dispatching to a worker, then selects the model tier accordingly. Workers don't choose their own model — the coordinator routes them.

**Routing signals:**
- Prompt contains: "design", "architect", "debug why", "security" → frontier
- Prompt contains: "implement", "add feature", "write tests" → mid-tier
- Prompt contains: "rename", "format", "update comment", "change X to Y" → fast
- Binary decisions (safe/unsafe, relevant/irrelevant) → smallest viable

**Guardrail:** when uncertain about task complexity, route up, not down. The cost of under-routing (slow/expensive for a simple task) is a known quantity. The cost of over-routing (cheap model produces wrong output that requires expensive correction) is often higher.

---

## 7. Circuit Breaker for Repeated Agent Failures

Retry loops without circuit breakers cause catastrophic resource waste. A real-world example: compaction failures in 1,279 sessions — with the worst session failing 3,272 consecutive times — generated approximately 250,000 wasted API calls per day before a circuit breaker was added.

**Pattern: hard failure limit with fast exit**

```
MAX_CONSECUTIVE_FAILURES = 3

on_failure():
  consecutive_failures += 1
  if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
    stop()  # don't retry
    surface_to_user()
  else:
    retry_with_backoff()
```

Apply this to any automated retry loop: compaction, memory consolidation, tool execution recovery, API call retry. The specific threshold depends on the operation — but any retry loop without a hard stop is a liability.

**What good failure behavior looks like:**
1. Fail fast (3 is enough for most operations)
2. Surface actionable information to the user
3. Don't silently consume resources on futile retries
4. Log the failure count and reason for post-mortem analysis

---

## 8. Diminishing-Returns Token Budget Detector

A token budget that runs to exhaustion wastes money when the agent is spinning — repeating itself, hesitating, or producing diminishing output per round.

**Pattern: early stopping when marginal output collapses**

```
DIMINISHING_THRESHOLD = 500  # tokens

per_round:
  delta = tokens_this_round - tokens_last_round

  if (
    continuation_count >= 3 and
    delta < DIMINISHING_THRESHOLD and
    tokens_last_round < DIMINISHING_THRESHOLD
  ):
    stop_early()  # budget not exhausted, but output is collapsing
```

**Behavior at budget thresholds:**
- At 0–90% of budget: normal operation
- At 90–100% of budget: nudge the agent to push toward completion
- At any point with diminishing returns: stop early, report current state

**Why:** once marginal output per round falls below ~500 tokens for 3 consecutive rounds, the agent is no longer making meaningful progress. Spending the remaining 40% of the budget on a stuck agent is pure cost. Detect the plateau and stop.

---

## 9. Long-Running Task Wake Lock

When an agent runs a multi-minute task, the host system may sleep and interrupt it. On systems that support it, hold a wake lock for the duration:

**Core pattern:**
```
start:
  wake_lock = acquire_wake_lock(timeout=300s)  # 5-minute auto-expire

every 240s (before expiry):
  wake_lock.refresh()  # restart with new 300s timeout

on finish/error:
  wake_lock.release()
```

**Self-healing design:** set the lock timeout shorter than the refresh interval. If the agent process is killed before cleanup runs, the orphaned lock expires automatically rather than holding indefinitely.

**Reference counting for nested callers:** if multiple sub-agents are running simultaneously and all hold wake locks, release only when the last one finishes:

```
lock_count += 1 on acquire
lock_count -= 1 on release
actually_release() only when lock_count == 0
```

This prevents a sub-agent that finishes early from releasing the wake lock while siblings are still running.

---

## 10. Startup Profiling

Every production agent should have a startup profiler with checkpoints:

```
profileCheckpoint("app_entry")
# ... fire prefetches ...
profileCheckpoint("prefetches_started")
# ... module init ...
profileCheckpoint("modules_ready")
# ... feature flags loaded ...
profileCheckpoint("flags_ready")
# ... first UI paint ...
profileCheckpoint("first_render")
```

Emit the time between each checkpoint at the end of startup. This makes startup regressions immediately visible — without a profiler, 50ms regressions accumulate undetected.

**Implement this early** — it's cheap to add and expensive to retrofit.

---

## 11. Speculative Pre-Generation (Sub-Zero Turn Latency)

Pre-generate the likely next response while the user is thinking:

1. After each assistant turn, spawn a background agent that predicts the user's most likely next message
2. Begin generating a response to the predicted message
3. If the user's actual message matches the prediction sufficiently, serve the pre-generated response immediately
4. If not, discard it and generate normally

**Cost:** one additional inference per turn.
**Benefit:** near-zero response latency for 20–40% of turns in typical interactive workflows.

Implementation note: use a cancellation token (AbortController pattern) that terminates speculative generation the moment a real user message arrives. This prevents wasted compute on wrong predictions.

---

## 12. Idle Timeout and Resource Cleanup

Long-running agents accumulate resources. Implement:

- **Idle timeout** — abort sessions that have been inactive for N minutes; surface a "session expired" message rather than silently failing later
- **Cleanup registry** — register cleanup handlers at startup (for open file handles, network connections, lock files); fire all of them on graceful exit
- **Graceful shutdown** — flush logs, complete in-flight writes, release advisory locks before exiting
- **OOM handling** — emit a heap dump for post-mortem analysis on out-of-memory rather than crashing silently

---

## 13. Cache Safety vs. Cache Warmth

Caching is the primary performance lever, but creates coherence risks. Enforce a naming convention that makes staleness visible at the call site:

```
getConfig_CACHED()                     # cached, may be stale
checkPermission_LIVE()                 # always fresh, no cache
getToolSchemas_LAZY()                  # computed once, then cached
checkFeatureGate_CACHED_MAY_BE_STALE() # explicitly stale
```

**Rules:**
- Security decisions: never cache — always live
- User preferences: cache with a short TTL (5–15 minutes)
- Feature flags: cache indefinitely, refresh async
- Model availability: cache with medium TTL, refresh on error

---

## 14. Observability

A fast agent that fails silently is worse than a slow agent that fails loudly. Instrument:

- **Startup time** — profiler checkpoints from entry to first response token
- **Turn latency** — time from user message to first token output
- **Tool call latency** — time per tool invocation (p50, p95, p99)
- **Token usage per turn** — input, output, cache hit/miss separately
- **Background task completion rate** — memory consolidation, speculation, docs update
- **Error rate** — tool failures, network errors, permission denials

Without observability, performance regressions are invisible until they become severe user-facing issues.

---

## Sources

- [LLM Orchestration in the Real World — CrossML](https://www.crossml.com/llm-orchestration-in-the-real-world/)
- [LangGraph vs LangChain vs AutoGen vs CrewAI — Multi-agent frameworks benchmark, AIMultiple 2025](https://aimultiple.com/multi-agent-frameworks)
- [Towards a Science of Scaling Agent Systems — Google Research](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/)
- [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory — arxiv 2504.19413](https://arxiv.org/pdf/2504.19413)
- [Context Rot — Morph LLM Research](https://www.morphllm.com/context-rot)
- [Effective Context Engineering for AI Agents — Anthropic Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Coding with AI Agents: Best Practices for 2026 — Nimbalyst](https://nimbalyst.com/blog/coding-with-ai-agents-best-practices-2026/)
