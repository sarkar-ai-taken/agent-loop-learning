"""
review.py
=========
Model-agnostic review runner for agent-loop-learning leaderboard.

Loads best-practice docs, clones the target repo, builds the review prompt,
calls the configured model (Ollama / Anthropic / OpenAI), and parses the
structured ✅/⚠️/❌ scorecard output.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Dimension labels ─────────────────────────────────────────────────────────

DIMENSIONS = [
    (1, "Multi-agent orchestration"),
    (2, "Worker prompting"),
    (3, "Context & memory"),
    (4, "Tool design"),
    (5, "Verification & testing"),
    (6, "Security & permissions"),
    (7, "Prompt engineering"),
    (8, "Performance & startup"),
]

AGENT_FILE_PATTERNS = [
    "*agent*", "*tool*", "*prompt*", "*chain*", "*workflow*",
    "*orchestrat*", "*coordinator*", "*runner*", "*executor*",
]

AGENT_IMPORT_PATTERNS = [
    "langchain", "langgraph", "openai", "anthropic", "autogen",
    "crewai", "pydantic_ai", "llamaindex", "llama_index",
]

MAX_FILE_BYTES = 8_000   # per file
MAX_FILES = 15


# ── Best-practice doc loading ─────────────────────────────────────────────────

def load_best_practices(repo_root: Path) -> str:
    """Load all 9 best-practice docs into a single string."""
    bp_dir = repo_root / "best-practices"
    if not bp_dir.exists():
        raise FileNotFoundError(f"best-practices/ not found at {bp_dir}")
    docs = []
    for f in sorted(bp_dir.glob("*.md")):
        docs.append(f"### {f.name}\n\n{f.read_text(encoding='utf-8', errors='ignore')}")
    return "\n\n---\n\n".join(docs)


# ── Agent code extraction ─────────────────────────────────────────────────────

def find_agent_files(repo_path: Path, max_tokens: int) -> list[tuple[str, str]]:
    """
    Find agent-related source files in the cloned repo.
    Returns list of (relative_path, content) tuples, capped at max_tokens.
    """
    candidates: list[Path] = []

    # Pattern-based search
    for pattern in AGENT_FILE_PATTERNS:
        for ext in ["*.py", "*.ts", "*.js", "*.tsx"]:
            candidates.extend(repo_path.rglob(f"{pattern}{ext[1:]}"))
            candidates.extend(repo_path.rglob(f"{ext[:-1]}{pattern[1:]}"))

    # Also grab any file that imports agent frameworks
    for src_file in repo_path.rglob("*.py"):
        if src_file in candidates:
            continue
        try:
            text = src_file.read_text(encoding="utf-8", errors="ignore")
            if any(imp in text for imp in AGENT_IMPORT_PATTERNS):
                candidates.append(src_file)
        except OSError:
            pass

    # Deduplicate, skip huge files and node_modules/venv
    seen: set[Path] = set()
    filtered: list[Path] = []
    for p in candidates:
        p = p.resolve()
        if p in seen:
            continue
        if any(part in p.parts for part in ("node_modules", ".venv", "venv", "__pycache__", ".git")):
            continue
        seen.add(p)
        filtered.append(p)

    # Sort by relevance: prefer files with "agent" in name
    filtered.sort(key=lambda p: (0 if "agent" in p.stem.lower() else 1, p.stat().st_size))

    # Cap by token budget (rough: 1 token ≈ 4 chars)
    token_budget = max_tokens
    result: list[tuple[str, str]] = []
    for p in filtered[:MAX_FILES]:
        try:
            content = p.read_bytes()[:MAX_FILE_BYTES].decode("utf-8", errors="ignore")
        except OSError:
            continue
        tokens_used = len(content) // 4
        if tokens_used > token_budget:
            break
        token_budget -= tokens_used
        rel = str(p.relative_to(repo_path))
        result.append((rel, content))

    return result


# ── Prompt building ───────────────────────────────────────────────────────────

REVIEW_SYSTEM_PROMPT = """You are an expert AI agent systems auditor. Your job is to review open-source AI agent repositories against a set of best-practice dimensions and produce a structured scorecard.

