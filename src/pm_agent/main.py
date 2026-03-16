import os
import click
from pathlib import Path
from rich.console import Console
from pm_agent.config import load_config
from pm_agent.indexer import index_repo, map_repo
from pm_agent.analyzer import analyze_repo
from pm_agent.questioner import run_questioner
from pm_agent.doc_writer import DocWriter
from pm_agent.watcher import start_watcher
from pm_agent.prompt_builder import build_prompt
from pm_agent.llm.factory import get_client

console = Console()

GLOBAL_CONFIG = Path.home() / ".pm-agent" / "config.yaml"


def resolve_config() -> dict:
    """Load global config if it exists, else fall back to local config.yaml."""
    if GLOBAL_CONFIG.exists():
        return load_config(str(GLOBAL_CONFIG))
    return load_config("config.yaml")


@click.group()
def cli():
    """pm-agent — local AI project management agent."""
    pass


@cli.command()
def setup():
    """First-time setup wizard — configure your AI provider."""
    from pm_agent.wizard import run_wizard
    run_wizard()


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def init(path):
    """Scan a repo, ask questions, and generate PROJECT.md."""
    cfg = resolve_config()
    client = get_client(cfg)
    writer = DocWriter(path)

    console.rule("[bold cyan]pm-agent init")

    # 1. Index
    console.print("[cyan]Indexing repository...")
    file_tree, contents = index_repo(path, cfg["ignore_patterns"])
    console.print(f"[green]Found {len(contents)} files.")

    # 2. Code map
    console.print("[cyan]Mapping functions and classes...")
    code_map = map_repo(contents)
    mapped = sum(len(v) for v in code_map.values())
    console.print(f"[green]Mapped {len(code_map)} code files, {mapped} symbols.")

    # 3. Git history
    git_context = ""
    try:
        from pm_agent.git_reader import get_recent_commits, format_commits_for_doc, is_git_repo
        if is_git_repo(path):
            commits = get_recent_commits(path, limit=10)
            if commits:
                console.print(f"[green]Found {len(commits)} recent git commits.")
                git_context = format_commits_for_doc(commits)
    except Exception:
        pass

    # 4. Analyze
    console.print("[cyan]Analyzing with LLM...")
    analysis = analyze_repo(client, file_tree, contents)

    # 5. Q&A
    console.print("[cyan]Running clarifying questions...")
    decisions = run_questioner(client, analysis)

    # 6. Write doc
    console.print("[cyan]Writing PROJECT.md...")
    writer.write_initial(analysis, decisions, code_map=code_map, git_context=git_context)

    # 7. Gitignore
    console.print("[cyan]Updating .gitignore...")
    from pm_agent.gitignore_manager import setup_core
    setup_core(path, quiet=True)
    console.print("[green]  .gitignore updated.")

    console.rule("[bold green]Done — .pm/PROJECT.md created")


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def watch(path):
    """Watch for file changes and auto-update PROJECT.md."""
    cfg = resolve_config()
    client = get_client(cfg)
    writer = DocWriter(path)

    console.rule("[bold cyan]pm-agent watch")
    console.print(f"[cyan]Watching [bold]{path}[/bold] for changes...")
    console.print("[dim]Press Ctrl+C to stop.[/dim]")

    start_watcher(path, cfg, client, writer)


@cli.command()
@click.argument("task")
@click.option("--copy", is_flag=True, help="Copy prompt to clipboard")
def prompt(task, copy):
    """Generate a context-rich LLM prompt for a task."""
    writer = DocWriter(".")
    output = build_prompt(writer, task)

    if copy:
        try:
            import pyperclip
            pyperclip.copy(output)
            console.print("[green]Prompt copied to clipboard.")
        except Exception:
            console.print("[yellow]pyperclip not available, printing instead.")
            console.print(output)
    else:
        console.print(output)


@cli.command()
@click.argument("text")
def decision(text):
    """Manually add a decision to PROJECT.md."""
    writer = DocWriter(".")
    writer.append_decision(text)
    console.print(f"[green]Decision added: {text}")


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def summary(path):
    """Print a quick project status overview in the terminal."""
    from pm_agent.summarizer import print_summary
    doc_path = os.path.join(path, ".pm", "PROJECT.md")
    print_summary(doc_path, repo_path=path)


if __name__ == "__main__":
    cli()