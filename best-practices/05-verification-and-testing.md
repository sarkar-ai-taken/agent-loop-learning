---
name: verification-and-testing
description: Best practices for agent self-verification, independent checking, and proving changes work — not just confirming they exist.
type: reference
---

# Verification and Testing Best Practices

## Benchmarks at a Glance

| Metric | Finding | Source |
|--------|---------|--------|
| Top SWE-bench Verified score | **81.42%** (Claude Opus 4.6, April 2026) | swebench.com |
| Scaffold gain (same model) | **+8 pp** (62.3% → 70.3%, Claude 3.7 Sonnet) | SWE-bench, Feb 2025 |
| Self-Refine improvement over direct generation | **+5% to +40%** across 7 diverse tasks | Madaan et al. — Self-Refine paper |
| Reflexion: GPT-4 coding improvement | **80% → 91%** (+11 pp) | Reflexion framework paper |
| Unguided self-reflection at the frontier | **+1.8 pp or less** over 5 iterations | 2025 refinement study (1,000 problems, 11 domains) |
| Guided external feedback within 5 turns | **+80% gains** | 2025 refinement study |
| Error amplification without cross-checking | **17.2×** in independent multi-agent systems | Google DeepMind, Dec 2025 |
| Error amplification with centralized orchestration | **4.4×** | Google DeepMind, Dec 2025 |
| Enterprise agent failure rate (first year) | **73%** experience reliability failures | Cleanlab: AI Agents in Production, 2025 |
| Teams with "elite" evaluation coverage | Only **15%** test >90% of behaviors | Cleanlab, 2025 |
| Well-implemented agents with structured verification | **85–95% autonomous completion** for structured tasks | Industry benchmarks, 2025 |
| 20-step agent at 95% per-step reliability | Only **36% end-to-end success** | Compounding math |

**Key insight:** Unguided self-reflection adds very little at the frontier (+1.8 pp). External structured verification with distinct detection mechanisms produces meaningful gains (+80%). Scaffolding alone accounts for +8 percentage points on SWE-bench, more than many model upgrades.

---

## 1. Verification Is the Highest-Leverage Thing You Can Do

If you do one thing to improve agent output quality, make it this: **give the agent a way to verify its own work.**

Without a verification mechanism — tests, expected output, screenshots, acceptance criteria — the agent produces something that looks right and self-reports success. You become the only feedback loop, which defeats the purpose of automation.

With clear verification criteria:
- The agent knows what "done" looks like before it starts
- Failure is detected within the agentic loop, not after delivery to the user
- The agent can iterate on failures without requiring human intervention
- Success reports are grounded in evidence, not in the agent's confidence

**Practical rule:** before spawning any implementation agent, define its verification criteria. If you can't define "how will we know it works?", the task isn't specific enough to delegate.

---

## 2. The Verification Mandate

The hardest-won lesson in autonomous coding agents is that **self-reported success is not success**. An implementation agent that runs its own tests and says "tests pass" is the first layer of QA, not the last. A separate, independent verification step is required for production-grade agentic systems.

Snorkel AI's enterprise study (2025) found that independent multi-agent systems without a cross-checking mechanism amplified errors by 17.2×. Adding a centralized orchestrator that reviews results reduced amplification to 4.4× — a 4× improvement from a single architectural change.

---

## 3. Two-Layer Verification Model

### Layer 1: Implementation worker self-test
The worker that makes the change runs:
- Relevant unit and integration tests
- Type check
- Linter (if configured)

This catches obvious breakage. It is **not** the final word.

### Layer 2: Independent verification worker
A fresh agent with no knowledge of how the change was made:
- Runs the full test suite with the feature explicitly enabled
- Tests edge cases and error paths
- Tries to falsify the change
- Treats agent-generated code like a junior developer's first PR

**Why fresh?** An implementation worker carries assumptions. It may skip a test because "that's unrelated to my change." An independent verifier has no such bias.

---

## 4. What Verification Actually Includes

