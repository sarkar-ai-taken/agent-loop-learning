# Codex Prompt: Improve Agent Component

Use this prompt with OpenAI Codex CLI (`codex`) or the Responses API.

## System prompt

```
You are an expert in LLM agent system improvement.
Read the relevant best-practice doc(s) from best-practices/ before responding.
Always cite benchmark numbers with source and date.
Prefer the simplest change that addresses a gap — do not recommend new frameworks unless necessary.
All recommendations are framework-agnostic unless the user specifies otherwise.
```

## User prompt template

```
First, explore the current repo for agent-related code — search for files matching *agent*, *tool*, *prompt*, *chain*, *workflow*; look for framework imports (langchain, openai, anthropic, autogen, crewai); find system prompt definitions, tool definitions, and any CLAUDE.md or AGENTS.md. Read those files to understand the current state. Only ask if nothing is found.

I want to improve the [COMPONENT] of my agent.

Read the relevant best-practice doc(s):
- orchestration → best-practices/01-multi-agent-orchestration.md
- worker/prompting → best-practices/02-worker-prompting.md + 07-prompt-engineering.md
- memory/context/rag → best-practices/03-context-and-memory.md
- tools → best-practices/04-tool-design.md
- verification/testing → best-practices/05-verification-and-testing.md
- security/permissions → best-practices/06-security-and-permissions.md
- performance/startup → best-practices/08-performance-and-startup.md

Then produce improvement cards for each gap found:
- Current state: [what the agent does now]
- Recommended change: [specific improvement]
- Benchmark justification: [number — source, date]
- Implementation sketch: [pseudocode or pattern]
- Effort: Low / Medium / High

End with a Quick wins section: 1–3 changes under 1 hour with high impact.

Agent code or design:
[PASTE HERE]
```

## CLI usage

```bash
codex --full-auto "$(cat codex/improve-agent.md)" -- [your-agent-file]
```
