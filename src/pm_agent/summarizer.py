"""
Generates a quick project status summary in the terminal
without opening PROJECT.md.
"""

import os
import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich import box

console = Console()


def _extract_section(content: str, header: str) -> str:
    """Extract content between two ## headers."""
    pattern = rf"## {header}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else ""


def _count_decisions(content: str) -> int:
    section = _extract_section(content, "Design Decisions")
    rows = [l for l in section.splitlines() if l.startswith("|") and "---" not in l and "Question" not in l]
    return len(rows)


def _count_changelog_entries(content: str) -> int:
    section = _extract_section(content, "Changelog")
    return len([l for l in section.splitlines() if l.strip().startswith("-")])


def _last_changelog_date(content: str) -> str:
    section = _extract_section(content, "Changelog")
    for line in section.splitlines():
        if line.startswith("###"):
            return line.replace("###", "").strip()
    return "Unknown"


def _count_code_map(content: str) -> tuple[int, int]:
    """Returns (file_count, symbol_count)."""
    section = _extract_section(content, "Code Map")
    files = len([l for l in section.splitlines() if l.startswith("###")])
    symbols = len([l for l in section.splitlines() if l.strip().startswith("-")])
    return files, symbols


def print_summary(doc_path: str, repo_path: str = "."):
    if not os.path.exists(doc_path):
        console.print("[red]PROJECT.md not found. Run pm-agent init first.[/red]")
        return

    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract fields
    purpose = _extract_section(content, "Purpose") or "Not set"
    stack = _extract_section(content, "Stack") or "Not set"
    architecture = _extract_section(content, "Architecture") or "Not set"
    decisions = _count_decisions(content)
    changelog_entries = _count_changelog_entries(content)
    last_change = _last_changelog_date(content)
    files_mapped, symbols_mapped = _count_code_map(content)

    # Git info
    git_info = ""
    try:
        from pm_agent.git_reader import get_recent_commits, is_git_repo
        if is_git_repo(repo_path):
            commits = get_recent_commits(repo_path, limit=3)
            if commits:
                git_info = "\n".join(
                    f"  [dim]{c['hash']}[/dim] {c['message']}" for c in commits
                )
    except Exception:
        pass

    # ── Render ────────────────────────────────────────────────────────────────
    project_name = content.splitlines()[0].replace("#", "").strip()

    console.print()
    console.rule(f"[bold cyan]{project_name}[/bold cyan]")

    # Purpose + Stack
    console.print(f"\n[bold]Purpose[/bold]")
    console.print(f"  {purpose[:120]}")

    console.print(f"\n[bold]Stack[/bold]")
    console.print(f"  {stack}")

    # Stats table
    stats = Table(box=box.SIMPLE, show_header=False, padding=(0, 3))
    stats.add_column(style="dim")
    stats.add_column(style="bold white")
    stats.add_row("Code files mapped", str(files_mapped))
    stats.add_row("Symbols (fn/class)", str(symbols_mapped))
    stats.add_row("Design decisions", str(decisions))
    stats.add_row("Changelog entries", str(changelog_entries))
    stats.add_row("Last change", last_change)

    console.print(f"\n[bold]Stats[/bold]")
    console.print(stats)

    # Recent commits
    if git_info:
        console.print(f"[bold]Recent commits[/bold]")
        console.print(git_info)

    console.print()