### Required for any code change
- [ ] Run tests **with the relevant feature enabled** (not just the default suite)
- [ ] Run type checks — investigate errors, don't skip as "unrelated"
- [ ] Run linter where configured
- [ ] Manually test the happy path end-to-end

### Required for bug fixes
- [ ] Reproduce the bug with a test before fixing
- [ ] Confirm the test fails before the fix, passes after
- [ ] Verify the fix doesn't regress adjacent behavior

### Required for new features
- [ ] Test with all documented inputs
- [ ] Test edge cases (empty input, maximum values, concurrent access)
- [ ] Test error paths (what happens when upstream fails)
- [ ] Test with feature flag off (if applicable)

### Red flags that require more investigation
- "Tests pass" without specifying which tests
- "No type errors" after a type-related change
- "Verified" with no evidence (no test names, no output)
- Dismissing failures as "probably unrelated"

---

## 5. Self-Correction Protocol

When a worker reports failure (tests failed, build errors, file not found):

1. **Continue the same worker** — it has full error context. Don't spawn fresh for corrections.
2. Include specific error messages in the continuation prompt.
3. If a first correction fails, try a different approach.
4. If two correction attempts fail, escalate with full error context.
5. Re-synthesize and either try a different implementation strategy or escalate to the user.

**Never retry the identical prompt.** A worker that failed will fail again given the same instructions. Diagnose before retrying.

---

## 6. The Verification Worker Prompt

A good verification prompt:

```
Verify that the session expiry fix works correctly.

The change: a null check was added before user.id access in the session
validation logic. When session.user is null (expired session), it now
returns 401 with 'Session expired' instead of throwing.

Prove it by:
1. Running the auth test suite
2. Specifically confirming the session expiry test cases pass
3. Testing this edge case: session where token is valid but user is null
4. Testing the error path: what happens on concurrent expiry

Do NOT just re-run what the implementation worker ran.
Investigate any failures — do not dismiss as unrelated.
Report specific evidence: test names, not just "tests pass".
```

---

## 7. Treating Agent Output Like a Junior Developer's First PR

The industry standard for AI-generated code (2026): **same scrutiny as a first PR from a new junior developer.**

- Code may be functionally correct in spirit but need verification
- CI catches what visual review misses — always run it
- Don't merge code you haven't understood at some level
- The agent's confidence in its output is not a quality signal

What to check:
- Does it solve the stated problem or just the test case?
- Does it introduce a new vulnerability (SQL injection, path traversal, etc.)?
- Does it leave debug artifacts, commented-out code, or TODO stubs?
- Is it idiomatic for the language/framework in use?

---

## 8. Automated Test Generation

When a bug is fixed without a regression test, the fix is not complete. Best practice:

1. Write the regression test that reproduces the bug *first*
2. Confirm it fails before the fix
3. Apply the fix
4. Confirm the test passes
5. Include the test in the commit

Agent systems that skip test generation tend to see the same bugs reappear as the codebase evolves.

---

## 9. The "Rubber Stamp" Anti-Pattern

A verifier that just re-runs the implementation worker's tests and says "pass" adds no value:

| Rubber stamp behavior | Why it fails |
|----------------------|-------------|
| "I ran the tests and they pass" | Doesn't prove the right tests were run |
| "No type errors found" | Doesn't prove the types are correct, only that they compile |
| "The feature works as described" | Doesn't test what happens when inputs are wrong |
| Dismissing a failing test as "pre-existing" | Might be a genuine regression |

**A good verifier is adversarial.** Its job is to find problems, not to confirm there are none.

---

## 10. Fixture-Based API Testing (VCR Pattern)

Agents that make API calls to external services are notoriously hard to test deterministically. The VCR (Video Cassette Recorder) pattern solves this: record real API interactions once, then replay them in tests.

**How it works:**
1. Hash the request body (normalize dynamic fields first: UUIDs, timestamps, temp paths)
2. Use the hash as the fixture filename
3. On first run: execute the real call, save response to fixture file
4. On subsequent runs: serve from fixture, no API call made

