import yaml
import os

DEFAULT_CONFIG = {
    "provider": "local",
    "model": "qwen2.5-coder:3b",
    "ollama_host": "http://localhost:11434",
    "api_key": None,
    "watch_debounce_seconds": 2,
    "ignore_patterns": [
        "*.pyc", "__pycache__", ".git", "node_modules",
        ".pm", "*.log", "dist", "build", ".venv", "venv"
    ],
    "prompt_output": "stdout",
}

def load_config(path: str = "config.yaml") -> dict:
    if not os.path.exists(path):
        return DEFAULT_CONFIG.copy()
    with open(path, "r") as f:
        user = yaml.safe_load(f) or {}
    cfg = DEFAULT_CONFIG.copy()
    cfg.update({k: v for k, v in user.items() if v is not None})
    return cfg