You will be given:
1. Nine best-practice reference documents covering agent design dimensions
2. Source code from the repository being reviewed

CRITICAL RULES:
- Score each dimension ONLY based on what you can see in the provided code
- Cite benchmark numbers EXACTLY as they appear in the provided best-practice docs (do not invent numbers)
- Follow the output format precisely — it will be parsed programmatically
- Each score must be exactly one of: ✅ (solid), ⚠️ (partial), or ❌ (gap)
- Include the "Evaluated by:" line at the end"""

def build_review_prompt(
    repo_info: dict,
    agent_files: list[tuple[str, str]],
    best_practices: str,
    evaluated_by: str,
) -> str:
    files_block = "\n\n".join(
        f"**File: {path}**\n```\n{content}\n```" for path, content in agent_files
    )
    return f"""# Agent Review Task

## Repository
- **Name**: {repo_info['full_name']}
- **Stars**: {repo_info['stars']:,}
- **Description**: {repo_info['description']}
- **Primary language**: {repo_info['language']}
- **URL**: {repo_info['url']}

---

## Best-Practice Reference Docs

{best_practices}

---

## Repository Source Files

{files_block if agent_files else "_No agent source files found — review based on repo metadata and README only._"}

---

## Instructions

Perform a structured audit using this EXACT format:

### Agent Review: {repo_info['repo']}

**Summary** (2–3 sentences on the overall design)

---

#### Dimension-by-dimension audit

| # | Dimension | Score | Finding |
|---|-----------|-------|---------|
| 01 | Multi-agent orchestration | [✅/⚠️/❌] | [finding] |
| 02 | Worker prompting | [✅/⚠️/❌] | [finding] |
| 03 | Context & memory | [✅/⚠️/❌] | [finding] |
| 04 | Tool design | [✅/⚠️/❌] | [finding] |
| 05 | Verification & testing | [✅/⚠️/❌] | [finding] |
| 06 | Security & permissions | [✅/⚠️/❌] | [finding] |
| 07 | Prompt engineering | [✅/⚠️/❌] | [finding] |
| 08 | Performance & startup | [✅/⚠️/❌] | [finding] |

---

#### Top 3 highest-priority improvements

For each:
- **What**: the specific change
- **Why**: cite the benchmark number from the provided docs
- **How**: concrete implementation suggestion

---

#### What's already strong

2–3 things the design does well, referencing the best-practice docs.

---

