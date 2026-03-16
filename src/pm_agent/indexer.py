import os
import ast
import pathspec
from pathlib import Path

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".exe", ".dll", ".so",
    ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3",
    ".db", ".sqlite", ".lock",
}

MAX_FILE_SIZE_KB = 100


def load_gitignore(root: str) -> pathspec.PathSpec:
    gitignore_path = os.path.join(root, ".gitignore")
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            patterns = f.read().splitlines()
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def index_repo(root: str, extra_ignores: list[str]) -> tuple[list[str], dict[str, str]]:
    """
    Returns:
        file_tree: list of relative paths
        contents:  dict of relative_path -> file content (text files only)
    """
    gitignore = load_gitignore(root)
    extra_spec = pathspec.PathSpec.from_lines("gitwildmatch", extra_ignores)

    file_tree = []
    contents = {}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if not gitignore.match_file(os.path.relpath(os.path.join(dirpath, d), root))
            and not extra_spec.match_file(d)
        ]

        for filename in filenames:
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, root)

            if gitignore.match_file(rel_path):
                continue
            if extra_spec.match_file(rel_path):
                continue

            ext = Path(filename).suffix.lower()
            if ext in BINARY_EXTENSIONS:
                continue

            size_kb = os.path.getsize(abs_path) / 1024
            if size_kb > MAX_FILE_SIZE_KB:
                file_tree.append(rel_path + "  [skipped: too large]")
                continue

            file_tree.append(rel_path)

            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    contents[rel_path] = f.read()
            except Exception:
                pass

    return file_tree, contents


# ── AST-based code map ────────────────────────────────────────────────────────

def _get_docstring(node) -> str:
    """Extract docstring from a function or class node."""
    try:
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            doc = first.value.s.strip().splitlines()[0]  # first line only
            return f" — {doc}"
    except Exception:
        pass
    return ""


def _parse_python_file(content: str) -> list[str]:
    """
    Parse a Python file and extract:
    - Top-level functions with docstring (first line)
    - Classes with their methods and docstrings
    """
    entries = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return ["[could not parse — syntax error]"]

    for node in ast.walk(tree):
        # Only top-level nodes
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        # Skip if it's nested (parent is not Module)
        pass

    # Walk only top-level body
    for node in ast.parse(content).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = _get_docstring(node)
            entries.append(f"- `{node.name}(){doc}`")

        elif isinstance(node, ast.ClassDef):
            class_doc = _get_docstring(node)
            entries.append(f"- `{node.name}`{class_doc}")
            # Add methods
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_doc = _get_docstring(item)
                    entries.append(f"  - `.{item.name}(){method_doc}`")

    return entries if entries else ["[no public functions or classes found]"]


def _parse_js_ts_file(content: str) -> list[str]:
    """
    Simple regex-based extraction for JS/TS files.
    Extracts: function declarations, arrow functions, class declarations, exports.
    """
    import re
    entries = []

    patterns = [
        (r"^export default function\s+(\w+)", "function"),
        (r"^export function\s+(\w+)", "function"),
        (r"^async function\s+(\w+)", "async function"),
        (r"^function\s+(\w+)", "function"),
        (r"^export class\s+(\w+)", "class"),
        (r"^class\s+(\w+)", "class"),
        (r"^export const\s+(\w+)\s*=\s*(?:async\s+)?\(", "const arrow fn"),
        (r"^const\s+(\w+)\s*=\s*(?:async\s+)?\(", "const arrow fn"),
    ]

    for line in content.splitlines():
        line = line.strip()
        for pattern, kind in patterns:
            match = re.match(pattern, line)
            if match:
                name = match.group(1)
                entries.append(f"- `{name}` ({kind})")
                break

    return entries if entries else ["[no extractable symbols found]"]


def map_repo(contents: dict[str, str]) -> dict[str, list[str]]:
    """
    Build a code map: file path -> list of function/class entries.
    Supports Python (AST) and JS/TS (regex).
    Skips config, markdown, and other non-code files.
    """
    code_map = {}

    for path, content in contents.items():
        ext = Path(path).suffix.lower()

        if ext == ".py":
            entries = _parse_python_file(content)
            code_map[path] = entries

        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            entries = _parse_js_ts_file(content)
            code_map[path] = entries

        # Skip .md, .yaml, .json, .txt, etc.

    return code_map