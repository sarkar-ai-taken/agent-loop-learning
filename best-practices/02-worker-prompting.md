---
name: worker-prompting
description: Best practices for writing prompts that worker agents can execute reliably — self-contained context, synthesis, precision, and what "done" looks like.
type: reference
---

# Worker Prompting Best Practices

## Benchmarks at a Glance

| Metric | Finding | Source |
|--------|---------|--------|
| Self-contained prompt quality vs. vague prompts | Precise, synthesized prompts are the primary differentiator between top-performing and average agentic frameworks | LangChain Benchmarking, 2025 |
| Agent scaffolding impact (same model) | 17-issue gap on 731 SWE-bench problems between frameworks using the same model | SWE-bench Verified leaderboard, Feb 2026 |
| Top SWE-bench Verified scores | >80% (as of April 2026) — driven by scaffolding and retry logic, not just model quality | swebench.com leaderboard |
| Vague prompts failure mode | Single largest cause of worker failure in multi-agent systems | Anthropic Engineering, 2025 |

---

## 1. The Cardinal Rule: Workers Are Blind

**Workers cannot see your conversation.** They have no access to:
- The user's original request
- Prior worker results
- Context discussed outside their prompt
- Anything not explicitly included in their prompt

Every worker prompt must be **completely self-contained**. If the worker can't execute from the prompt alone, the prompt is wrong.

---

## 2. Always Synthesize — Never Delegate Understanding

The most common failure mode in multi-agent systems is lazy delegation:

**Bad — delegates understanding to the worker:**
```
"Based on your findings, fix the bug."
"The previous worker found an issue. Can you look at it?"
"Based on our discussion, implement the changes."
```

**Good — orchestrator has already synthesized the findings:**
```
"Fix the null pointer in the session validation logic.
 The session.user field is undefined when sessions expire but
 the token remains cached.
 Add a null check before accessing user.id — if null, return 401
 with message 'Session expired'.
 Run the auth tests, commit, and report the hash."
```

**The coordinator's job is to understand and translate.** The difference between a good and bad multi-agent system is almost entirely in whether the coordinator synthesizes before delegating. Phrases like "based on your findings" delegate understanding to the worker — which cannot see the findings.

### How to synthesize
1. Read the worker's findings in full
2. Identify the root cause or key information
3. Locate specific file paths, line numbers, type signatures
4. Write a prompt that proves you understood — include specifics

---

## 3. Anatomy of a Good Worker Prompt

Every effective worker prompt has these components:

### A. Purpose statement
Tell the worker *why* this task exists, so it can calibrate depth and emphasis:
- "This research will inform a PR description — focus on user-facing changes."
- "I need this to plan an implementation — report file paths, line numbers, and type signatures."
- "This is a quick check before we merge — verify the happy path."

### B. Precise task description
- Specific locations and line numbers when known
- Exact error messages if fixing a bug
- The function/class/module name, not just "the auth module"

### C. Constraints and mode
- "Report findings — do not modify any files." (research)
- "Run relevant tests and typecheck after your change." (implementation)
- "Prove the code works, don't just confirm it exists." (verification)

### D. Definition of done
- "Commit and report the hash."
- "Report specific file paths and line numbers."
- "Show the passing test output."

---

## 4. Prompt Templates by Task Type

### Research prompt
```
Investigate [specific thing] in [specific location].
Focus on: [what matters for the follow-up task].
Report: file paths, line numbers, type signatures, and [specific output needed].
This research will be used to [purpose] — calibrate accordingly.
Do not modify any files.
```

### Implementation prompt
```
Fix [specific problem] at [file/location].
Root cause: [what synthesis determined].
Change: [exactly what to add/modify/remove].
Constraints: [any edge cases, backward compat concerns].
After your change: run [specific tests], run typecheck.
Fix the root cause, not the symptom.
Commit and report the hash.
```

### Verification prompt
```
Verify that [specific change] works correctly.
The change: [what was done, in what files].
Prove it by: running [specific tests with feature enabled].
Also check: [edge cases, error paths].
Investigate any failures — don't dismiss as unrelated.
Do not re-run what the implementation worker already ran — try new angles.
Report specific evidence.
```

### Correction prompt (continuing a worker)
Keep it short — the worker has full context:
```
Two tests are still failing — update the assertions to match
the new error message (you changed it from 'Invalid session' to 'Session expired').
```

---

## 5. Common Anti-Patterns