Evaluated by: {evaluated_by}"""


# ── Model callers ─────────────────────────────────────────────────────────────

def run_review_ollama(system_prompt: str, user_prompt: str, config: dict) -> str:
    """Call local Ollama with the review prompt."""
    try:
        import ollama
    except ImportError:
        raise ImportError("Run: pip install ollama")

    model_name = config["model"]["name"]
    print(f"  Calling Ollama model: {model_name} ...")

    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": config["model"].get("temperature", 0.2)},
        )
        return response["message"]["content"]
    except Exception as e:
        if "model not found" in str(e).lower():
            raise RuntimeError(
                f"Model '{model_name}' not found in Ollama.\n"
                f"Run: ollama pull {model_name}"
            )
        if "connection refused" in str(e).lower():
            raise RuntimeError(
                "Ollama is not running.\n"
                "Start it with: ollama serve"
            )
        raise


def run_review_anthropic(system_prompt: str, user_prompt: str, config: dict) -> str:
    """Call Anthropic API with the review prompt."""
    try:
        import anthropic
    except ImportError:
        raise ImportError("Run: pip install anthropic")

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)
    model_name = config["model"]["name"]
    print(f"  Calling Anthropic model: {model_name} ...")

    message = client.messages.create(
        model=model_name,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


def run_review_openai(system_prompt: str, user_prompt: str, config: dict) -> str:
    """Call OpenAI API with the review prompt."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Run: pip install openai")

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = OpenAI(api_key=api_key)
    model_name = config["model"]["name"]
    print(f"  Calling OpenAI model: {model_name} ...")

    resp = client.chat.completions.create(
        model=model_name,
        temperature=config["model"].get("temperature", 0.2),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content


# ── Output parser ─────────────────────────────────────────────────────────────

SCORE_MAP = {"✅": "solid", "⚠️": "partial", "❌": "gap"}
SCORE_EMOJI = {"solid": "✅", "partial": "⚠️", "gap": "❌"}


def parse_review_output(raw: str, repo_info: dict, evaluated_by: str) -> dict[str, Any]:
    """
    Parse the structured review output into a machine-readable dict.
    Robust to minor model output variation.
    """
    scores: dict[str, str] = {}

    # Parse scorecard table rows
    for dim_num, dim_name in DIMENSIONS:
        pattern = rf"\|\s*0?{dim_num}\s*\|[^|]*\|\s*([✅⚠️❌]+)\s*\|"
        match = re.search(pattern, raw)
        if match:
            emoji = match.group(1).strip()
            scores[dim_name] = SCORE_MAP.get(emoji, "partial")
        else:
            scores[dim_name] = "partial"  # default if not found

    solid = sum(1 for v in scores.values() if v == "solid")
    partial = sum(1 for v in scores.values() if v == "partial")
    gap = sum(1 for v in scores.values() if v == "gap")

    # Extract summary (first paragraph after "**Summary**")
    summary_match = re.search(r"\*\*Summary\*\*\s*\(.*?\)\s*\n+(.*?)(?:\n\n|\n---)", raw, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""

    # Extract top improvements titles
    improvements = re.findall(r"###\s*\d+\.\s+(.+)", raw)
    if not improvements:
        improvements = re.findall(r"\*\*([A-Z][^*]{5,60})\*\*\s*\n-\s*\*\*What\*\*", raw)

    # Extract strengths
    strengths_match = re.search(r"What's already strong.*?\n+(.*?)(?:\n---|\Z)", raw, re.DOTALL)
    strengths_text = strengths_match.group(1).strip() if strengths_match else ""
    strengths = [s.strip("* ").strip() for s in re.findall(r"\*\*(.+?)\*\*", strengths_text)][:3]

    return {
        "owner": repo_info["owner"],
        "repo": repo_info["repo"],
        "full_name": repo_info["full_name"],
        "stars": repo_info["stars"],
        "description": repo_info["description"],
        "url": repo_info["url"],
        "language": repo_info["language"],
        "scores": scores,
        "solid_count": solid,
        "partial_count": partial,
        "gap_count": gap,
        "score_display": f"{solid}✅ {partial}⚠️ {gap}❌",
        "top_improvements": improvements[:3],
        "strengths": strengths,
        "summary": summary,
        "evaluated_by": evaluated_by,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "raw_review": raw,
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def review_repo(repo_info: dict, config: dict, repo_root: Path) -> dict[str, Any]:
    """
    Full review pipeline for a single repo:
    clone → find agent files → build prompt → call model → parse output.
    """
    print(f"\n  Reviewing: {repo_info['full_name']} ({repo_info['stars']:,}★)")

    best_practices = load_best_practices(repo_root)
    evaluated_by = config["model"]["evaluated_by"]
    max_code_tokens = config["model"].get("max_code_tokens", 30000)

    with tempfile.TemporaryDirectory() as tmp:
        clone_path = Path(tmp) / repo_info["repo"]
        print(f"  Cloning {repo_info['clone_url']} ...")
        result = subprocess.run(
            ["git", "clone", "--depth=1", "--quiet", repo_info["clone_url"], str(clone_path)],
            capture_output=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Clone failed: {result.stderr.decode()}")

        agent_files = find_agent_files(clone_path, max_code_tokens)
        print(f"  Found {len(agent_files)} agent-related source files")

        user_prompt = build_review_prompt(repo_info, agent_files, best_practices, evaluated_by)

        provider = config["model"]["provider"]
        if provider == "ollama":
            raw = run_review_ollama(REVIEW_SYSTEM_PROMPT, user_prompt, config)
        elif provider == "anthropic":
            raw = run_review_anthropic(REVIEW_SYSTEM_PROMPT, user_prompt, config)
        elif provider == "openai":
            raw = run_review_openai(REVIEW_SYSTEM_PROMPT, user_prompt, config)
        else:
            raise ValueError(f"Unknown provider: {provider}. Use: ollama, anthropic, openai")

    return parse_review_output(raw, repo_info, evaluated_by)
