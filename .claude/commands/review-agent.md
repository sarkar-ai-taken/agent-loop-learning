# /review-agent

**Goal: review and show only.** Audit an agent design against the best-practice reference docs and surface findings. Do **not** modify any files, write code, or execute fixes. The user (or `/improve-agent`) decides what to do with the findings.

**Works for any LLM agent framework** — LangChain, LangGraph, AutoGen, CrewAI, OpenAI Agents SDK, custom loops, etc. The practices are framework-agnostic.

## Instructions

1. **Explore the current repo first** — do not ask the user for anything yet. Look for agent-related code by searching for common patterns:
   - Files matching `*agent*`, `*tool*`, `*prompt*`, `*chain*`, `*workflow*` in `src/`, `lib/`, `app/`, root
   - Imports of agent frameworks: `langchain`, `langgraph`, `openai`, `anthropic`, `autogen`, `crewai`, `pydantic`
   - System prompt definitions, tool definitions, agent loop logic
   - `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, or any README describing the agent architecture

   Read the most relevant files to understand the agent design. Only ask the user if you genuinely cannot find any agent-related code after exploring.

2. **Read all 9 best-practice docs** from `best-practices/` in this repo.

3. **Produce a structured gap analysis** using the format below. This is the output — do not edit any project files, do not write fixes, do not run shell commands beyond what's needed to explore the repo.

---

### Agent Review: [agent name or "Unnamed Agent"]

**Summary** (2–3 sentences on the overall design)

---

#### Dimension-by-dimension audit

For each of the 9 dimensions below, score the design:
- ✅ Solid — clearly covered
- ⚠️ Partial — present but missing something important
- ❌ Gap — not addressed or actively violating the practice

| # | Dimension | Score | Finding |
|---|-----------|-------|---------|
| 01 | Multi-agent orchestration | | |
| 02 | Worker prompting | | |
| 03 | Context & memory | | |
| 04 | Tool design | | |
| 05 | Verification & testing | | |
| 06 | Security & permissions | | |
| 07 | Prompt engineering | | |
| 08 | Performance & startup | | |

---

#### Top 3 highest-priority improvements

For each, include:
- **What**: the specific change
- **Why**: the benchmark or principle it addresses (cite the number)
- **How**: a concrete implementation suggestion (description only — do not apply it)

---

#### What's already strong

Call out 2–3 things the design does well, with reference to the best-practice docs.

---

4. Keep benchmark citations tight — e.g. "centralized orchestration reduces error amplification from 17.2× to 4.4× (Google DeepMind, Dec 2025)".

5. If the design is for a non-Claude model (GPT, Gemini, Llama, etc.), note which practices are model-specific vs. universally applicable.

6. **End with a handoff line**, e.g.: *"Run `/improve-agent` to act on these findings, or `/improve-agent <dimension>` to focus on one area."* Do not start implementing without the user's go-ahead.
