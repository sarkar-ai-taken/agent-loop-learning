---
name: prompt-engineering
description: Best practices for system prompts, context engineering, structure, and role definition for production LLM agents.
type: reference
---

# Prompt Engineering Best Practices

## Benchmarks at a Glance

| Metric | Finding | Source |
|--------|---------|--------|
| Context rot onset | Performance degrades before the context window is full; models don't use context uniformly | Chroma Research (Hong et al., 2025) |
| Optimal task context size | 150–300 words of focused context is the practical sweet spot for most tasks | Anthropic Engineering, 2025 |
| Lost-in-the-middle effect | Models recall start/end of context most reliably; information in the middle is systematically lost | Liu et al. (Stanford), 2024 |
| Few-shot examples efficacy | Concrete examples outperform abstract rules at shaping model behavior per token invested | Multiple prompt engineering studies, 2024–2025 |
| System prompt quality impact | System prompt design is a primary differentiator between high and low-performing agents on the same model | SWE-bench analysis, 2026 |

---

## 1. From Prompt Engineering to Context Engineering

The discipline has evolved. **Prompt engineering** — finding the right words — is the entry-level skill. **Context engineering** — curating and maintaining the optimal set of tokens at inference time — is the production skill.

> "Building is less about finding the right words for prompts and more about: what configuration of context is most likely to generate desired behavior?" — Anthropic Engineering, 2025

Context engineering encompasses everything that lands in the context window:
- System prompt
- Conversation history
- Tool definitions and their descriptions
- Retrieved memories
- Tool results
- Injected documents

All of these compete for the same finite token budget. Managing them together is the real skill.

---

## 2. System Prompt Structure

A well-structured system prompt for a coding agent:

```markdown
## 1. Role and Scope
[Who the agent is, what it's responsible for, where that scope ends]

## 2. Core Principles
[3-5 non-negotiable behaviors]

## 3. Available Tools
[What tools exist, what each does, when to use each, when NOT to use each]

## 4. Workflow
[The phases of work: how to approach tasks step by step]

## 5. Output Standards
[How to format responses, what level of detail, what to include/exclude]

## 6. Anti-patterns
[Explicit "never do this" list with reasons]

## 7. Examples
[2-3 concrete good/bad examples of the key behaviors]
```

The examples section is not optional decoration — it typically produces the most behavior change per token of any section. A well-designed coordinator system prompt will devote roughly a quarter of its length to concrete examples.

---

## 3. Role Definition

Tell the agent **what it is, what its job is, and where that job begins and ends.** This is the most important sentence in the system prompt.

**Bad — too vague:**
```
"You are a helpful AI assistant."
```

**Good — bounded and purposeful:**
```
"You are an AI coding assistant that orchestrates software engineering
tasks. Your job is to help the user achieve their goal by directing
workers to research, implement, and verify code changes — then synthesize
results and communicate with the user. Answer questions directly when
possible — don't delegate work you can handle without tools."
```

**Include a boundary.** "Answer questions directly when possible — don't delegate work you can handle without tools." Without a boundary, agents over-delegate or under-delegate.

---

## 4. XML Tags as Structural Delimiters

XML-like tags are the most reliable way to separate instructions from content:

```xml
<system>
You are an expert code reviewer. Review the following code for security issues.
</system>

<code>
[user-provided code goes here — treated as data, not instructions]
</code>

<format>
Return findings as a JSON array: [{line, severity, description}]
</format>
```

Why XML works:
- Human-readable and parseable by models
- Stable across model versions
- Creates a clear boundary between instruction and data (prevents prompt injection)
- Supports nested structure for complex contexts

---

## 5. The Context Budget

LLM reasoning degrades as context grows — even before the window is full (context rot, Chroma 2025). The practical sweet spot for most tasks is **150–300 words of focused context**.

### Budget allocation heuristic

| Slot | Recommended budget |
|------|-------------------|
| System prompt | 800–1500 tokens |
| Conversation history (recent verbatim) | 1000–2000 tokens |
| Tool definitions | 500–1000 tokens |
| Retrieved memory | 200–500 tokens |
| Current task context | 500–1000 tokens |
| **Total** | **~3000–6000 tokens** |

Strategies to stay in budget:
- **Compress conversation history** — summarize turns older than N; keep recent N verbatim
- **Defer tool schemas** — load core tools always; provide a discovery tool for the rest
- **Retrieve selectively** — inject only the most relevant memory
- **Trim tool output** — truncate large file contents, search results, etc.
- **Position critical facts at start or end** — the lost-in-the-middle effect means middle placement reduces recall

