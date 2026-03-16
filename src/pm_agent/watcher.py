import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console
from pm_agent.diff_engine import compute_diff
from pm_agent.analyzer import CHUNK_SIZE
from pm_agent.indexer import map_repo
from pathlib import Path

console = Console()

CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx"}


class RepoEventHandler(FileSystemEventHandler):
    def __init__(self, root, cfg, client, writer):
        self.root = root
        self.cfg = cfg
        self.client = client
        self.writer = writer
        self.debounce = cfg.get("watch_debounce_seconds", 2)
        self._last_trigger = 0
        self._pending = False
        self._changed_paths = set()

    def on_any_event(self, event):
        if event.is_directory:
            return
        rel = os.path.relpath(event.src_path, self.root)
        for pattern in self.cfg.get("ignore_patterns", []):
            if pattern.strip("*") in rel:
                return
        self._pending = True
        self._last_trigger = time.time()
        self._changed_paths.add(rel)

    def flush_if_ready(self):
        if not self._pending:
            return
        if time.time() - self._last_trigger < self.debounce:
            return
        self._pending = False
        changed = set(self._changed_paths)
        self._changed_paths.clear()
        self._process_changes(changed)

    def _process_changes(self, changed_paths: set):
        changes = compute_diff(self.root, self.writer, self.cfg.get("ignore_patterns", []))
        if not changes:
            return

        console.print(f"[cyan]Detected {len(changes)} change(s), updating doc...")

        # ── Update Code Map if any code files changed ──
        has_code_changes = any(
            Path(p).suffix.lower() in CODE_EXTENSIONS
            for p in changed_paths
        )

        if has_code_changes:
            from pm_agent.indexer import index_repo
            _, contents = index_repo(self.root, self.cfg.get("ignore_patterns", []))
            new_code_map = map_repo(contents)
            self.writer.update_code_map(new_code_map)
            console.print("[dim]  ↻ Code Map updated[/dim]")

        # ── LLM changelog summary ──
        change_summary = "\n".join(
            f"- [{c['status'].upper()}] {c['path']}" for c in changes
        )
        content_preview = "\n".join(
            f"### {c['path']}\n```\n{c['content']}\n```"
            for c in changes if c["status"] != "deleted"
        )[:CHUNK_SIZE]

        doc = self.writer.read_doc()
        prompt = f"""You are a project documentation agent.

Current PROJECT.md summary:
{doc[:1000]}

Recent file changes:
{change_summary}

Changed file contents (preview):
{content_preview}

Write 1-3 concise changelog entries describing what changed and why it matters.
Return only a JSON array of strings:
["entry 1", "entry 2"]"""

        raw = self.client.complete(prompt)
        try:
            import json
            clean = raw.strip().strip("```json").strip("```").strip()
            entries = json.loads(clean)
            if isinstance(entries, list):
                self.writer.append_changelog(entries)
                for e in entries:
                    console.print(f"[green]  + {e}")
        except Exception:
            entries = [f"{c['status'].capitalize()}: {c['path']}" for c in changes]
            self.writer.append_changelog(entries)


def start_watcher(root: str, cfg: dict, client, writer):
    handler = RepoEventHandler(root, cfg, client, writer)
    observer = Observer()
    observer.schedule(handler, root, recursive=True)
    observer.start()
    try:
        while True:
            handler.flush_if_ready()
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[yellow]Watcher stopped.")
    observer.join()