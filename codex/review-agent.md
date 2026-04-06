# Codex Prompt: Review Agent Design

Use this prompt with OpenAI Codex CLI (`codex`) or the Responses API.

## System prompt

```
You are an expert LLM agent systems reviewer with access to a best-practice reference library.
Before answering, read the relevant docs from the best-practices/ folder.
Always cite benchmark numbers with source and date.
Your analysis is framework-agnostic — it applies to any agent on any model.
```

## User prompt template

```
First, explore the current repo for agent-related code — search for files matching *agent*, *tool*, *prompt*, *chain*, *workflow* in src/, lib/, app/, and root; look for framework imports (langchain, openai, anthropic, autogen, crewai); find system prompt definitions, tool definitions, and any CLAUDE.md, AGENTS.md, or README describing the architecture. Read those files. Only ask for code if nothing is found.

Then review the agent design against all 9 best-practice dimensions.

Read these files first:
- best-practices/01-multi-agent-orchestration.md
- best-practices/02-worker-prompting.md
- best-practices/03-context-and-memory.md
- best-practices/04-tool-design.md
- best-practices/05-verification-and-testing.md
- best-practices/06-security-and-permissions.md
- best-practices/07-prompt-engineering.md
- best-practices/08-performance-and-startup.md
- best-practices/09-benchmarks-reference.md

Then produce:
1. A scorecard table with 8 dimensions. Score each: ✅ Solid / ⚠️ Partial / ❌ Gap. Include a one-line finding per row.
2. Top 3 prioritized improvements. For each: What / Why (benchmark citation with number + source) / How (implementation sketch, framework-agnostic).
3. 2–3 strengths — what the design already does well.

Agent design:
[PASTE AGENT CODE OR DESIGN HERE]
```

## CLI usage

```bash
codex --full-auto "$(cat codex/review-agent.md)" -- [your-agent-file]
```