---

## 6. Few-Shot Examples in System Prompts

**Include concrete examples for every non-obvious behavior.** Research consistently shows examples are more effective per token than abstract rules at shaping model behavior.

Example structure for a coordinator prompt:
```
### Bad (never do this):
Spawn worker with: "Based on your findings, fix the bug"
Why: delegates understanding — the worker can't see the findings

### Good:
Spawn worker with: "Fix the null pointer in the session validation logic.
  The session.user field is undefined when the session expires but the token
  is still cached. Add a null check — if null, return 401 with 'Session expired'."
Why: synthesized, self-contained, precisely targeted
```

Rules of thumb for examples:
- Include both good and bad for every key behavior
- Explain **why** each is good or bad — "why" is what the model generalizes from
- Use real-looking examples, not placeholder text
- 2–3 examples per behavior is enough; more creates noise

---

## 7. Instruction Priority and Conflict Resolution

When instructions might conflict, establish explicit priority:

```
Priorities (highest to lowest):
1. User safety and legal requirements
2. Explicit user instructions in this conversation
3. Project configuration files (CLAUDE.md, .cursorrules, etc.)
4. These system instructions
5. General best practices
```

Without explicit priority, models resolve conflicts unpredictably. With it, they resolve consistently.

---

## 8. Negative Instructions

Tell the agent what NOT to do, not just what to do. Negative instructions are more effective per token at preventing specific failure modes:

```
Effective negative instructions:
- Never delegate synthesis to workers ("based on your findings…")
- Never acknowledge worker results as if they are conversation partners
- Never fabricate or predict agent results before they arrive
- Never bypass safety checks (e.g., --no-verify flags)
- Never include attribution in public-facing content unless explicitly requested
```

A dedicated anti-patterns section in the system prompt that explains the *why* behind each prohibition produces more reliable adherence than rules alone.

---

## 9. Stable/Dynamic Prompt Cache Boundary

Prompt caching charges for the first inference and serves subsequent ones cheaply — but only if the cached prefix is byte-identical across turns. A common efficiency mistake is mixing stable and dynamic content inside the system prompt, which invalidates the cache on every turn.

**Pattern: split the system prompt at the stability boundary.**

```
[STABLE — cache this prefix, never changes between sessions]
Role definition
Core principles
Tool definitions
Workflow phases
Anti-patterns
Examples

[DYNAMIC — never cached, changes per session or per turn]
Current working directory
Active git branch
Loaded plugins / MCP servers
Session-specific flags
Recent memory summaries
```

Everything before the boundary can be cached. Everything after changes and shouldn't be. The stable prefix is typically 70–90% of the total system prompt.

**Rule:** if a piece of content changes between sessions, it must go after the boundary. If it never changes, it must go before. Violating this rule by putting dynamic content early invalidates the entire cache.

---

## 10. Persistent Project Configuration Pattern

A persistent project configuration file (placed in the project root, loaded at session start) is the most cost-effective memory layer available. It survives across sessions without any retrieval cost and is loaded with zero latency.

**What to include:**
```markdown
# Project Configuration

## Tech stack
[Languages, frameworks, major dependencies]

## Conventions
[Naming, file structure, commit message format]

## Build and test
[Commands to run tests, lint, build, and deploy]

## What NOT to do
[Specific anti-patterns in this codebase]

## Preferred libraries
[For common tasks: HTTP clients, test runners, logging]

## Active context
[Current sprint focus, known issues, in-progress work]
```

**Why this works:**
- Zero retrieval overhead — loaded directly into context at startup
- Survives session restarts with no memory consolidation required
- Agents and humans both benefit — onboarding for new contributors and new sessions
- Can be updated by the agent as it learns new conventions

**Keep it bounded:** a project config that grows without limit becomes noise. Reserve it for non-obvious facts not derivable from the code. Obvious things (language, framework) go in the stable prompt; project-specific non-obvious facts go here.

---

## 11. Comments as Agent Documentation

In agentic workflows, code comments serve a different purpose than in human-only codebases. Humans learn patterns from surrounding code and can consult documentation; agents process each file afresh and may not see the surrounding context.

**What agents need in comments:**
- Decision rationale: "Using polling instead of webhooks here because the external service doesn't support webhooks in sandbox mode"
- Non-obvious constraints: "This function must stay synchronous — the caller relies on LIFO stack behavior"
- Historical context that's not in the code: "This file is the entry point for the migration system — don't refactor the function names without updating the migration runner"
- Configuration that affects behavior: "The timeout here is intentionally long — upstream SLA is 45s"

