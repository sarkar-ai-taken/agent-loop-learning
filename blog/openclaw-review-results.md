# Agent Review: OpenClaw (Pi/Subagent Runtime)

**Summary:** OpenClaw's agent runtime is a production-grade, depth-limited hierarchical spawning system. The core architecture (`subagent-spawn → subagent-announce → pi-embedded-runner`) implements a solid coordinator/worker pattern with push-based result delivery, layered sandbox permissions, and explicit prompt-cache stability engineering. The primary gaps are in independent verification workers, semantic/procedural memory tiers, and formal tool security classification properties.

---

## Dimension-by-Dimension Audit

| # | Dimension | Score | Finding |
|---|-----------|:-----:|---------|
| 01 | Multi-agent orchestration | ✅ | Depth-limited hierarchical spawning (`subagent-spawn.ts`), push-based result announcement, concurrent task queue lanes, tool loop detection (generic/polling/ping-pong), lifecycle hooks. Coordinator explicitly suppresses subagent re-initiation via role declaration in prompts. |
| 02 | Worker prompting | ⚠️ | Runtime context injection (workspace, tools, capabilities) is solid. Missing: no enforcement layer for synthesis quality — nothing prevents a coordinator from writing "based on findings, fix it" and spawning. Stop conditions exist at the tool level (loop detection) but task-level exit criteria are not enforced structurally. |
| 03 | Context & memory | ⚠️ | Working memory is excellent — compaction, bootstrap cache, tool-result truncation, token tracking per context engine. Semantic/procedural tiers are absent as first-class constructs. No background consolidation agent converting session transcripts into durable semantic memory. The 3-layer architecture (index → topic files → grep-only transcripts) is not present in the product runtime. |
| 04 | Tool design | ⚠️ | Permission gating (sandbox policy, safe-bin allowlists, abort signals) is strong. Missing: no evidence of the 6 security classification properties (`isConcurrencySafe`, `isReadOnly`, `isDestructive`, `interruptBehavior`, `isOpenWorld`, `toAutoClassifierInput`) formally declared on tool definitions. Tool descriptions lack systematic "when NOT to use" sections. |
| 05 | Verification & testing | ⚠️ | Loop detection and failover policy prevent the worst runaway cases. Missing: no independent verification worker pattern — agents self-report pass/fail with no adversarial second pass. Error amplification without cross-checking reaches 17.2× (Google DeepMind, Dec 2025); no structural mitigation for that specific risk in the agent loop. |
| 06 | Security & permissions | ✅ | Defense-in-depth: Docker/SSH/local sandbox types, sandbox-tool-policy allow/deny lists, safe-bin flag validation, session write locks on context injection, audit logging, gateway method scopes. Prompt injection mitigation exists (context injected after lock acquisition). |
| 07 | Prompt engineering | ✅ | Explicit prompt-cache boundary (`system-prompt-cache-boundary.ts`), normalized and sorted capability IDs (`prompt-cache-stability.ts`), dynamic system prompt composition by runtime mode. Stable/dynamic split is architecturally enforced, not just documented. |
| 08 | Performance & startup | ⚠️ | Lazy model registry, memoized context windows, prompt cache retention per provider, task queue lanes, plugin lazy loading, extra-params per provider. Missing: no startup profiler with named checkpoints; fire-and-await parallel prefetch pattern for credentials/flags/registry not clearly present; no diminishing-returns budget detector for stuck agents. |

---

## Top 3 Highest-Priority Improvements

### 1. Independent Verification Worker Pattern

**What:** After any implementation subagent completes, spawn a fresh subagent with no knowledge of *how* the change was made — only *what* was changed — and give it an adversarial brief to try to falsify the outcome.

**Why:** Unguided self-reporting amplifies errors 17.2× in independent multi-agent systems (Google DeepMind, Dec 2025). A centralized verifier brings that to 4.4×. This is the single highest-leverage architectural addition for output reliability, and it is currently absent as a first-class pattern.

**How:** In `subagent-announce.ts` (around the result-delivery path), when a subagent completes with a coding/implementation task type, the coordinator spawns a second subagent with a verification prompt template (per `05-verification-and-testing.md §3`). Worker type (`implementation` vs `verification`) should be a first-class enum in the spawn call so the coordinator can route without hard-coding prompt text.

---

### 2. 3-Layer Semantic Memory with Background Consolidation

**What:** Add background consolidation that converts session transcripts into durable semantic memory, structured as: always-loaded index → on-demand topic files → grep-only raw transcripts.

**Why:** Commercial memory systems drop 30–60% on hard long-context evaluations (LongMemEval, ICLR 2025). Context rot begins at 50K tokens even with a 1M window (Chroma, 2025). Without a consolidation pipeline, every new session starts cold and repeated context is re-derived at full token cost.

**How:** Add a background consolidation agent triggered by a time gate (24h) + session count gate (5 sessions) + lock check, matching the pattern in `03-context-and-memory.md §4`. The consolidation agent gets read-only access to `~/.openclaw/agents/<id>/sessions/*.jsonl` and write access to a memory directory, sandboxed via the existing `sandbox-tool-policy`. Wire it to the `session_end` hook so it fires non-blocking after each session completes.

---

### 3. Formal Tool Security Classification Properties

**What:** Require every tool definition to declare 6 security properties: `isConcurrencySafe`, `isReadOnly`, `isDestructive`, `interruptBehavior`, `isOpenWorld`, `toAutoClassifierInput`.

**Why:** Without these properties, the tool orchestrator (`pi-tools.ts`) cannot make automated safety decisions — it either always confirms or always bypasses. `isDestructive` in particular drives the confirmation UI and reversibility checks. This is OWASP Agentic Top 10 #2 (insecure tool/plugin design, 2026). Tool misuse is the #5 risk and correlates directly with incomplete tool contracts.

**How:** Add a `ToolSecurityClassification` type to `src/plugin-sdk/channel-contract.ts` (or a new `src/plugin-sdk/tool-contract.ts`). Make it required in the tool registration path. The safe-bin policy profiles already encode some of this knowledge implicitly — lift it into the formal tool schema so it's queryable by the orchestrator and the classifier side-query pattern (`06-security-and-permissions.md §10`).

---

## What's Already Strong

**1. Prompt-cache stability engineering** (`src/agents/prompt-cache-stability.ts`, `system-prompt-cache-boundary.ts`)

Capability IDs are normalized and sorted before building the request; there is an explicit stable/dynamic split at the cache boundary. This is production-grade and directly addresses the correctness and performance-critical guidance in `CLAUDE.md` — few agent systems treat cache stability as a first-class concern.

**2. Defense-in-depth security** (`sandbox-tool-policy.ts`, `exec-safe-bin-policy-profiles.ts`, `security/audit.ts`)

Multiple independent security layers: sandbox isolation (Docker/SSH/local), safe-bin allowlist and flag validation, session write locks on context injection, audit logging, and gateway method scopes. This matches the Zero Trust for Agents model (`06-security-and-permissions.md §1`) better than most open-source agent runtimes.

**3. Circuit breakers and loop detection** (`tool-loop-detection.ts`, `compaction-safety-timeout.ts`, `failover-policy.ts`)

Generic-repeat, polling, and ping-pong loop detectors with warning/critical thresholds, plus model-rotation failover on errors. The compaction safety timeout directly mirrors the real-world incident pattern described in `08-performance-and-startup.md §7` (3,272 consecutive failures before a circuit breaker was added in that cautionary tale). OpenClaw already has this right.
