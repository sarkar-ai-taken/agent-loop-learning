# /improve-agent

Generate targeted, benchmark-backed improvement recommendations for a specific agent component or the full agent system.

**Works for any LLM agent framework** — LangChain, LangGraph, AutoGen, CrewAI, OpenAI Agents SDK, Semantic Kernel, custom loops, etc. All recommendations are framework-agnostic unless the user asks for framework-specific code.

## Usage

```
/improve-agent                        → full system improvement pass
/improve-agent orchestration          → focus on multi-agent design
/improve-agent prompting              → focus on prompt structure
/improve-agent memory                 → focus on context & memory
/improve-agent tools                  → focus on tool design
/improve-agent verification           → focus on testing & verification
/improve-agent security               → focus on security & permissions
/improve-agent performance            → focus on startup & latency
/improve-agent <paste code/design>    → targeted review of what's pasted
```

## Instructions

1. If a topic keyword is provided, read only the relevant best-practice doc(s):
   - `orchestration` → `01-multi-agent-orchestration.md`
   - `prompting` → `02-worker-prompting.md` + `07-prompt-engineering.md`
   - `memory` → `03-context-and-memory.md`
   - `tools` → `04-tool-design.md`
   - `verification` → `05-verification-and-testing.md`
   - `security` → `06-security-and-permissions.md`
   - `performance` → `08-performance-and-startup.md`
   - No keyword → read all 9 docs

2. **Explore the current repo first** — do not ask the user for anything yet. Search for agent-related code:
   - Files matching `*agent*`, `*tool*`, `*prompt*`, `*chain*`, `*workflow*` in `src/`, `lib/`, `app/`, root
   - Imports of agent frameworks: `langchain`, `langgraph`, `openai`, `anthropic`, `autogen`, `crewai`
   - System prompt definitions, tool definitions, agent loop logic
   - `CLAUDE.md`, `AGENTS.md`, or any README describing the agent architecture
   Read the relevant files to understand the current state before producing recommendations. Only ask the user if no agent code can be found after exploring.

3. Produce improvement recommendations in this format:

---

### Improvement Plan: [component or "Full System"]

**Context** (1–2 sentences summarizing what the agent currently does)

---

#### Recommended improvements (prioritized)

For each improvement, use this card format:

**[Short title]**
- **Current state**: what the agent does now (or doesn't do)
- **Recommended change**: the specific improvement
- **Benchmark justification**: cite the number that motivates this (e.g. "+26% accuracy, 90% fewer tokens — agentic RAG vs traditional RAG, 2025")
- **Implementation sketch**: pseudocode or pattern, framework-agnostic unless asked otherwise
- **Effort**: Low / Medium / High

---

4. After the improvement cards, add a **Quick wins** section: 1–3 changes that take under an hour and have high impact.

5. If the user's agent uses a specific model family (GPT, Gemini, Llama, Claude), note which optimizations are model-specific.

6. Do not suggest adding frameworks or dependencies unless they directly address a gap — preference is always for the simplest change that achieves the goal.