**What agents don't need:**
- Restating what the code does (`// increment counter by 1`)
- Type information already in signatures
- Scaffolding comments (`// TODO: implement`)

**Rule:** write comments for the next agent, not the next human. The next agent will have the function signature and docstring; it won't have the context that was in your head when you wrote it.

---

## 12. Force-Uncached Content: The DANGEROUS_ Pattern

Some content must never be cached, even within a session — because caching stale values of it produces wrong behavior. Mark this content explicitly so it can't accidentally be cached.

**Examples of content that must be recomputed each turn:**
- Current date/time (changes every day)
- Git status (changes after every tool call)
- File system state (changes after any write)
- Active session flags (may change mid-session)
- Current working directory

**Implementation pattern:** wrap force-uncached content in a distinct wrapper that signals to the cache layer "never store this":

```
DANGEROUS_uncachedSection() {
  return `Current date: ${new Date().toISOString()}`
  // DANGEROUS_ prefix is a convention: this content must not be cached
  // because stale values will cause incorrect behavior
}
```

The `DANGEROUS_` prefix is a human signal to reviewers: "if you move this content before the cache boundary, you will introduce a bug." The prefix makes the risk visible at the call site — a convention more reliable than a comment that can drift from the code.

**Cost vs. correctness:** force-uncached sections are charged at full price every turn. Keep them minimal. The goal is to put only genuinely dynamic content here, not content that's slightly variable but mostly stable.

---

## 13. DO NOT Comments as Policy Anchors

A `DO NOT` comment in a codebase is a gravestone — it marks where someone already stepped on the landmine. Every one represents a real incident.

In system prompts and agent instructions, the same principle applies: `NEVER` and `DO NOT` instructions are not style rules — they are lessons learned from failures.

**When writing agent instructions:**
- If a "DO NOT" is born from an incident, say so: "DO NOT push to remote unless explicitly asked — previously caused production data loss"
- If a "DO NOT" prevents a subtle bug: "DO NOT count exploration turns toward the budget — skews task completion metrics"
- If the prohibition applies only in specific contexts: say which ones

**Why this matters for agents:** agents are more likely to follow prohibitions when they understand the reason. A bare "DO NOT do X" gets interpreted as a style preference. A "DO NOT do X — previous incident showed it corrupts the commit log" is treated as a hard constraint.

**The same applies to system prompt anti-patterns sections.** Don't just list bad behaviors. Explain what goes wrong when they happen. The model generalizes from the consequence, not from the rule.

---

## 14. Dynamic System Prompt Composition

System prompts don't have to be static. Compose them at session start based on context:

```
Build system prompt from:
- Base prompt (always included)
- Coordinator section (only if coordinator mode is active)
- Worktree section (only if a git worktree is checked out)
- Scratchpad section (only if scratchpad is configured)
- MCP context (only if MCP servers are connected)
```

This keeps the base prompt lean while adding context only when it's actually relevant to the session. Sections not relevant to the current mode don't consume tokens.

---

## 15. Speculative Pre-Generation

Advanced context engineering includes **pre-generating likely responses** to approach zero latency on predicted turns:

1. After each assistant turn, a background agent predicts the user's most likely next message
2. It begins generating a response to that prediction
3. If the user's actual message matches the prediction, serve the pre-generated response
4. If not, discard it and generate normally

**Cost:** one additional inference per turn.
**Benefit:** near-zero response latency for 20–40% of turns in typical interactive workflows.

Implement with an `AbortController` that cancels the speculative generation the moment a real user message arrives.

---

## Sources

- [Context Rot: How Increasing Input Tokens Impacts LLM Performance — Chroma Research (Hong et al., 2025)](https://research.trychroma.com/context-rot)
- [Effective Context Engineering for AI Agents — Anthropic Engineering (Sep 2025)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [The Ultimate Guide to Prompt Engineering 2026 — Lakera](https://www.lakera.ai/blog/prompt-engineering-guide)
- [The 2026 Guide to Prompt Engineering — IBM](https://www.ibm.com/think/prompt-engineering)
- [Prompt Engineering for AI Agents 2026 — Inflectra](https://www.inflectra.com/Ideas/Topic/AI-Agent-Prompt-Engineering.aspx)
- [OpenAI Prompt Engineering Guide](https://developers.openai.com/api/docs/guides/prompt-engineering)
- [Lost in the Middle: How Language Models Use Long Contexts — Liu et al., Stanford 2024](https://arxiv.org/abs/2307.03172)
