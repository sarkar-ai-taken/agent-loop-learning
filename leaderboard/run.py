#!/usr/bin/env python3
"""
run.py — agent-loop-learning leaderboard runner
================================================
Discovers top open-source AI agent repos, reviews them with a local or
cloud model, and publishes results to the leaderboard + GitHub Pages site.

Usage:
    python leaderboard/run.py                         # full weekly run
    python leaderboard/run.py --discover-only         # list discovered repos, no reviews
    python leaderboard/run.py --repo owner/repo-name  # review one specific repo
    python leaderboard/run.py --dry-run               # run without committing to git
    python leaderboard/run.py --no-push               # run and commit but don't push

Run from the repo root:
    cd agent-loop-learning
    python leaderboard/run.py

Prerequisites:
    pip install -r leaderboard/requirements.txt
    ollama serve                    # if using Ollama (default)
    ollama pull gemma4:27b          # first time only
"""

from __future__ import annotations

import argparse
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Ensure leaderboard/ is on the path when run from repo root
sys.path.insert(0, str(Path(__file__).parent))

from discover import discover_agents
from publish import (
    git_commit_and_push,
    load_existing_reviews,
    save_review_sidecar,
    update_agent_data_json,
    update_leaderboard_readme,
    write_review_file,
)
from review import review_repo

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


def _print(msg: str, style: str = "") -> None:
    if HAS_RICH and console:
        console.print(msg, style=style)
    else:
        print(msg)


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        print(f"ERROR: config not found at {config_path}")
        print("Run from the repo root: python leaderboard/run.py")
        sys.exit(1)
    return yaml.safe_load(config_path.read_text())


def make_repo_info_from_slug(slug: str) -> dict:
    """Build a minimal repo_info dict from an owner/repo string."""
    parts = slug.strip().split("/")
    if len(parts) != 2:
        print(f"ERROR: --repo must be in format owner/repo-name, got: {slug}")
        sys.exit(1)
    owner, repo = parts
    return {
        "owner": owner,
        "repo": repo,
        "full_name": slug,
        "stars": 0,
        "description": "",
        "url": f"https://github.com/{slug}",
        "clone_url": f"https://github.com/{slug}.git",
        "topics": [],
        "language": "Unknown",
        "last_commit": "",
        "open_issues": 0,
        "license": "Unknown",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="agent-loop-learning leaderboard runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--discover-only", action="store_true", help="List discovered repos without reviewing")
    parser.add_argument("--repo", metavar="owner/repo", help="Review a single specific repo")
    parser.add_argument("--dry-run", action="store_true", help="Run without committing to git")
    parser.add_argument("--no-push", action="store_true", help="Commit but don't push to remote")
    parser.add_argument("--config", default="leaderboard/config.yaml", help="Path to config.yaml")
    args = parser.parse_args()

    repo_root = Path(".").resolve()
    config_path = repo_root / args.config
    config = load_config(config_path)

    # Resolve directories
    reviews_dir = repo_root / config["leaderboard"]["reviews_dir"]
    docs_dir = repo_root / config["leaderboard"]["docs_dir"]
    reviews_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    top_n: int = config["leaderboard"]["top_n"]

    _print("\n[bold cyan]agent-loop-learning leaderboard[/bold cyan]" if HAS_RICH else "\nagent-loop-learning leaderboard")
    _print(f"  Config:  {config_path}")
    _print(f"  Model:   {config['model']['evaluated_by']}")
    _print(f"  Top N:   {top_n}")
    _print(f"  Dry run: {args.dry_run}\n")

    # ── Discover ──────────────────────────────────────────────────────────────
    if args.repo:
        candidates = [make_repo_info_from_slug(args.repo)]
        _print(f"  Single-repo mode: {args.repo}")
    else:
        _print("  Discovering agent repos on GitHub ...")
        candidates = discover_agents(config)

        if args.discover_only:
            _print(f"\n  Found {len(candidates)} candidates:\n")
            for r in candidates:
                _print(f"    {r['stars']:>6}★  {r['full_name']:<45}  {r['description'][:60]}")
            return

        candidates = candidates[:top_n]

    # ── Review ────────────────────────────────────────────────────────────────
    new_reviews: list[dict] = []
    failed: list[str] = []

    for i, repo_info in enumerate(candidates, 1):
        _print(f"\n[{i}/{len(candidates)}] {repo_info['full_name']}")
        try:
            review = review_repo(repo_info, config, repo_root)
            new_reviews.append(review)

            # Write individual review file + JSON sidecar
            review_file = write_review_file(review, reviews_dir)
            save_review_sidecar(review, reviews_dir)
            _print(f"  ✓ Review written: {review_file.name}")
            _print(f"    Score: {review['score_display']}")

        except Exception as e:
            _print(f"  ✗ Failed: {e}", style="red" if HAS_RICH else "")
            traceback.print_exc()
            failed.append(repo_info["full_name"])

    if not new_reviews and not args.discover_only:
        _print("\n  No new reviews completed. Check errors above.")
        if failed:
            _print(f"  Failed repos: {', '.join(failed)}")
        return

    # ── Publish ───────────────────────────────────────────────────────────────
    _print("\n  Publishing leaderboard ...")

    # Merge new reviews with existing ones for the full leaderboard
    existing = load_existing_reviews(reviews_dir)
    existing_names = {r["full_name"] for r in new_reviews}
    all_reviews = new_reviews + [r for r in existing if r["full_name"] not in existing_names]
    all_reviews = sorted(all_reviews, key=lambda r: r.get("solid_count", 0), reverse=True)[:top_n * 2]

    readme_path = repo_root / "leaderboard" / "README.md"
    update_leaderboard_readme(all_reviews, readme_path)
    update_agent_data_json(all_reviews, docs_dir)

    if not args.dry_run:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        commit_msg = config["leaderboard"]["commit_message"].format(date=date_str)
        auto_push = config["leaderboard"].get("auto_push", True) and not args.no_push
        try:
            git_commit_and_push(repo_root, commit_msg) if auto_push else \
                _commit_only(repo_root, commit_msg)
        except Exception as e:
            _print(f"  Git error (results saved locally): {e}", style="yellow" if HAS_RICH else "")
    else:
        _print("  Dry run — skipping git commit.")

    # ── Summary ───────────────────────────────────────────────────────────────
    _print(f"\n  Done. {len(new_reviews)} reviews completed, {len(failed)} failed.")
    if failed:
        _print(f"  Failed: {', '.join(failed)}")
    _print(f"  Leaderboard: {readme_path}")
    _print(f"  GitHub Pages data: {docs_dir / 'agent-data.json'}")


def _commit_only(repo_root: Path, message: str) -> None:
    import subprocess
    subprocess.run(["git", "add", "leaderboard/", "docs/"], cwd=repo_root, check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo_root)
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", message], cwd=repo_root, check=True)
        print(f"  Committed: {message} (not pushed — use git push to publish)")


if __name__ == "__main__":
    main()
