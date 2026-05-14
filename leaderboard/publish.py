"""
publish.py
==========
Updates the leaderboard README, writes individual review files,
updates agent-data.json for the GitHub Pages site, and commits everything.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Individual review files ───────────────────────────────────────────────────

def write_review_file(review: dict[str, Any], reviews_dir: Path) -> Path:
    """Write leaderboard/reviews/{owner}-{repo}.md with the full review."""
    slug = f"{review['owner']}-{review['repo']}"
    out_path = reviews_dir / f"{slug}.md"

    scores = review.get("scores", {})
    score_rows = "\n".join(
        f"| {i+1:02d} | {dim} | {'✅' if scores.get(dim) == 'solid' else '⚠️' if scores.get(dim) == 'partial' else '❌'} |"
        for i, (_, dim) in enumerate([
            (1, "Multi-agent orchestration"), (2, "Worker prompting"),
            (3, "Context & memory"), (4, "Tool design"),
            (5, "Verification & testing"), (6, "Security & permissions"),
            (7, "Prompt engineering"), (8, "Performance & startup"),
        ])
    )

    improvements = review.get("top_improvements", [])
    improvements_md = "\n".join(f"- {imp}" for imp in improvements) if improvements else "_See full review below._"
    strengths = review.get("strengths", [])
    strengths_md = "\n".join(f"- {s}" for s in strengths) if strengths else "_See full review below._"

    reviewed_at = review.get("reviewed_at", "")
    if reviewed_at:
        try:
            dt = datetime.fromisoformat(reviewed_at)
            reviewed_at_fmt = dt.strftime("%B %d, %Y")
        except Exception:
            reviewed_at_fmt = reviewed_at[:10]
    else:
        reviewed_at_fmt = "Unknown"

    content = f"""# {review['repo']} — Agent Review

**Repository:** [{review['full_name']}]({review['url']})
**Stars:** {review['stars']:,}
**Language:** {review['language']}
**Reviewed:** {reviewed_at_fmt}
**Evaluated by:** {review['evaluated_by']}

> {review.get('description', '')}

---

## Score Summary

| Score | Count |
|-------|-------|
| ✅ Solid | {review['solid_count']} |
| ⚠️ Partial | {review['partial_count']} |
| ❌ Gap | {review['gap_count']} |

## Dimension Scores

| # | Dimension | Score |
|---|-----------|-------|
{score_rows}

## Top Improvements

{improvements_md}

## Strengths

{strengths_md}

---

## Full Review

{review.get('raw_review', '_No raw review content available._')}

---

