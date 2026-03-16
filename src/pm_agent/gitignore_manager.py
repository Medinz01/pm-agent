"""
Manages .gitignore entries for pmagent.
Called by both `pmagent init` (core) and `pmagent promote setup` (marketing).
Never duplicates entries. Never removes user entries.
"""

import os

# ── Entry sets ────────────────────────────────────────────────────────────────

CORE_ENTRIES = [
    ".pm/snapshot.json",
    ".pm/prompts/",
]

PROMOTE_ENTRIES = [
    ".pm/marketing/",
]

SECTION_HEADER = "# pmagent"
SECTION_FOOTER = "# end pmagent"


def _read_gitignore(root: str) -> list[str]:
    path = os.path.join(root, ".gitignore")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def _write_gitignore(root: str, lines: list[str]):
    path = os.path.join(root, ".gitignore")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _already_present(lines: list[str], entry: str) -> bool:
    return any(line.strip() == entry.strip() for line in lines)


def _get_managed_section(lines: list[str]) -> tuple[int, int]:
    """
    Returns (start_idx, end_idx) of the pmagent-managed section.
    Returns (-1, -1) if no section found.
    """
    start = -1
    end = -1
    for i, line in enumerate(lines):
        if line.strip() == SECTION_HEADER:
            start = i
        if line.strip() == SECTION_FOOTER:
            end = i
    return start, end


def add_entries(root: str, entries: list[str], quiet: bool = False) -> list[str]:
    """
    Add entries to the pmagent-managed section of .gitignore.
    Creates .gitignore if it doesn't exist.
    Returns list of newly added entries.
    """
    lines = _read_gitignore(root)
    start, end = _get_managed_section(lines)
    added = []

    if start == -1:
        # No managed section yet — append it
        if lines and lines[-1].strip() != "":
            lines.append("\n")
        lines.append(f"{SECTION_HEADER}\n")
        for entry in entries:
            lines.append(f"{entry}\n")
            added.append(entry)
        lines.append(f"{SECTION_FOOTER}\n")
    else:
        # Managed section exists — insert new entries before footer
        new_lines = []
        for entry in entries:
            if not _already_present(lines[start:end+1], entry):
                new_lines.append(f"{entry}\n")
                added.append(entry)
        if new_lines:
            lines = lines[:end] + new_lines + lines[end:]

    _write_gitignore(root, lines)

    if not quiet and added:
        for e in added:
            print(f"  [.gitignore] + {e}")

    return added


def setup_core(root: str, quiet: bool = False):
    """Called by `pmagent init` — adds core engine gitignore entries."""
    added = add_entries(root, CORE_ENTRIES, quiet=quiet)
    if not quiet:
        if added:
            print(f"[green]Added {len(added)} entries to .gitignore[/green]")
        else:
            print("[dim].gitignore already up to date[/dim]")


def setup_promote(root: str, quiet: bool = False):
    """Called by `pmagent promote setup` — adds marketing gitignore entries."""
    add_entries(root, PROMOTE_ENTRIES, quiet=quiet)


def verify(root: str) -> dict[str, bool]:
    """
    Returns dict of entry -> is_present for all known pmagent entries.
    Useful for diagnostics.
    """
    lines = _read_gitignore(root)
    all_entries = CORE_ENTRIES + PROMOTE_ENTRIES
    return {entry: _already_present(lines, entry) for entry in all_entries}