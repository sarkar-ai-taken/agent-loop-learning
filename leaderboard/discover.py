"""
discover.py
===========
Discovers top open-source AI agent repos on GitHub using the Search API.
Filters by topic, stars, language, and skips recently-reviewed repos.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def _headers() -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def _recently_reviewed(owner: str, repo: str, reviews_dir: Path, within_days: int) -> bool:
    """Return True if this repo has a review file modified within the last N days."""
    slug = f"{owner}-{repo}".replace("/", "-")
    review_file = reviews_dir / f"{slug}.md"
    if not review_file.exists():
        return False
    mtime = datetime.fromtimestamp(review_file.stat().st_mtime, tz=timezone.utc)
    return mtime > datetime.now(timezone.utc) - timedelta(days=within_days)


def search_github(
    topic: str,
    min_stars: int,
    languages: list[str],
    per_page: int = 10,
) -> list[dict[str, Any]]:
    """Search GitHub for repos with a given topic, filtered by stars and language."""
    lang_q = " ".join(f"language:{l}" for l in languages)
    query = f"topic:{topic} stars:>={min_stars} {lang_q} archived:false fork:false"

    try:
        with httpx.Client(headers=_headers(), timeout=15.0) as client:
            resp = client.get(
                f"{GITHUB_API}/search/repositories",
                params={"q": query, "sort": "stars", "order": "desc", "per_page": per_page},
            )
            if resp.status_code == 403:
                print(f"  GitHub rate limit hit for topic:{topic}. Set GITHUB_TOKEN env var for higher limits.")
                return []
            resp.raise_for_status()
            return resp.json().get("items", [])
    except httpx.HTTPError as e:
        print(f"  GitHub API error for topic:{topic}: {e}")
        return []


def discover_agents(config: dict) -> list[dict[str, Any]]:
    """
    Discover top open-source AI agent repos.

    Returns a deduplicated list of repo dicts, sorted by stars,
    excluding recently-reviewed and excluded repos.
    """
    disc = config["discovery"]
    topics: list[str] = disc["topics"]
    min_stars: int = disc["min_stars"]
    languages: list[str] = disc.get("languages", ["Python", "TypeScript", "JavaScript"])
    max_candidates: int = disc.get("max_candidates", 20)
    exclude: list[str] = disc.get("exclude_repos", [])
    skip_days: int = disc.get("skip_if_reviewed_within_days", 7)

    repo_root = Path(config["leaderboard"]["repo_root"]).resolve()
    reviews_dir = repo_root / config["leaderboard"]["reviews_dir"]

    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []

    for topic in topics:
        print(f"  Searching topic: {topic} ...")
        items = search_github(topic, min_stars, languages, per_page=10)
        time.sleep(1.0)  # be polite to GitHub API

        for item in items:
            full_name: str = item["full_name"]
            owner, repo = full_name.split("/", 1)

            if full_name in seen:
                continue
            if full_name in exclude:
                print(f"    Skipping excluded: {full_name}")
                continue
            if _recently_reviewed(owner, repo, reviews_dir, skip_days):
                print(f"    Skipping recently reviewed: {full_name}")
                continue

            seen.add(full_name)
            candidates.append({
                "owner": owner,
                "repo": repo,
                "full_name": full_name,
                "stars": item.get("stargazers_count", 0),
                "description": item.get("description") or "",
                "url": item.get("html_url", ""),
                "clone_url": item.get("clone_url", ""),
                "topics": item.get("topics", []),
                "language": item.get("language") or "Unknown",
                "last_commit": item.get("pushed_at") or "",
                "open_issues": item.get("open_issues_count", 0),
                "license": (item.get("license") or {}).get("spdx_id") or "Unknown",
            })

    # Sort by stars, return top candidates
    candidates.sort(key=lambda r: r["stars"], reverse=True)
    result = candidates[:max_candidates]
    print(f"\n  Found {len(result)} candidates after filtering.\n")
    return result


if __name__ == "__main__":
    import yaml
    cfg = yaml.safe_load(Path("leaderboard/config.yaml").read_text())
    repos = discover_agents(cfg)
    for r in repos:
        print(f"  {r['stars']:>6}★  {r['full_name']:<45}  {r['description'][:60]}")
