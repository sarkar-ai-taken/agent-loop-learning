---
name: tool-design
description: Best practices for designing, naming, and implementing tools that LLM agents can use reliably and safely.
type: reference
---

# Tool Design Best Practices

## Benchmarks at a Glance

| Metric | Finding | Source |
|--------|---------|--------|
| Tool design impact on agent quality | Scaffolding quality (including tool design) explains same-model score gaps of 17 issues on 731 SWE-bench problems | SWE-bench leaderboard, Feb 2026 |
| Agent failures due to tool misuse | Tool misuse is OWASP #5 agentic risk; tools with poor descriptions are the primary cause | OWASP Top 10 for Agentic Applications, 2026 |
| Context used by tool definitions | Tool schemas and descriptions compete directly with the task context budget | Anthropic Engineering, 2025 |
| Multi-agent tool access | Workers given access to specialized tools outperform workers with only general tools | LangChain multi-agent benchmarks, 2025 |

---

## 1. The Tool Contract

Every tool makes a contract with the agent. A good tool contract has:

1. **A precise, unambiguous name** — the agent uses the name to decide when to call it
2. **A description that includes when NOT to use it** — as important as when to use it
3. **A minimal, typed input schema** — only required parameters; no optional sprawl
4. **Predictable, structured output** — the agent must be able to parse and act on results
5. **Fail loudly with useful error messages** — silent failures create phantom successes

---

## 2. Naming Conventions

Tool names directly influence when the model calls them. Invest in naming.

| Principle | Bad | Good |
|-----------|-----|------|
| Verb + noun | `files` | `FileRead`, `FileEdit`, `FileWrite` |
| Specific action | `search` | `GrepContent` (content search), `GlobFiles` (file pattern) |
| No ambiguity between similar tools | `run`, `execute` | `BashExec`, `REPLEval`, `PowerShellExec` |
| Match mental model | `get_file` | `FileRead` |
| Destructive action visible in name | `manage_file` | `FileDelete` |

**Split tools that do two different things.** A content search tool and a file-pattern search tool look similar but serve different needs. Separate tools prevent the model conflating them, which is a common source of tool-selection errors.

---

## 3. Input Schema Design

**Bad — too permissive, agent has to guess the format:**
```json
{
  "type": "object",
  "properties": {
    "input": { "type": "string" }
  }
}
```

**Good — explicit, leaves no room for misinterpretation:**
```json
{
  "type": "object",
  "required": ["file_path", "old_string", "new_string"],
  "properties": {
    "file_path": {
      "type": "string",
      "description": "Absolute path to the file to modify"
    },
    "old_string": {
      "type": "string",
      "description": "The exact text to replace (must be unique in the file)"
    },
    "new_string": {
      "type": "string",
      "description": "The text to replace it with"
    },
    "replace_all": {
      "type": "boolean",
      "default": false,
      "description": "Replace all occurrences (default: first only)"
    }
  }
}
```

### Schema rules
- Mark every required field as `required`
- Use `description` on every field — the agent reads these at inference time
- Provide `default` values for optional fields
- Constrain strings with `enum` when valid values are finite
- Use `minimum`/`maximum` for numeric fields
- Never make a required field ambiguous between two meanings

---

## 4. Output Design

Tool output goes directly into the LLM's context. Design it for the model, not for humans.

**Principles:**
- **Token-efficient** — return only what the agent needs; trim noise
- **Structured when possible** — JSON or delimited output the agent can parse
- **Error messages include the fix hint** — "File not found: /foo/bar (did you mean /foo/baz?)"
- **Truncate large outputs** with a clear signal: "Output truncated at 5000 chars. Use offset/limit params to page."
- **Never silently swallow errors** — an empty success is worse than an informative failure

File read tools that return content with line numbers are better for agentic use than plain content, because the model can reference specific lines in follow-up edits without re-reading.

---

## 5. Permission Gating

Every tool that modifies state (files, network, shell) must be permission-gated. Each tool should have an explicit pre-execution permission check:

**Permission tiers (least to most dangerous):**

| Tier | Actions | Default approval |
|------|---------|-----------------|
| 0 | Read project files, search content | Always allowed |
| 1 | Read arbitrary local files | Allowed by default |
| 2 | Write/edit project files | Confirm once per session |
| 3 | Shell execution (bounded scope) | Confirm; show exact command |
| 4 | Network calls | Confirm; show URL |
| 5 | Destructive operations | Confirm every time; show what is destroyed |
| 6 | Operations outside project scope | Require explicit session flag |

Never auto-approve a tool that modifies state outside the declared project scope. Never skip confirmation for destructive operations.

---

## 6. Tool Descriptions That Work

The description is the most important part of a tool definition — the model decides when to call a tool almost entirely from its description.

**Bad description:**
> "Read a file."

**Good description:**
> "Read a file from the local filesystem. Use this to read any file the user might reference. Results are returned with line numbers. Reads up to 2000 lines by default; use offset and limit for large files. Does not work for directories — use GlobFiles to list directory contents. Do NOT use this when a more specific tool is available."

