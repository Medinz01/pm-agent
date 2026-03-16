import json

CHUNK_SIZE = 6000  # characters per chunk sent to LLM


def chunk_contents(contents: dict[str, str]) -> list[str]:
    """Split repo contents into chunks that fit LLM context."""
    chunks = []
    current = ""
    for path, content in contents.items():
        entry = f"""\n\n### {path}\n```\n{content[:2000]}\n```"""
        if len(current) + len(entry) > CHUNK_SIZE:
            chunks.append(current)
            current = entry
        else:
            current += entry
    if current:
        chunks.append(current)
    return chunks


def analyze_repo(client, file_tree: list[str], contents: dict[str, str]) -> dict:
    """
    Sends repo content to LLM and extracts structured analysis.
    Returns dict with keys: purpose, stack, architecture, entry_points, summary
    """
    tree_str = "\n".join(file_tree)
    chunks = chunk_contents(contents)

    # First pass: understand from file tree
    tree_prompt = f"""You are analyzing a software repository.

File tree:
{tree_str}

Based on the file tree alone, give a brief first impression:
- What kind of project is this?
- What stack/language is likely being used?
- What might the entry point be?

Be concise, 3-5 sentences."""

    first_impression = client.complete(tree_prompt)

    # Second pass: deep analysis from contents (first chunk)
    deep_prompt = f"""You are a senior software architect analyzing a codebase.

Previous impression:
{first_impression}

Codebase (partial):
{chunks[0] if chunks else "No content available"}

Respond ONLY with a valid JSON object — no markdown, no extra text:
{{
  "purpose": "one sentence describing what this project does",
  "goals": ["goal 1", "goal 2"],
  "stack": ["language/framework 1", "language/framework 2"],
  "architecture": "2-3 sentence description of how the system is structured",
  "entry_points": ["file1.py", "index.ts"],
  "summary": "3-4 sentence overview suitable for a README"
}}"""

    raw = client.complete(deep_prompt)

    try:
        # Strip markdown fences if present
        clean = raw.strip().strip("```json").strip("```").strip()
        analysis = json.loads(clean)
    except Exception:
        # Fallback if LLM doesn't return clean JSON
        analysis = {
            "purpose": first_impression,
            "goals": [],
            "stack": [],
            "architecture": first_impression,
            "entry_points": [],
            "summary": first_impression,
        }

    return analysis