**Key constraints:**
- CI is never allowed to record new fixtures — only replay them
- Developers record locally, commit the fixture files
- This keeps CI deterministic and prevents API keys from reaching CI environments

**Dehydration before hashing:** replace session-specific values with stable placeholders before computing the hash:
```
{userId: "abc-123-def"} → {userId: "<USER_ID>"}
{timestamp: 1743879234} → {timestamp: "<TIMESTAMP>"}
```

Logically identical requests produce the same fixture regardless of session-specific values.

**When fixtures are missing in CI:** fail loudly with instructions: `"Fixture missing: {filename}. Re-run with RECORD=1 locally, then commit the result."` Never silently pass or silently hit live APIs.

---

## 11. Forced Acknowledgment Patterns

Some decisions are too consequential to make automatically or accidentally. A forced acknowledgment pattern makes the decision visible and deliberate.

**Type-name-as-declaration:**
In any code path that sends data to external systems (analytics, telemetry, logging), require the developer to cast using a type whose name is a declaration of what they verified:

```typescript
type UserData_I_VERIFIED_THIS_CONTAINS_NO_PII = never
```

To use this type, the developer must type out `as UserData_I_VERIFIED_THIS_CONTAINS_NO_PII` — a 47-character statement that is hard to type accidentally and impossible to type dishonestly.

**Principle: design for deliberateness in dangerous paths.** If a mistake in a code path could cause a compliance violation, data breach, or irreversible action, make the path require a visible human declaration of intent. Speed bumps don't stop determined actors — but they do catch accidental ones, which are more common.

---

## 12. Confidence Threshold Filtering for Agent Outputs

Raw agent output contains findings at varying confidence levels. Surfacing all of them — including uncertain, speculative, or near-duplicate issues — creates noise that reduces trust in the agent over time.

**Pattern: filter by confidence before surfacing**

```
Only report findings where:
  confidence >= 80%         ← suppress uncertain observations
  AND not similar to an already-reported finding  ← consolidate duplicates
  AND ranked by severity (security issues first)
```

**Why 80%:** below this threshold, findings are more likely to generate false-alarm fatigue than catch real problems. A single accurate high-confidence finding is worth more than ten uncertain ones.

**Consolidation before output:** when two findings describe the same root issue in different locations (e.g., the same missing null check in three functions), merge them into one finding with a list of affected locations. Separate reports of the same pattern multiply the user's work without adding information.

**Severity ordering:** always lead with the highest-severity findings. Security vulnerabilities (hardcoded credentials, injection vectors) should surface before style issues, regardless of confidence. A medium-confidence security finding outranks a high-confidence style finding.

Apply this pattern to: code review agents, security scanners, bug-finding agents, test coverage analyzers — any agent whose job is to find and report problems.

---

## 13. When Not to Spawn a Separate Verifier

Not every change needs a full independent verification pass. Reserve it for:
- Changes to security-sensitive code (auth, permissions, crypto)
- Changes that touch multiple modules
- Fixes for production bugs
- Any change where the implementation worker had to iterate (multiple correction cycles)

For small, isolated changes (fixing a typo, updating a config value) the implementation worker's self-test is sufficient.

---

## Sources

- [SWE-bench Verified Leaderboard — swebench.com](https://www.swebench.com/)
- [Evaluating Multi-Agent Systems in Enterprise Tool Use — Snorkel AI](https://snorkel.ai/blog/multi-agents-in-the-context-of-enterprise-tool-use/)
- [Demystifying Evals for AI Agents — Anthropic Engineering](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Best AI Coding Agents for 2026: Real-World Developer Reviews — Faros AI](https://www.faros.ai/blog/best-ai-coding-agents-2026)
- [Autonomous Coding Agents: Beyond Developer Productivity — C3 AI](https://c3.ai/blog/autonomous-coding-agents-beyond-developer-productivity/)
- [The Complete Guide to Agentic Coding in 2026 — Teamday](https://www.teamday.ai/blog/complete-guide-agentic-coding-2026)
