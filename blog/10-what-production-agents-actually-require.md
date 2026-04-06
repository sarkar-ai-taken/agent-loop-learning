# 9 Things I Learned Reading Claude Code's Source Code

*A deep dive into how Anthropic's production agent actually works — with the real code, the real design decisions, and the lessons you can copy today*

---

Most "agent best practices" posts cite research papers and give you generic advice. This one is different.

Claude Code is one of the few production-grade AI coding agents with readable source code. I went through it. What follows are 9 concrete, specific things the Anthropic engineering team did — with the actual code — that most teams building agents get wrong.

Each section ends with what you should change in your own agent today.

---

## 1. CLAUDE.md Is Not in the System Prompt

This is the most counterintuitive thing in Claude Code's architecture, and the one most teams building similar tools get wrong.

Every Claude Code user knows about `CLAUDE.md` — the file where you put project-specific instructions. The natural assumption is that it gets injected into the system prompt. **It does not.** It goes into the user turn.

Here's the code:

```typescript
// src/context.ts
export const getUserContext = memoize(
  async (): Promise<{ [k: string]: string }> => {
    const claudeMd = shouldDisableClaudeMd
      ? null
      : getClaudeMds(filterInjectedMemoryFiles(await getMemoryFiles()))

    return {
      ...(claudeMd && { claudeMd }),
      currentDate: `Today's date is ${getLocalISODate()}.`,
    }
  },
)
```

And here's where it gets injected:

```typescript
// src/utils/api.ts
export function prependUserContext(
  messages: Message[],
  context: { [k: string]: string },
): Message[] {
  return [
    createUserMessage({
      content: `<system-reminder>\nAs you answer the user's questions, you can use the following context:\n${Object.entries(
        context,
      )
        .map(([key, value]) => `# ${key}\n${value}`)
        .join('\n')}

      IMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task.\n</system-reminder>\n`,
      isMeta: true,
    }),
    ...messages,
  ]
}
```

`getUserContext()` returns `claudeMd` and `currentDate`. They are both wrapped in a `<system-reminder>` block inside a **user message** — `isMeta: true` marks it as infrastructure, invisible to the user — and prepended to the conversation.

Contrast this with `getSystemContext()`, which returns `gitStatus` and is appended to the actual system prompt via `appendSystemContext()`.

**Why?** The system prompt is stable across turns and can be cached aggressively. CLAUDE.md changes per project. If CLAUDE.md were in the system prompt, every project change would bust the cache for every user. By moving it to the first user turn, the system prompt stays stable (and cacheable at org scope), and CLAUDE.md enters the conversation as context the model reads, not as instructions it's initialized with.

**The semantic difference matters too.** System prompt = who the agent is and what it must always do. CLAUDE.md = what you should know about this project. Those are different things, and placing them in different locations makes that explicit.

**What to change today:** If your agent's project-specific context is in the system prompt, move it to the first user turn wrapped in a `<system-reminder>` block. Keep your system prompt stable. Let project context be contextual.

---

## 2. Cache Boundaries Are Named and Enforced in Code

Every production agent leaks money through cache misses. Claude Code handles this by making cache boundary violations visible at the code level.

Two functions, explicitly named to signal cost:

```typescript
// src/constants/systemPromptSections.ts

/**
 * Create a memoized system prompt section.
 * Computed once, cached until /clear or /compact.
 */
export function systemPromptSection(
  name: string,
  compute: ComputeFn,
): SystemPromptSection {
  return { name, compute, cacheBreak: false }
}

/**
 * Create a volatile system prompt section that recomputes every turn.
 * This WILL break the prompt cache when the value changes.
 * Requires a reason explaining why cache-breaking is necessary.
 */
export function DANGEROUS_uncachedSystemPromptSection(
  name: string,
  compute: ComputeFn,
  _reason: string,  // ← you must write why
): SystemPromptSection {
  return { name, compute, cacheBreak: true }
}
```

`DANGEROUS_uncachedSystemPromptSection` takes a `_reason` parameter. The underscore means it's not used at runtime — it's documentation-as-code. Every engineer who calls this function has to write a reason for why this section should recompute every turn and break the cache. The naming convention makes the cost visible in code review.

The system prompt also has a literal boundary marker between what can be globally cached and what cannot:

```typescript
// src/constants/prompts.ts

/**
 * Boundary marker separating static (cross-org cacheable) content
 * from dynamic content.
 */
export const SYSTEM_PROMPT_DYNAMIC_BOUNDARY =
  '__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__'
```

And feature flags follow the same explicit-cost convention:

```typescript
// src/coordinator/coordinatorMode.ts
checkStatsigFeatureGate_CACHED_MAY_BE_STALE('tengu_scratch')
```

`_CACHED_MAY_BE_STALE` is not a warning — it's the name. When you call this function, you are declaring that you accept reading a potentially stale value from cache. The alternative is `initializeFeatureFlags()`, which makes a network call. The naming forces the choice to be explicit at every call site.

**What to change today:** Name your volatile prompt sections explicitly. Use a convention like `VOLATILE_` or `UNCACHED_` as a prefix for anything that recomputes each turn. Make cache-breaking visible in code.

---

## 3. The Verification Agent Cannot Edit Files — By Design

Claude Code ships a built-in verification agent. Its system prompt is 130+ lines of carefully engineered adversarial instruction. But the architectural detail is what's interesting:

```typescript
// src/tools/AgentTool/built-in/verificationAgent.ts

export const VERIFICATION_AGENT: BuiltInAgentDefinition = {
  agentType: 'verification',
  disallowedTools: [
    AGENT_TOOL_NAME,        // cannot spawn sub-agents
    EXIT_PLAN_MODE_TOOL_NAME,
    FILE_EDIT_TOOL_NAME,    // cannot edit files
    FILE_WRITE_TOOL_NAME,   // cannot write files
    NOTEBOOK_EDIT_TOOL_NAME,
  ],
  source: 'built-in',
  background: true,
  model: 'inherit',
  getSystemPrompt: () => VERIFICATION_SYSTEM_PROMPT,
  criticalSystemReminder_EXPERIMENTAL:
    'CRITICAL: This is a VERIFICATION-ONLY task. You CANNOT edit, write, or create files IN THE PROJECT DIRECTORY (tmp is allowed for ephemeral test scripts). You MUST end with VERDICT: PASS, VERDICT: FAIL, or VERDICT: PARTIAL.',
}
```

The verification agent has `FILE_EDIT_TOOL_NAME` and `FILE_WRITE_TOOL_NAME` in its `disallowedTools` list. This is not a prompt instruction — it's an architectural constraint enforced by the tool permission system. The agent literally cannot edit files. Not because it was told not to, but because the tool isn't in its available set.

The `criticalSystemReminder_EXPERIMENTAL` field is also revealing — it's a separate injection mechanism that provides a persistent reminder at a specific location in the context, separate from the main system prompt. This is an acknowledgment that even a good system prompt can be "forgotten" as context grows. The critical reminder is injected at a location designed to survive context rot.

The verification agent's system prompt itself is engineering worth reading. It explicitly names its own failure modes:

> "You have two documented failure patterns. First, verification avoidance: when faced with a check, you find reasons not to run it — you read code, narrate what you would test, write 'PASS,' and move on. Second, being seduced by the first 80%..."

And it pre-empts the rationalizations the agent will reach for:

> "- 'The code looks correct based on my reading' — reading is not verification. Run it.  
> - 'The implementer's tests already pass' — the implementer is an LLM. Verify independently.  
> - 'This is probably fine' — probably is not verified. Run it."

This is the hardest-won lesson in agentic systems: **models will take the path of least resistance**. If the verification agent can rationalize a PASS, it will. The system prompt pre-empts those rationalizations by naming them.

**What to change today:** Implement your verification agent with `disallowedTools` enforced at the architectural level, not just the prompt level. And pre-write the rationalizations your verification agent will reach for — then explicitly prohibit them in the system prompt.

---

## 4. The Denial Circuit Breaker Is Exact and Enforced

Claude Code's permission system includes a circuit breaker with specific, hardcoded thresholds:

```typescript
// src/utils/permissions/denialTracking.ts

export const DENIAL_LIMITS = {
  maxConsecutive: 3,
  maxTotal: 20,
} as const

export function shouldFallbackToPrompting(
  state: DenialTrackingState,
): boolean {
  return (
    state.consecutiveDenials >= DENIAL_LIMITS.maxConsecutive ||
    state.totalDenials >= DENIAL_LIMITS.maxTotal
  )
}
```

If an agent's tool calls are denied **3 times in a row**, or **20 times total** in a session, the system falls back to prompting the user directly. This is a circuit breaker that catches two distinct failure modes:

1. **Consecutive denials** (3 max): the agent is stuck in a loop trying the same blocked action repeatedly — likely injection or runaway behavior
2. **Total denials** (20 max): the agent is operating broadly outside its permitted scope — a deeper permission misconfiguration or session drift

State is tracked immutably and a success resets the consecutive counter (but not the total):

```typescript
export function recordDenial(state: DenialTrackingState): DenialTrackingState {
  return {
    ...state,
    consecutiveDenials: state.consecutiveDenials + 1,
    totalDenials: state.totalDenials + 1,
  }
}

export function recordSuccess(state: DenialTrackingState): DenialTrackingState {
  if (state.consecutiveDenials === 0) return state
  return { ...state, consecutiveDenials: 0 }
}
```

The immutable update pattern (`{ ...state, field: newValue }`) is intentional — denialTracking state cannot be mutated in place, which prevents a compromised tool from silently resetting its own denial counter.

For async subagents whose `setAppState` is a no-op, there's a `localDenialTracking` field on `ToolUseContext` — a mutable reference passed through the agent context so the counter accumulates correctly even when the agent can't reach the main state store.

This came from production incident data — those exact numbers aren't arbitrary. They represent the threshold at which the pattern of denials changes from "normal agentic friction" to "something is wrong."

**What to change today:** Add a denial circuit breaker to your agent loop. Track consecutive and total denials separately. When either threshold triggers, surface the situation to the user — do not retry.

---

## 5. Tools Default to Unsafe

Every tool in Claude Code is built through `buildTool()`, which applies a set of defaults before the tool definition overrides them:

```typescript
// src/Tool.ts

const TOOL_DEFAULTS = {
  isEnabled: () => true,
  isConcurrencySafe: (_input?) => false,   // assume NOT safe
  isReadOnly: (_input?) => false,           // assume WRITES
  isDestructive: (_input?) => false,
  checkPermissions: (input, _ctx?): Promise<PermissionResult> =>
    Promise.resolve({ behavior: 'allow', updatedInput: input }),
  toAutoClassifierInput: (_input?) => '',   // skip security classifier
  userFacingName: (_input?) => '',
}

export function buildTool<D extends AnyToolDef>(def: D): BuiltTool<D> {
  return {
    ...TOOL_DEFAULTS,
    userFacingName: () => def.name,
    ...def,
  } as BuiltTool<D>
}
```

Three critical defaults:
- `isConcurrencySafe: false` — assume the tool cannot run in parallel
- `isReadOnly: false` — assume the tool writes
- `toAutoClassifierInput: () => ''` — skip the security classifier (the tool is invisible to auto-mode security analysis)

These are **fail-closed** defaults for the first two and **fail-open** for the third. A new tool that doesn't declare itself read-only is treated as a writer. A new tool that doesn't declare itself concurrency-safe is serialized. A new tool that doesn't implement `toAutoClassifierInput` is invisible to the security classifier — which is also a safe default, because most tools don't need classifier input, and an incorrect classifier representation is worse than no representation.

The tool interface also includes `interruptBehavior`:

```typescript
/**
 * What should happen when the user submits a new message while this tool
 * is running.
 *
 * - 'cancel' — stop the tool and discard its result
 * - 'block'  — keep running; the new message waits
 *
 * Defaults to 'block' when not implemented.
 */
interruptBehavior?(): 'cancel' | 'block'
```

This is a UX and correctness decision combined. A read-only search tool should `cancel` when interrupted — no point finishing a search the user has already moved past. A write operation should `block` — abandoning a half-written file edit is worse than making the user wait.

**What to change today:** When building tools, explicitly declare `isReadOnly`, `isConcurrencySafe`, and `isDestructive`. Don't rely on defaults for safety-relevant fields. Add `interruptBehavior` to anything that runs for more than a second.

---

## 6. Agents Are Typed and Lifecycle-Managed

Claude Code's task system distinguishes seven types of agents:

```typescript
// src/Task.ts

export type TaskType =
  | 'local_bash'
  | 'local_agent'
  | 'remote_agent'
  | 'in_process_teammate'
  | 'local_workflow'
  | 'monitor_mcp'
  | 'dream'
```

And five lifecycle states:

```typescript
export type TaskStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'killed'
```

`'killed'` is distinct from `'failed'`. A failed task encountered an error; a killed task was deliberately stopped. The distinction matters for cleanup, retry logic, and user reporting. And `isTerminalTaskStatus` provides a single source of truth for "will this task transition again?":

```typescript
export function isTerminalTaskStatus(status: TaskStatus): boolean {
  return status === 'completed' || status === 'failed' || status === 'killed'
}
```

Task IDs are typed by agent type, with a security-conscious alphabet:

```typescript
// Case-insensitive-safe alphabet (digits + lowercase) for task IDs.
// 36^8 ≈ 2.8 trillion combinations, sufficient to resist brute-force symlink attacks.
const TASK_ID_ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyz'

const TASK_ID_PREFIXES: Record<string, string> = {
  local_bash:           'b',
  local_agent:          'a',
  remote_agent:         'r',
  in_process_teammate:  't',
  local_workflow:       'w',
  monitor_mcp:          'm',
  dream:                'd',
}
```

The prefix `b`, `a`, `r`, `t`, `w`, `m`, `d` makes it instantly obvious from a task ID what kind of agent produced it. The comment explains the design intent — "resist brute-force symlink attacks" — which means someone thought carefully about what an attacker could do with a predictable task ID.

`'dream'` is the most interesting type. It appears to be an internal designation for speculative or imaginative agent modes — the kind of task the system might run to explore possibilities without committing to them.

**What to change today:** Add explicit lifecycle states to your agent tasks. Distinguish killed from failed. Make terminal states queryable through a single function so your cleanup logic has one source of truth.

---

## 7. The Verification Agent's System Prompt Is the Product

Most teams write verification into their main agent's instructions: "after completing the task, verify your work." This does not work reliably. The verification agent pattern in Claude Code separates verification into its own agent with its own system prompt, its own tool constraints, and its own verdict format.

The prompt structure is worth studying as a template for any high-stakes agent:

**1. Named failure modes** — the prompt opens by naming the two ways the verification agent typically fails (verification avoidance, being seduced by the first 80%). Naming your agent's failure modes at the top of the system prompt is an unusually effective technique.

**2. Hard prohibitions in ALL CAPS** — `=== CRITICAL: DO NOT MODIFY THE PROJECT ===`. The all-caps header isn't aesthetic — frontier models respond to visual prominence in prompts. Important prohibitions get headers.

**3. Type-specific verification strategies** — the prompt provides distinct verification paths for frontend changes, backend/API changes, CLI changes, infrastructure changes, library changes, bug fixes, mobile, data/ML, migrations, and refactoring. This prevents the agent from applying a one-size-fits-all approach.

**4. Required output format** — every check must follow an exact structure with `Command run`, `Output observed`, and `Result`. A PASS without a command is a skip. The caller can spot-check by re-running the command and comparing output.

**5. Mandatory adversarial probe** — before issuing PASS, the agent must run at least one adversarial probe (concurrency, boundary, idempotency, orphan operation). This prevents the agent from confirming the happy path and calling it verified.

**6. Pre-emptive rationalization blocking** — the prompt names every excuse the agent will reach for and explicitly instructs the agent to do the opposite.

The output ends with `VERDICT: PASS`, `VERDICT: FAIL`, or `VERDICT: PARTIAL` — a parseable machine-readable line that the calling system can extract without reading the whole report.

```typescript
// The whenToUse field tells the orchestrator when to invoke this agent
const VERIFICATION_WHEN_TO_USE =
  'Use this agent to verify that implementation work is correct before reporting completion. Invoke after non-trivial tasks (3+ file edits, backend/API changes, infrastructure changes). Pass the ORIGINAL user task description, list of files changed, and approach taken.'
```

Note: it's invoked after "3+ file edits." That's the threshold at which self-verification becomes unreliable enough to warrant an independent agent.

**What to change today:** Write your verification agent's system prompt around its failure modes, not its goals. Name what the agent will do wrong. Require a parseable verdict line. Require evidence, not narration.

---

## 8. Swarm Initialization Distinguishes Resumed From Fresh

When Claude Code's multi-agent "swarm" mode starts, it explicitly handles two very different startup paths:

```typescript
// src/hooks/useSwarmInitialization.ts

export function useSwarmInitialization(
  setAppState: SetAppState,
  initialMessages: Message[] | undefined,
  { enabled = true }: { enabled?: boolean } = {},
): void {
  useEffect(() => {
    if (!enabled) return
    if (isAgentSwarmsEnabled()) {
      const firstMessage = initialMessages?.[0]
      const teamName = firstMessage?.teamName
      const agentName = firstMessage?.agentName

      if (teamName && agentName) {
        // RESUMED agent session — context stored in transcript
        initializeTeammateContextFromSession(setAppState, teamName, agentName)
        const teamFile = readTeamFile(teamName)
        const member = teamFile?.members.find(m => m.name === agentName)
        if (member) {
          initializeTeammateHooks(setAppState, getSessionId(), {
            teamName,
            agentId: member.agentId,
            agentName,
          })
        }
      } else {
        // FRESH spawn — context from environment
        const context = getDynamicTeamContext?.()
        if (context?.teamName && context?.agentId && context?.agentName) {
          initializeTeammateHooks(setAppState, getSessionId(), context)
        }
      }
    }
  }, [setAppState, initialMessages, enabled])
}
```

The distinction: a **resumed** agent reads its team and agent name from the transcript (`firstMessage.teamName`, `firstMessage.agentName`). A **fresh** agent reads from the environment context. This is important because resumed agents need to restore their specific identity within the team — they can't just re-read the environment, because the environment might now describe a different session.

Team membership is stored in a `teamFile` on disk, keyed by team name. Each member has an `agentId` that survives resume. The hooks — which gate what the agent is allowed to do — are initialized from this persisted state.

This matters for verification specifically: the verification agent (`background: true` in its definition) runs as a separate process. On resume, it needs to know it's the verification agent for this specific team, not a fresh general-purpose agent that happens to have the same tools.

**What to change today:** If your agents can be resumed, explicitly distinguish the resume path from the fresh-start path. Store agent identity in the transcript, not just the environment. On resume, reconstruct from transcript state, not from current environment.

---

## 9. The Buffer Gate for Message Ordering

This is a low-level but important pattern — one that any agent with streaming or bridged communication needs.

When a Claude Code session starts, it flushes historical messages to the server in a single HTTP POST. Any new messages that arrive during this flush must be queued — not sent — or they arrive at the server interleaved with the historical messages, producing a broken conversation state.

```typescript
// src/bridge/flushGate.ts

export class FlushGate<T> {
  private _active = false
  private _pending: T[] = []

  start(): void {
    this._active = true
  }

  end(): T[] {
    this._active = false
    return this._pending.splice(0)   // drain and return atomically
  }

  enqueue(...items: T[]): boolean {
    if (!this._active) return false
    this._pending.push(...items)
    return true
  }

  drop(): number {
    this._active = false
    const count = this._pending.length
    this._pending.length = 0
    return count
  }

  deactivate(): void {
    this._active = false   // clear flag without dropping items
    // Used when transport is replaced — new transport's flush will drain
  }
}
```

`deactivate()` is the subtle one — it clears the active flag without dropping the pending items. This is for transport replacement: when the underlying WebSocket connection is replaced mid-session, the new transport takes ownership of the pending queue. `drop()` is for permanent close — the session is done, drop everything.

`end()` returns `this._pending.splice(0)` — not `this._pending` and then `this._pending = []`. `splice(0)` is atomic: it returns all items and empties the array in a single operation, preventing any window where items could be added between the return and the clear.

For session capacity management, there's the capacity wake primitive:

```typescript
// src/bridge/capacityWake.ts

export function createCapacityWake(outerSignal: AbortSignal): CapacityWake {
  let wakeController = new AbortController()

  function wake(): void {
    wakeController.abort()
    wakeController = new AbortController()  // fresh controller for next sleep
  }

  function signal(): CapacitySignal {
    const merged = new AbortController()
    // Merge shutdown signal and capacity signal
    // Whichever fires first, the merged signal aborts
    outerSignal.addEventListener('abort', abort, { once: true })
    wakeController.signal.addEventListener('abort', abort, { once: true })
    return { signal: merged.signal, cleanup }
  }
}
```

The poll loop uses two intervals:

```typescript
// src/bridge/pollConfigDefaults.ts

const POLL_INTERVAL_MS_NOT_AT_CAPACITY = 2000      // actively seeking work
const POLL_INTERVAL_MS_AT_CAPACITY = 600_000        // 10 minutes — just a liveness signal
```

Not-at-capacity: poll every 2 seconds to pick up work quickly. At-capacity: poll every 10 minutes — not to pick up work (the transport handles that), but as a liveness signal to prevent the Redis key from expiring (TTL is 4 hours; 10-minute poll gives 24× headroom).

**What to change today:** If your agent handles streaming messages or session bridging, implement a flush gate pattern before you need it. The bugs from interleaved messages during flush are difficult to reproduce and difficult to debug. The gate is simple enough to add proactively.

---

## What These 9 Patterns Have in Common

Looking across them:

**1. Architecture enforces constraints that prompts cannot.** The verification agent can't edit files because the tool isn't available — not because it was instructed not to. Permission defaults are fail-closed. Denial limits are hardcoded constants. Instructions drift; architecture holds.

**2. Naming makes costs visible.** `DANGEROUS_uncachedSystemPromptSection`, `checkStatsigFeatureGate_CACHED_MAY_BE_STALE`, `_reason` as a required-but-unused parameter. The naming convention is the documentation. Engineers can't accidentally cache-break or cache-hit without the code making it obvious.

**3. Failure modes are explicit, not implicit.** The verification agent's system prompt names the two ways it fails. The denial circuit breaker has exact numeric thresholds from production incidents. The flush gate has a `deactivate()` path specifically for transport replacement. These aren't defensive programming — they're the result of things going wrong in production, being understood, and being fixed specifically.

**4. Fresh and resumed are always distinguished.** Swarm initialization, task IDs, session bridging — every stateful component explicitly handles both the fresh-start and the resume case. This is the difference between a system that works in demos and a system that works in production.

**5. Context placement is intentional.** CLAUDE.md in the user turn, git status in the system prompt, critical reminders in a separate injection field. Where context lands determines how reliably it's attended to. The middle of context is where information goes to be forgotten (Liu et al., Stanford 2024). Every piece of information has a deliberate placement.

---

## The Reference Library

These patterns are extracted and organized into an open-source reference library with audit checklists and skills for Claude Code, Cursor, Codex CLI, Gemini CLI, Windsurf, Aider, and Continue.dev:

**[github.com/sarkar-ai-taken/agent-loop-learning](https://github.com/sarkar-ai-taken/agent-loop-learning)**

Three slash commands available in any Claude Code session pointed at the repo:

```
/review-agent    → full audit against 9 dimensions with ✅/⚠️/❌ scorecard
/improve-agent   → targeted improvement cards for a specific component
/best-practices  → load a reference doc by topic keyword
```

---

*All code excerpts are from the Claude Code source. All source paths reference the April 2026 codebase.*
