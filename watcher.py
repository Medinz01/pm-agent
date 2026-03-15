import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console
from diff_engine import compute_diff
from analyzer import CHUNK_SIZE

console = Console()


class RepoEventHandler(FileSystemEventHandler):
    def __init__(self, root, cfg, client, writer):
        self.root = root
        self.cfg = cfg
        self.client = client
        self.writer = writer
        self.debounce = cfg.get("watch_debounce_seconds", 2)
        self._last_trigger = 0
        self._pending = False

    def on_any_event(self, event):
        if event.is_directory:
            return
        # Ignore .pm directory and ignored patterns
        rel = os.path.relpath(event.src_path, self.root)
        for pattern in self.cfg.get("ignore_patterns", []):
            if pattern.strip("*") in rel:
                return
        self._pending = True
        self._last_trigger = time.time()

    def flush_if_ready(self):
        if not self._pending:
            return
        if time.time() - self._last_trigger < self.debounce:
            return
        self._pending = False
        self._process_changes()

    def _process_changes(self):
        changes = compute_diff(self.root, self.writer, self.cfg.get("ignore_patterns", []))
        if not changes:
            return

        console.print(f"[cyan]Detected {len(changes)} change(s), updating doc...")

        # Build summary prompt
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
            # Fallback: just log the changed files
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