**Include in every description:**
- What the tool does
- When to use it vs. alternatives
- **When NOT to use it** (most important and most overlooked)
- Output format
- Any limits or gotchas

The "When NOT to use" section prevents the most common agent tool-selection errors.

---

## 7. Dedicated Tools Beat General-Purpose Shell for Everything

If a specific tool exists for a task, the agent should use it instead of a general-purpose shell command. Why:
- The dedicated tool has known, predictable output format
- It can enforce permissions cleanly
- It appears in audit logs as a specific, auditable action
- It can't accidentally execute adjacent dangerous operations

Enforce this in the system prompt: explicitly list every case where a dedicated tool exists and instruct the agent to prefer it over shell fallbacks.

---

## 8. Structured Output Mode

For programmatic/non-interactive use cases, provide a way for the agent to produce machine-readable output distinct from its conversational output. This allows callers to parse results reliably rather than scraping prose.

This is especially important for agents called via API or in automation pipelines where downstream systems need structured data.

---

## 9. Tool Security Classification Properties

Every tool should declare six security properties as part of its definition. These properties drive automatic safety decisions without requiring per-call analysis:

| Property | What it means | Who uses it |
|----------|--------------|-------------|
| `isConcurrencySafe` | Can run in parallel with other tools | Tool orchestrator (parallel vs. serial scheduling) |
| `isReadOnly` | Does not modify any state | Permission layer (skip confirmation for read-only) |
| `isDestructive` | Action is irreversible | UI layer (extra confirmation, epitaph warning) |
| `interruptBehavior` | `cancel` or `block` on user interrupt | Task manager (clean vs. wait-for-finish) |
| `isOpenWorld` | Involves external systems | Network policy layer |
| `toAutoClassifierInput` | Compact one-line representation of call | Safety classifier (compressed context for quick judgment) |

**toAutoClassifierInput** is the most subtle. It compresses a tool invocation — including the arguments — into a single line that a safety classifier can evaluate cheaply without loading the full tool context. Example: `ls -la /project/src`. The classifier sees that string and makes a binary safe/unsafe judgment.

**isDestructive** is the most important. Tools returning true trigger: confirmation prompts, epitaph warnings ("Note: may overwrite remote history"), and mandatory reversibility checks. The system repeats "measure twice, cut once" for these tools.

A tool that lacks these properties cannot participate in automated safety decisions — it will either always require confirmation or always bypass checks. Neither is correct.

---

## 10. Streaming Tool Execution

Don't wait for the full model response before starting tool execution. Start executing tool calls as their blocks arrive in the stream.

**Standard (wasteful):**
```
Wait for full response → Parse all tool calls → Execute serially
```

**Streaming (optimal):**
```
[tool_use block #1 arrives] → Start executing immediately
[tool_use block #2 arrives] → Start executing immediately
[tool_use block #3 arrives] → Start executing immediately
[response complete] → Buffer results in arrival order → Return all
```

**Benefits:**
- Tool execution overlaps with the tail of model generation
- Parallel tool calls run truly in parallel (not sequentially queued)
- Latency reduction proportional to the number of concurrent tool calls

**Sibling abort:** if one tool in a parallel batch errors, abort all sibling tool processes immediately via a shared cancellation signal. Don't wait for the others to complete — they'll produce results for a task that already failed. Continue the query loop with the error result so the agent can recover.

---

## 11. Tool Indexing and Deferred Loading

When a system has 40+ tools, loading all schemas into every context wastes tokens and degrades reasoning. A better pattern:

1. Load a small core set always (10–15 tools covering the most common operations)
2. Provide a search/discovery tool for the rest
3. The model fetches the full schema for a deferred tool before calling it

This prevents the "tool list longer than the task" problem, where tool definitions consume a disproportionate share of the context budget.

---

## 12. Tool Composition Anti-Patterns

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| One tool that does everything | Agent can't target specific behavior | Split by action and scope |
| Side effects not visible in the name | Agent doesn't know it's destructive | Name destructively: `FileDelete`, not `FileManage` |
| Tool that requires reading another tool's output to use | Creates implicit ordering | Make each tool independently usable |
| Required params the agent won't always know | Agent hallucinates values | Make those params optional with sensible defaults |
| Silent partial failure | Agent believes task is done | Return partial success status explicitly |
| Tool description with no "when NOT to use" | Model uses it in wrong contexts | Always include disambiguation guidance |

---

## Sources

- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [Effective Context Engineering for AI Agents — Anthropic Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [SWE-bench Verified Leaderboard — swebench.com](https://www.swebench.com/)
- [AI Agent Security Best Practices — IBM](https://www.ibm.com/think/tutorials/ai-agent-security)
- [OpenAI Agents SDK — Tool design](https://openai.github.io/openai-agents-python/multi_agent/)
- [Benchmarking Multi-Agent Architectures — LangChain Blog](https://blog.langchain.com/benchmarking-multi-agent-architectures/)
