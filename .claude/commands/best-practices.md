# /best-practices

Load and present a specific best-practice reference document by topic keyword.

**Framework-agnostic** — all documents cover patterns applicable to any LLM agent system.

## Usage

```
/best-practices orchestration    → 01-multi-agent-orchestration.md
/best-practices worker           → 02-worker-prompting.md
/best-practices prompting        → 02-worker-prompting.md + 07-prompt-engineering.md
/best-practices memory           → 03-context-and-memory.md
/best-practices context          → 03-context-and-memory.md
/best-practices tools            → 04-tool-design.md
/best-practices verification     → 05-verification-and-testing.md
/best-practices testing          → 05-verification-and-testing.md
/best-practices security         → 06-security-and-permissions.md
/best-practices permissions      → 06-security-and-permissions.md
/best-practices performance      → 08-performance-and-startup.md
/best-practices startup          → 08-performance-and-startup.md
/best-practices benchmarks       → 09-benchmarks-reference.md
/best-practices all              → full README summary + all benchmark numbers
```

## Instructions

1. Match the user's keyword to the file(s) above.

2. Read the matched file(s) from `best-practices/` in this repo.

3. Present the content with this structure:
   - **Key benchmarks** — pull the "Benchmarks at a Glance" table from the doc
   - **Core principles** — 3–5 bullet summary of the must-know rules
   - **Full document** — the complete doc content
   - **How to apply** — 2–3 questions the user should ask themselves about their own agent

4. If the user asks to apply this to their agent, switch to `/review-agent` or `/improve-agent` mode.

5. If no keyword is provided, show the full index from `best-practices/README.md` and ask which topic they want.
