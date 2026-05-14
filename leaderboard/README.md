# Agent Loop Leaderboard

> Top open-source AI agents reviewed weekly against 9 best-practice dimensions from [agent-loop-learning](../README.md).
> **[View live leaderboard →](https://sarkar-ai-taken.github.io/agent-loop-learning/)**

---

## Current Rankings

| Rank | Agent | Stars | Score | Top Gap | Evaluated By | Reviewed |
|------|-------|-------|-------|---------|--------------|----------|
| — | *Run `python leaderboard/run.py` to populate* | — | — | — | — | — |

**Score key:** ✅ Solid · ⚠️ Partial · ❌ Gap · across 8 agent design dimensions

---

## How scoring works

Each agent is reviewed against 8 dimensions from the [best-practices docs](../best-practices/):

| # | Dimension | What it measures |
|---|-----------|-----------------|
| 01 | Multi-agent orchestration | Coordinator/worker split, concurrency, error amplification |
| 02 | Worker prompting | Prompt structure, scaffold design, stop conditions |
| 03 | Context & memory | 6-layer context pipeline, semantic/procedural memory |
| 04 | Tool design | Security properties, classification, streaming |
| 05 | Verification & testing | Independent verification workers, VCR fixtures |
| 06 | Security & permissions | Injection defense, circuit breakers, token hygiene |
| 07 | Prompt engineering | Cache boundaries, prompt anchors, stable/dynamic split |
| 08 | Performance & startup | Circuit breakers, diminishing-returns detector |

---

## Running locally

### Prerequisites
```bash
pip install -r leaderboard/requirements.txt

# If using the default local model (Gemma 4):
brew install ollama          # or: https://ollama.com
ollama serve                 # start Ollama
ollama pull gemma4:27b       # first time only (~16GB download)
```

### Run the full weekly leaderboard
```bash
cd agent-loop-learning
python leaderboard/run.py
```

### Review a specific repo
```bash
python leaderboard/run.py --repo owner/repo-name
```

### Dry run (no git commit)
```bash
python leaderboard/run.py --dry-run
```

### Use a cloud model instead
Edit `leaderboard/config.yaml`:
```yaml
model:
  provider: anthropic          # or: openai
  name: claude-sonnet-4-6      # or: gpt-4o
  evaluated_by: "Claude Sonnet 4.6 (Anthropic API)"
```
Then set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` and run normally.

---

## Contributing a review

Have API tokens? Run the leaderboard with a different model and submit a PR:

1. Fork this repo
2. Edit `leaderboard/config.yaml` to set your model
3. Run `python leaderboard/run.py --repo owner/repo --dry-run`
4. Submit a PR adding the review file from `leaderboard/reviews/`

All reviews are clearly labeled with the model that produced them. Multiple
evaluations of the same repo with different models are welcome.

---

[See all reviews](./reviews/) · [Best-practice docs](../best-practices/) · [Back to main README](../README.md)
