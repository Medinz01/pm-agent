"""
Reads git history and surfaces recent commits as context
for the analyzer and watcher.
"""

import os
from datetime import datetime


def is_git_repo(path: str) -> bool:
    return os.path.exists(os.path.join(path, ".git"))


def get_recent_commits(path: str, limit: int = 10) -> list[dict]:
    """
    Returns last N commits as list of dicts:
    { hash, author, date, message }
    """
    if not is_git_repo(path):
        return []

    try:
        import git
        repo = git.Repo(path)
        commits = []
        for commit in list(repo.iter_commits("HEAD", max_count=limit)):
            commits.append({
                "hash": commit.hexsha[:7],
                "author": str(commit.author),
                "date": datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d"),
                "message": commit.message.strip().splitlines()[0],  # first line only
            })
        return commits
    except Exception:
        return []


def get_commit_diff(path: str, commit_hash: str) -> str:
    """Return the diff for a specific commit."""
    if not is_git_repo(path):
        return ""
    try:
        import git
        repo = git.Repo(path)
        commit = repo.commit(commit_hash)
        if commit.parents:
            diff = commit.parents[0].diff(commit, create_patch=True)
            return "\n".join(d.diff.decode("utf-8", errors="ignore")[:500] for d in diff)
        return ""
    except Exception:
        return ""


def format_commits_for_doc(commits: list[dict]) -> str:
    """Format commits as markdown for PROJECT.md git history section."""
    if not commits:
        return "_No git history found._\n"
    lines = []
    for c in commits:
        lines.append(f"- `{c['hash']}` {c['date']} — {c['message']} _{c['author']}_")
    return "\n".join(lines) + "\n"


def format_commits_for_prompt(commits: list[dict]) -> str:
    """Format commits as context for LLM prompts."""
    if not commits:
        return "No git history available."
    lines = ["Recent commits:"]
    for c in commits:
        lines.append(f"  {c['hash']} ({c['date']}): {c['message']}")
    return "\n".join(lines)