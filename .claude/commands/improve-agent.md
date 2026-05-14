# /improve-agent

**Goal: execute on issues found.** Apply concrete, benchmark-backed improvements to the agent in this repo.

There are two entry paths:
- **Findings already exist** (the user just ran `/review-agent`, pasted a review, or named specific issues) → skip straight to executing on those.
- **No findings yet** → first run the `/review-agent` flow internally to surface gaps, then execute on the top issues.

**Works for any LLM agent framework** — LangChain, LangGraph, AutoGen, CrewAI, OpenAI Agents SDK, Semantic Kernel, custom loops, etc. Recommendations are framework-agnostic unless the user asks for framework-specific code.

## Usage

```
/improve-agent                        → full system pass (review first if needed, then execute)
/improve-agent orchestration          → focus on multi-agent design
/improve-agent prompting              → focus on prompt structure
/improve-agent memory                 → focus on context & memory
/improve-agent tools                  → focus on tool design
/improve-agent verification           → focus on testing & verification
/improve-agent security               → focus on security & permissions
/improve-agent performance            → focus on startup & latency
/improve-agent <paste findings>       → execute on the pasted findings directly
```

## Instructions

1. **Check whether findings already exist in the conversation.**
   - If the user pasted a review, named specific issues, or just ran `/review-agent` — use those findings as the work list and skip to step 4.
   - Otherwise, continue to step 2 to generate them.

2. **Explore the current repo first** — do not ask the user for anything yet. Search for agent-related code:
   - Files matching `*agent*`, `*tool*`, `*prompt*`, `*chain*`, `*workflow*` in `src/`, `lib/`, `app/`, root
   - Imports of agent frameworks: `langchain`, `langgraph`, `openai`, `anthropic`, `autogen`, `crewai`
   - System prompt definitions, tool definitions, agent loop logic
   - `CLAUDE.md`, `AGENTS.md`, or any README describing the agent architecture

   Read the relevant files. Only ask the user if no agent code can be found after exploring.

3. **Run the `/review-agent` audit internally** to produce a gap analysis (same format as that command). Load only the docs relevant to the topic keyword if one was given:
   - `orchestration` → `01-multi-agent-orchestration.md`
   - `prompting` → `02-worker-prompting.md` + `07-prompt-engineering.md`
   - `memory` → `03-context-and-memory.md`
   - `tools` → `04-tool-design.md`
   - `verification` → `05-verification-and-testing.md`
   - `security` → `06-security-and-permissions.md`
   - `performance` → `08-performance-and-startup.md`
   - No keyword → read all 9 docs

   Show the user a short summary of the findings (not the full review) so they know what's about to change.

4. **Propose an execution plan** — a numbered list of the changes you intend to make, each tied to a finding and a file path. Use this card format:

   **[Short title]**
   - **Finding**: the gap this addresses
   - **Files to change**: concrete paths
   - **Change**: what you'll do
   - **Benchmark justification**: cite the number (e.g. "+26% accuracy, 90% fewer tokens — agentic RAG vs traditional RAG, 2025")
   - **Effort**: Low / Medium / High

5. **Get the user's go-ahead before editing.** For destructive or wide-blast-radius changes (dependency swaps, deleting modules, rewriting prompts in production paths), confirm explicitly. Small, reversible edits can proceed once the plan is shown.

6. **Execute the changes.** Use Edit/Write tools, keep the diff minimal, and verify each change works (run tests/typecheck if available). After each change, report what was modified.

7. **Quick wins**: if any change takes under an hour and has high impact, apply it first.

8. Do not suggest or install new frameworks/dependencies unless they directly address a gap — preference is always for the simplest change that achieves the goal.

9. If the user's agent uses a specific model family (GPT, Gemini, Llama, Claude), note which optimizations are model-specific before applying them.

10. **End with a summary**: which findings were resolved, which were deferred, and any follow-ups the user should run themselves.
