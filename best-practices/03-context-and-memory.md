---
name: context-and-memory
description: Best practices for managing context windows, memory tiers, consolidation pipelines, and retrieval in LLM agent systems.
type: reference
---

# Context and Memory Best Practices

## Benchmarks at a Glance

| Metric | Finding | Source |
|--------|---------|--------|
| Context rot — models tested | **18 frontier LLMs** — universal, not model-specific | Chroma (Hong et al., 2025) |
| Context degradation threshold | At **50K tokens even with a 1M token window** | Chroma / Morph, 2025 |
| Effective context — Gemini 2.5 Pro, GPT-5 | ~**200K tokens** before significant degradation | Benchmarking, early 2026 |
| Effective context — Claude Sonnet 4 (Thinking) | ~**60K–120K tokens** | Benchmarking, early 2026 |
| Lost-in-the-middle accuracy drop | **~30%+** for information in the middle of context | Liu et al. (Stanford), 2024 |
| 20-step agent at 95% per-step reliability | Only **36% end-to-end success** (compounding) | Math |
| Agentic RAG vs. traditional RAG | **+26% accuracy, 90% fewer tokens** | Multiple 2025 sources |
| Hindsight agentic memory accuracy | **91.4%** on LongMemEval | Vectorize.io / Virginia Tech, 2025 |
| Observational memory vs. standard RAG | **+4.18 pp accuracy, ~10× cost reduction** | VentureBeat / 2025 study |
| LongMemEval commercial system drop (hard setting) | **30–60% performance drop** from simple to hard | LongMemEval (ICLR 2025) |
| Memory compression efficiency | **89–95%** with maintained correctness | Mem0 (arxiv 2504.19413) |

---

## 1. Context Is a Finite, Degrading Resource

Context rot — the measurable degradation of LLM output quality as input length grows — is an **architectural property** of transformer-based attention, not a capability gap that training solves. Chroma's 2025 study measured 18 LLMs and found that "models do not use their context uniformly; instead, their performance grows increasingly unreliable as input length grows."

Anthropic's engineering team stated: "you must treat context as a limited resource with decreasing returns. Models have an attention budget — the amount of context they can focus on without losing the original intention."

Key principles:
- **Treat context as a budget.** Every token either helps or costs performance.
- **Start fresh for new tasks.** Don't carry conversation history from one unrelated task into another.
- **Compress aggressively.** Summarize old turns into concise memory objects rather than truncating; key facts must survive summarization.
- **Beware the middle.** Information at the start and end of context is recalled most reliably; inject critical facts at these positions.

---

## 2. The Four Memory Tiers

Agent memory mirrors human cognition. A well-designed system separates:

| Tier | What it stores | Lifespan | How accessed |
|------|---------------|----------|--------------|
| **Working / in-context** | Current task state, recent turns | Single session | Already in context |
| **Episodic** | What happened in past sessions | Days to months | Retrieval from session logs |
| **Semantic** | Facts, preferences, learned knowledge | Persistent | Retrieval + memory files |
| **Procedural** | How to do recurring tasks | Persistent | Skill definitions, reusable prompts |

Each tier requires a different storage and retrieval strategy. Conflating them leads to context bloat or knowledge loss.

---

## 3. Memory Extraction (Inline)

During a session, extract atomic facts worth preserving **immediately** when they occur — don't batch at the end.

**What to extract:**
- User preferences and working style
- Architectural facts not easily derivable from code
- Decisions made and their rationale
- Corrections the user gave you (most important)
- Confirmed non-obvious approaches

**What NOT to extract:**
- Things already in the codebase (read the code instead)
- Git history (version control is authoritative)
- Ephemeral task details that won't apply next session
- Obvious language/framework conventions

**Format for every memory entry:**
- Lead with the rule/fact
- Follow with **Why:** (the reason — often a past incident or strong preference)
- Follow with **How to apply:** (when this guidance kicks in)

This structure lets future sessions judge edge cases instead of blindly following stale rules.

---

## 4. Background Memory Consolidation

Periodic consolidation turns episodic memory (session logs) into durable semantic memory. This should run as a background process, not blocking the main session.

### Gate conditions (evaluate cheapest first)
1. **Time gate** — minimum hours since last consolidation (e.g., 24h default)
2. **Session gate** — minimum new sessions since last consolidation (e.g., 5 sessions default)
3. **Lock** — no other consolidation process currently running

### Consolidation phases
1. **Orient** — read existing memory index to understand current state
2. **Gather** — scan new session transcripts for signals worth preserving
3. **Consolidate** — update durable memory files with new learnings
4. **Prune** — remove stale or superseded entries to keep the index bounded