*Reviewed by the [agent-loop-learning](https://github.com/sarkar-ai-taken/agent-loop-learning) leaderboard system.*
*Model: {review['evaluated_by']} · [Contribute a review with a different model](../README.md#contributing)*
"""

    out_path.write_text(content, encoding="utf-8")
    return out_path


# ── Leaderboard README ────────────────────────────────────────────────────────

def update_leaderboard_readme(all_reviews: list[dict[str, Any]], readme_path: Path) -> None:
    """Rewrite leaderboard/README.md with the current ranking table."""

    sorted_reviews = sorted(
        all_reviews,
        key=lambda r: (r.get("solid_count", 0), r.get("partial_count", 0), -r.get("gap_count", 0)),
        reverse=True,
    )

    rows = []
    for i, r in enumerate(sorted_reviews, 1):
        slug = f"{r['owner']}-{r['repo']}"
        reviewed_at = r.get("reviewed_at", "")
        date_str = reviewed_at[:10] if reviewed_at else "—"
        top_gap_dim = next(
            (dim for dim, score in r.get("scores", {}).items() if score == "gap"),
            next((dim for dim, score in r.get("scores", {}).items() if score == "partial"), "—"),
        )
        short_gap = top_gap_dim[:30] + "…" if len(top_gap_dim) > 30 else top_gap_dim
        rows.append(
            f"| {i} | [{r['repo']}]({r['url']}) | "
            f"{r.get('stars', 0):,}★ | "
            f"{r.get('solid_count', 0)}✅ {r.get('partial_count', 0)}⚠️ {r.get('gap_count', 0)}❌ | "
            f"{short_gap} | "
            f"{r.get('evaluated_by', '—')[:30]} | "
            f"[{date_str}](./reviews/{slug}.md) |"
        )

    table = "\n".join(rows) if rows else "| — | *No reviews yet — run `python leaderboard/run.py`* | — | — | — | — | — |"

    updated_at = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

    content = f"""# Agent Loop Leaderboard

> Top open-source AI agents reviewed weekly against 9 best-practice dimensions from [agent-loop-learning](../README.md).
> **Last updated:** {updated_at}
> **Scoring model:** See "Evaluated By" column · [Contribute a review with a different model](#contributing-a-review)
> **[View live leaderboard →](https://sarkar-ai-taken.github.io/agent-loop-learning/)**

---

## Current Rankings

| Rank | Agent | Stars | Score | Top Gap | Evaluated By | Reviewed |
|------|-------|-------|-------|---------|--------------|----------|
{table}

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

## Contributing a review

Have API tokens? Run the leaderboard with Claude, GPT-4o, or another model and submit a PR:

```bash
# Clone the repo
git clone https://github.com/sarkar-ai-taken/agent-loop-learning
cd agent-loop-learning

# Install deps
pip install -r leaderboard/requirements.txt

# Edit config to set your model
# leaderboard/config.yaml → model.provider: anthropic, model.name: claude-sonnet-4-6

# Review a specific repo
python leaderboard/run.py --repo owner/repo-name --dry-run

# Submit a PR with the review file from leaderboard/reviews/
```

All reviews are clearly labeled with the model that produced them.

---

[See all reviews](./reviews/) · [Best-practice docs](../best-practices/) · [How to use in your project](../README.md)
"""

    readme_path.write_text(content, encoding="utf-8")
    print(f"  Updated leaderboard README: {readme_path}")


# ── agent-data.json for GitHub Pages ─────────────────────────────────────────

def update_agent_data_json(all_reviews: list[dict[str, Any]], docs_dir: Path) -> None:
    """Write docs/agent-data.json with all review data for the GitHub Pages site."""
    sorted_reviews = sorted(
        all_reviews,
        key=lambda r: (r.get("solid_count", 0), r.get("partial_count", 0), -r.get("gap_count", 0)),
        reverse=True,
    )

    agents = []
    for i, r in enumerate(sorted_reviews, 1):
        slug = f"{r['owner']}-{r['repo']}"
        agents.append({
            "rank": i,
            "owner": r["owner"],
            "repo": r["repo"],
            "full_name": r["full_name"],
            "stars": r.get("stars", 0),
            "description": r.get("description", ""),
            "url": r.get("url", ""),
            "language": r.get("language", ""),
            "scores": r.get("scores", {}),
            "solid_count": r.get("solid_count", 0),
            "partial_count": r.get("partial_count", 0),
            "gap_count": r.get("gap_count", 0),
            "top_improvements": r.get("top_improvements", []),
            "strengths": r.get("strengths", []),
            "summary": r.get("summary", ""),
            "evaluated_by": r.get("evaluated_by", ""),
            "reviewed_at": r.get("reviewed_at", ""),
            "review_url": f"https://github.com/sarkar-ai-taken/agent-loop-learning/blob/main/leaderboard/reviews/{slug}.md",
        })

    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "evaluated_by_default": sorted_reviews[0]["evaluated_by"] if sorted_reviews else "Gemma 4 27B (local, Mac Mini M4)",
        "total_reviewed": len(agents),
        "agents": agents,
    }

    out_path = docs_dir / "agent-data.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Updated agent-data.json: {out_path} ({len(agents)} agents)")


# ── Load existing reviews from disk ──────────────────────────────────────────

def load_existing_reviews(reviews_dir: Path) -> list[dict[str, Any]]:
    """Load all existing review JSON sidecars from the reviews/ directory."""
    reviews = []
    for f in reviews_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            reviews.append(data)
        except Exception:
            pass
    return reviews


def save_review_sidecar(review: dict[str, Any], reviews_dir: Path) -> None:
    """Save a machine-readable JSON sidecar alongside the review markdown."""
    slug = f"{review['owner']}-{review['repo']}"
    sidecar = reviews_dir / f"{slug}.json"
    # Don't save the raw_review in the JSON (too large)
    data = {k: v for k, v in review.items() if k != "raw_review"}
    sidecar.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Git commit & push ─────────────────────────────────────────────────────────

def git_commit_and_push(repo_root: Path, message: str) -> None:
    """Stage leaderboard/ and docs/ changes, commit, and push."""
    try:
        subprocess.run(["git", "add", "leaderboard/", "docs/"], cwd=repo_root, check=True)
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], cwd=repo_root
        )
        if result.returncode == 0:
            print("  No changes to commit.")
            return
        subprocess.run(["git", "commit", "-m", message], cwd=repo_root, check=True)
        subprocess.run(["git", "push"], cwd=repo_root, check=True)
        print(f"  Committed and pushed: {message}")
    except subprocess.CalledProcessError as e:
        print(f"  Git error: {e}")
        raise
