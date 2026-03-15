import click
from rich.console import Console
from config import load_config
from indexer import index_repo, map_repo
from analyzer import analyze_repo
from questioner import run_questioner
from doc_writer import DocWriter
from watcher import start_watcher
from prompt_builder import build_prompt
from llm.factory import get_client

console = Console()

@click.group()
def cli():
    """pm-agent — local AI project management agent."""
    pass


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def init(path):
    """Scan a repo, ask questions, and generate PROJECT.md."""
    cfg = load_config()
    client = get_client(cfg)
    writer = DocWriter(path)

    console.rule("[bold cyan]pm-agent init")

    # 1. Index
    console.print("[cyan]Indexing repository...")
    file_tree, contents = index_repo(path, cfg["ignore_patterns"])
    console.print(f"[green]Found {len(contents)} files.")

    # 2. Code map (AST parse — no LLM needed)
    console.print("[cyan]Mapping functions and classes...")
    code_map = map_repo(contents)
    mapped = sum(len(v) for v in code_map.values())
    console.print(f"[green]Mapped {len(code_map)} code files, {mapped} symbols.")

    # 3. Analyze
    console.print("[cyan]Analyzing with LLM...")
    analysis = analyze_repo(client, file_tree, contents)

    # 4. Q&A
    console.print("[cyan]Running clarifying questions...")
    decisions = run_questioner(client, analysis)

    # 5. Write doc
    console.print("[cyan]Writing PROJECT.md...")
    writer.write_initial(analysis, decisions, code_map=code_map)

    console.rule("[bold green]Done — .pm/PROJECT.md created")


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def watch(path):
    """Watch for file changes and auto-update PROJECT.md."""
    cfg = load_config()
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
    cfg = load_config()
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


if __name__ == "__main__":
    cli()