### Constraints during consolidation
- **Read-only access** — the consolidation agent must not modify project files
- **Sandboxed scope** — access only the memory directory and session transcripts
- **Background execution** — run as a forked subagent so the user session continues unblocked

---

## 5. The 3-Layer Memory Architecture

The most bandwidth-efficient memory architecture uses three tiers with radically different access patterns:

| Layer | What it contains | When loaded | Cost |
|-------|-----------------|-------------|------|
| **Index** | One-line pointers, ~150 chars each | Every session, always | ~0 (tiny) |
| **Topic files** | Full knowledge on a specific subject | On demand, when relevant | Medium |
| **Session transcripts** | Raw conversation logs | Never loaded directly | ~0 (grep only) |

**Index** — always loaded. Never stores content, only pointers:
```
- [Auth conventions](auth.md) — JWT strategy, session expiry, refresh token handling
- [Testing patterns](testing.md) — integration tests must use real DB, not mocks
- [Project context](project.md) — migration deadline 2026-05-01, mobile-first priority
```

**Topic files** — loaded only when the index pointer is relevant to the current task. Each file contains complete, detailed knowledge on one subject. The agent reads the index, identifies relevant topics, loads those files — and doesn't load the rest.

**Session transcripts** — raw conversation logs from past sessions. Never loaded into context. Accessed only via grep for specific facts. The index and topic files are the distilled form; transcripts are the raw material for consolidation only.

**Write discipline:**
1. Write new knowledge to the relevant topic file
2. Update the index pointer if the topic file is new or its summary changed
3. Never write knowledge content directly into the index

**Bandwidth-awareness principle:** loading everything into context every turn is expensive and introduces noise. The 3-layer design ensures the agent pays for only what it uses — the index is always cheap, topic files are fetched selectively, transcripts are never loaded.

---

## 6. Memory Is a Hint, Not Truth

Memory records reflect what was true when they were written. Before acting on a memory, verify it against the current state of the code or resource:

- Memory says "function X does Y" → read the function before relying on this
- Memory says "file Z exists at path" → check the file before citing it
- Memory says "team uses library A" → verify the dependency file

A stale memory that sends the agent in the wrong direction costs more than a cache miss. The rule: **trust the code over the memory; trust live state over cached state.** Memory is useful for narrowing search space, not for replacing verification.

---

## 7. Memory File Structure

```
memory/
├── MEMORY.md           # Index — one-line pointer per memory file, max ~200 lines
├── user_role.md        # Who the user is, their expertise, preferences
├── feedback_testing.md # What to do/avoid in tests
├── project_auth.md     # Auth rewrite context and rationale
└── reference_tickets.md # Where to find bugs, tickets, etc.
```

### MEMORY.md as an index (not storage)
The index is always loaded into every conversation. Keep it tight:
- Each entry: one line, under ~150 characters
- Format: `- [Title](file.md) — one-line hook`
- Never write memory content directly into the index
- After ~200 entries, start consolidating

### Memory file frontmatter
```markdown
---
name: feedback_testing
description: Guidance on integration tests — must hit real database not mocks
type: feedback
---

Do not mock the database in integration tests.

**Why:** Past incident where mock/prod divergence masked a broken migration.
**How to apply:** When writing or reviewing any test that touches data persistence.
```

---

## 8. Retrieval Best Practices

When memory must be retrieved (rather than kept fully in context):

### Retrieval scoring
A proper scoring function combines:
- **Semantic similarity** — is this memory relevant to the current topic?
- **Recency** — how recent is this memory?
- **Importance** — was this explicitly flagged as critical?

Recency alone misses critical facts. An older critical memory must be able to surface over a more recent casual one.

### Context budget for retrieval
Retrieved memories should be **summarized before injection**, not dumped raw. Mem0's production study (2025) shows 89–95% compression rates are achievable while maintaining correctness — a 500-token retrieved excerpt can often be compressed to 50 tokens without meaningful quality loss.

### RAG vs. agent memory distinction
- **RAG** — fetches external documents once per query; documents don't evolve
- **Agent memory** — maintains evolving state, user preferences, past decisions, learned procedures

Use RAG for static reference material. Use agent memory for anything that should change based on interactions.

---

## 9. The Context Management Pipeline

Context management is not a single operation — it's a layered pipeline. Each layer solves a specific problem, and the order matters:

```
raw messages
  → applyToolResultBudget   (persist oversized tool results to disk, replace with pointer)
  → snipCompact             (clip old intermediate messages that are no longer load-bearing)
  → microCompact            (compress individual tool-result contents from compactable tools)
  → contextCollapse         (granular context collapse — preserves structure)
  → autoCompact             (full-conversation compaction — last resort)
  → normalizeMessagesForAPI (format into API-compatible structure)
```

