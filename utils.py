# utility helpers for pm-agent

def truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "..."

def safe_json(raw: str):
    import json
    clean = raw.strip().strip("```json").strip("```").strip()
    return json.loads(clean)