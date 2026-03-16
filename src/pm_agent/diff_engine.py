import os
from pm_agent.doc_writer import DocWriter


def compute_diff(root: str, writer: DocWriter, ignore_patterns: list[str]) -> list[dict]:
    """
    Compare current files against snapshot.
    Returns list of {status, path, content} dicts.
    status: 'added' | 'modified' | 'deleted'
    """
    from indexer import index_repo
    _, contents = index_repo(root, ignore_patterns)

    old_snapshot = writer.load_snapshot()
    new_snapshot = {}
    changes = []

    for path, content in contents.items():
        file_hash = writer.hash_file(os.path.join(root, path))
        new_snapshot[path] = file_hash

        if path not in old_snapshot:
            changes.append({"status": "added", "path": path, "content": content[:500]})
        elif old_snapshot[path] != file_hash:
            changes.append({"status": "modified", "path": path, "content": content[:500]})

    for path in old_snapshot:
        if path not in new_snapshot:
            changes.append({"status": "deleted", "path": path, "content": ""})

    writer.save_snapshot(new_snapshot)
    return changes