**Why order matters:**
- `microCompact` runs before `autoCompact` — if micro-compaction frees enough space, full compaction is unnecessary and doesn't destroy granular structure
- Each layer runs on the output of the previous — a message cleared by snipCompact is not visible to microCompact
- Two systems cannot both run on the same context: if granular collapse is enabled, full compaction must be disabled or they compete and the coarser system wins

**MicroCompact tool whitelist:** not all tool results should be compacted. Compact only results from specific, re-runnable tools:

```
Compactable: Read, Bash, Grep, Glob, WebSearch, WebFetch, Edit, Write
Not compactable: Agent outputs (irreplaceable), task notifications, structured results
```

When a compactable result is cleared, replace with `[Old tool result content cleared]`. The model knows it can re-run the tool if needed. Agent outputs cannot be re-run — preserve them.

---

## 10. Memory Extraction Agent: Two-Turn Efficiency Constraint

Memory extraction after a session should follow a strict two-turn budget to avoid wasting tokens on overhead:

**Turn 1 — parallel reads:**
Issue all file reads simultaneously for every memory file that might need updating. Don't interleave reads with writes.

**Turn 2 — parallel writes:**
Issue all edits and writes simultaneously based on what was read in turn 1.

Alternating reads and writes (read one, write one, read another) wastes turns and is forbidden under a tight budget.

**No verification allowed:** the extraction agent must not grep source files, read code, or run git commands to verify what the user said. If the user said it, record it. Verification adds tool calls and rounds that exceed the budget. The tradeoff is efficiency over accuracy — stale or incorrect memories get corrected in the next consolidation cycle, not inline.

---

## 11. Session History Compaction

When conversation history grows long:

1. **Summarize, don't truncate** — truncation loses information silently; summarization can preserve key facts
2. **Preserve decisions and rationale** — "we chose JWT over sessions because of X" is load-bearing
3. **Mark tool results as compactable** — raw tool output (file contents, search results) is almost always safe to summarize away
4. **Keep the most recent N turns verbatim** — the model needs recency for coherence
5. **Force-position critical facts early or late in context** — the lost-in-the-middle effect means critical info placed in the middle is systematically under-attended

---

## 12. The Auto-Updating Document Pattern

Documents that should stay synchronized with the agent's evolving knowledge can be designated for **periodic auto-update**:

```markdown
# AUTO-MAINTAINED: Authentication Architecture
_Last updated by background agent — 2026-03-15_

[content maintained automatically]
```

A background subagent rewrites the document with new learnings from recent sessions. This externalizes knowledge from volatile context into a persistent artifact.

**When to use:** Architecture docs, decision logs, onboarding guides that should reflect current project state.

---

## 13. Anti-Patterns

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Full conversation history in every worker prompt | Context pollution, poor reasoning | Pass only the relevant excerpt |
| No consolidation, only growing memory index | Index grows unbounded, retrieval degrades | Prune and consolidate periodically |
| Storing code patterns in memory | Code is already in the repo | Read the code; memory is for non-derivable facts |
| Memory files without **Why:** fields | Future sessions can't judge edge cases | Always include rationale |
| Saving activity logs as memory | They go stale immediately | Save only the surprising/non-obvious insight |
| Injecting all retrieved memories | Context bloat degrades reasoning | Summarize and select; inject only what's relevant |

---

## Sources

- [Context Rot: How Increasing Input Tokens Impacts LLM Performance — Chroma Research (Hong et al., 2025)](https://research.trychroma.com/context-rot)
- [Context Rot: Why LLMs Degrade as Context Grows — Morph LLM](https://www.morphllm.com/context-rot)
- [Effective Context Engineering for AI Agents — Anthropic Engineering (Sep 2025)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Memory in the Age of AI Agents — arxiv 2512.13564](https://arxiv.org/abs/2512.13564)
- [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory — arxiv 2504.19413](https://arxiv.org/pdf/2504.19413)
- [Building Smarter AI Agents: AgentCore Long-Term Memory — AWS](https://aws.amazon.com/blogs/machine-learning/building-smarter-ai-agents-agentcore-long-term-memory-deep-dive/)
- [AI Agent Memory — IBM](https://www.ibm.com/think/topics/ai-agent-memory)
- [7 Steps to Mastering Memory in Agentic AI Systems — MachineLearningMastery](https://machinelearningmastery.com/7-steps-to-mastering-memory-in-agentic-ai-systems/)