| Anti-pattern | Why it fails | Fix |
|--------------|-------------|-----|
| "Fix the bug we discussed" | Worker can't see the conversation | Include the full bug description |
| "Based on your findings, implement it" | Delegates synthesis to the worker | Read the findings yourself, write a spec |
| "Something went wrong, can you look?" | No error message, no location, no direction | Include the exact error and location |
| "Create a PR for the recent changes" | Ambiguous: which branch? which changes? draft? | Specify branch, commits, draft vs. ready, reviewers |
| "Make it better" | No measurable outcome | Define what "better" means specifically |
| Embedding a 2000-word document "for context" | Worker context gets polluted | Include only the specific relevant excerpt |

---

## 6. Prompt Length and Precision

**Shorter is better when it's precise.** A 3-sentence prompt with a specific location, line number, and "commit the hash" is far more effective than a 10-paragraph description of the system's history.

**Precision scales down well; vagueness doesn't scale up.** Adding more words to a vague prompt doesn't fix it — it just buries the vagueness.

Rules of thumb:
- Research prompts: 3–8 sentences
- Implementation prompts: 5–12 sentences, include specific locations
- Correction prompts (continuing a worker): 1–3 sentences
- Verification prompts: 5–10 sentences, include what to test

---

## 7. Git Operation Precision

Git prompts are especially prone to ambiguity. Always specify:

**Vague (bad):**
```
"Create a PR for the recent changes"
```

**Precise (good):**
```
"Create a new branch from main called 'fix/session-expiry'.
 Cherry-pick only commit abc123 onto it.
 Push and create a draft PR targeting main.
 Add [reviewer] as a reviewer.
 Title: 'Fix null pointer in session expiry path'
 Report the PR URL."
```

Required specifics for any git operation:
- Branch name and base branch
- Which commits (cherry-pick? all since branch? specific hash?)
- Draft vs. ready
- Target reviewer(s)
- PR title framing

---

## 8. Agent Loop Stop Conditions

**The most common cause of infinite loops:** defining the task as a process rather than an outcome.

**Bad — process-based (agent may loop indefinitely):**
```
"Keep checking the logs until you find the error."
"Monitor the build and fix any issues you see."
"Search until you find a solution."
```

**Good — outcome-based (agent knows when it's done):**
```
"Check the last 100 lines of the log. If you find an error, explain it.
If no error is found, report 'No errors found in the last 100 lines.'"

"Run the build. If it fails, identify the first error and report the
file, line, and error message. If it passes, report 'Build succeeded'."
```

An outcome-based definition gives the agent a clear exit state. Every worker prompt should answer: "How does the agent know when this task is complete?"

**Design principle:** the task is "done" when a specific condition is met or a specific output is produced — never when the agent decides it has tried hard enough.

**Task definition checklist:**
- [ ] Is the success condition explicit (not "try until you find it")?
- [ ] Is the failure condition explicit (not "give up after a while")?
- [ ] Does the agent know what to report in both cases?
- [ ] Is the scope bounded (specific files, specific lines, specific steps)?

---

## 9. When Continuing a Worker

Reference what **the worker did**, not what you discussed elsewhere:

**Bad — references context the worker can't see:**
```
"As I mentioned earlier, the null check isn't working."
```

**Good — references the worker's own output:**
```
"The null check you added still fails for expired tokens —
 the test shows session.user is null when token.expires < Date.now().
 Add the expiry check before the null check."
```

---

## 10. Reasoning Depth and Prompt Framing

Agents calibrate the depth of their reasoning to the framing of the task. Operational prompts trigger operational responses; analysis prompts trigger deeper reasoning.

**Deep reasoning triggers:**
- "Analyze the architecture of..."
- "Debug why this is happening — investigate all possible causes..."
- "Design a solution for..."
- "What are the tradeoffs between..."

**Operational triggers (fast, shallow):**
- "Rename this variable to..."
- "Add this import to..."
- "Run the tests and report the output."
- "Create a branch called..."

**Rule:** match the framing to the task. Don't ask for analysis in an operational-style prompt. Don't ask for a quick change in an architecture-style prompt. The model reads the register of your request.

For complex debugging, investigation, or design tasks: spend a sentence framing why this is hard or ambiguous. This signals that the agent should reason carefully rather than snap to the first answer.

---

## Sources

- [Effective Context Engineering for AI Agents — Anthropic Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [SWE-bench Verified Leaderboard — swebench.com](https://www.swebench.com/)
- [Benchmarking Multi-Agent Architectures — LangChain Blog](https://blog.langchain.com/benchmarking-multi-agent-architectures/)
- [Prompt Engineering for AI Agents 2026 — Inflectra](https://www.inflectra.com/Ideas/Topic/AI-Agent-Prompt-Engineering.aspx)
- [PromptHub — Prompt Engineering for AI Agents](https://www.prompthub.us/blog/prompt-engineering-for-ai-agents)
