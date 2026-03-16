"""
pm-agent first-run setup wizard.
Guides user through local or cloud provider configuration.
"""

import os
import sys
import subprocess
import platform
import psutil
import yaml
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

console = Console()

CONFIG_PATH = Path.home() / ".pm-agent" / "config.yaml"

# ── Model recommendations by available RAM ────────────────────────────────────

LOCAL_MODELS = [
    {
        "name": "qwen2.5-coder:3b",
        "ram_gb": 4,
        "vram_gb": 2,
        "description": "Best for low-end hardware. Code-specialized, fast.",
        "recommended": True,
    },
    {
        "name": "qwen2.5-coder:7b",
        "ram_gb": 8,
        "vram_gb": 4.5,
        "description": "Better quality. Needs 8GB RAM minimum.",
        "recommended": False,
    },
    {
        "name": "llama3.1:8b",
        "ram_gb": 10,
        "vram_gb": 5,
        "description": "General purpose, good instruction following.",
        "recommended": False,
    },
    {
        "name": "deepseek-coder-v2:16b",
        "ram_gb": 16,
        "vram_gb": 10,
        "description": "Best local code model. Needs strong hardware.",
        "recommended": False,
    },
]

CLOUD_PROVIDERS = {
    "groq": {
        "label": "Groq (Free tier — fast, 70B models)",
        "models": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "key_url": "https://console.groq.com/keys",
        "free": True,
    },
    "openai": {
        "label": "OpenAI (Paid — GPT-4o)",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "key_url": "https://platform.openai.com/api-keys",
        "free": False,
    },
    "anthropic": {
        "label": "Anthropic (Paid — Claude)",
        "models": ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"],
        "key_url": "https://console.anthropic.com/settings/keys",
        "free": False,
    },
}


# ── Hardware detection ────────────────────────────────────────────────────────

def get_system_info() -> dict:
    ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    info = {"ram_gb": round(ram_gb, 1), "vram_gb": 0, "gpu_name": "Not detected"}

    try:
        import subprocess
        if platform.system() == "Windows":
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
        else:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(",")
            info["gpu_name"] = parts[0].strip()
            info["vram_gb"] = round(int(parts[1].strip()) / 1024, 1)
    except Exception:
        pass

    return info


def suggest_models(ram_gb: float, vram_gb: float) -> list[dict]:
    """Return models that fit within the user's hardware."""
    return [
        m for m in LOCAL_MODELS
        if m["ram_gb"] <= ram_gb and (vram_gb == 0 or m["vram_gb"] <= vram_gb + 1)
    ]


# ── Ollama detection ──────────────────────────────────────────────────────────

def is_ollama_installed() -> bool:
    try:
        result = subprocess.run(
            ["ollama", "--version"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def get_ollama_models() -> list[str]:
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return []
        lines = result.stdout.strip().splitlines()[1:]  # skip header
        return [line.split()[0] for line in lines if line.strip()]
    except Exception:
        return []


def pull_ollama_model(model: str) -> bool:
    console.print(f"\n[cyan]Pulling {model} from Ollama... (this may take a few minutes)[/cyan]")
    try:
        result = subprocess.run(["ollama", "pull", model], timeout=600)
        return result.returncode == 0
    except Exception:
        return False


def validate_api_key(provider: str, api_key: str, model: str) -> bool:
    """Make a minimal test call to verify the API key works."""
    try:
        if provider == "groq":
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": "hi"}], max_tokens=5
            )
        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": "hi"}], max_tokens=5
            )
        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            client.messages.create(
                model=model, max_tokens=5,
                messages=[{"role": "user", "content": "hi"}]
            )
        return True
    except Exception as e:
        console.print(f"[red]Key validation failed: {e}[/red]")
        return False


# ── Config write ──────────────────────────────────────────────────────────────

def write_config(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)
    console.print(f"\n[green]Config saved to {CONFIG_PATH}[/green]")


# ── Wizard steps ──────────────────────────────────────────────────────────────

def step_welcome():
    console.print(Panel.fit(
        "[bold cyan]Welcome to pm-agent[/bold cyan]\n\n"
        "This wizard will set up your AI provider in a few steps.\n"
        "You can re-run [bold]pm-agent setup[/bold] anytime to change settings.",
        title="Setup Wizard",
        border_style="cyan"
    ))


def step_local_or_cloud() -> str:
    console.print("\n[bold]Step 1 — Choose your AI provider type[/bold]")
    console.print("  [green]1. Local[/green]  — runs on your machine, completely free and private")
    console.print("  [blue]2. Cloud[/blue]  — uses an API (Groq is free, OpenAI/Anthropic are paid)\n")
    choice = Prompt.ask("Choose", choices=["1", "2"], default="1")
    return "local" if choice == "1" else "cloud"


# ── Local flow ────────────────────────────────────────────────────────────────

def flow_local() -> dict:
    console.print("\n[bold]Step 2 — Detecting your hardware...[/bold]")
    info = get_system_info()

    # Show hardware summary
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[dim]RAM[/dim]", f"[white]{info['ram_gb']} GB[/white]")
    table.add_row("[dim]GPU[/dim]", f"[white]{info['gpu_name']}[/white]")
    table.add_row("[dim]VRAM[/dim]", f"[white]{info['vram_gb']} GB[/white]" if info['vram_gb'] else "[dim]Not detected[/dim]")
    console.print(table)

    suitable = suggest_models(info["ram_gb"], info["vram_gb"])
    if not suitable:
        suitable = [LOCAL_MODELS[0]]  # fallback to smallest

    console.print("\n[bold]Step 3 — Check Ollama[/bold]")

    # ── Ollama installed? ──
    if not is_ollama_installed():
        console.print("[yellow]Ollama is not installed on your system.[/yellow]")
        console.print("\nOllama is required to run local models.")
        console.print("[bold]Install it from:[/bold] [link=https://ollama.com]https://ollama.com[/link]")
        console.print("\nOnce installed, re-run: [bold cyan]pm-agent setup[/bold cyan]")

        if Confirm.ask("\nHave you installed Ollama and want to continue?", default=False):
            if not is_ollama_installed():
                console.print("[red]Still not detected. Please restart your terminal after installing.[/red]")
                sys.exit(1)
        else:
            sys.exit(0)

    console.print("[green]✓ Ollama is installed.[/green]")

    # ── Check existing models ──
    existing = get_ollama_models()
    console.print(f"[dim]Models already pulled: {', '.join(existing) if existing else 'none'}[/dim]")

    # Check if a compatible model is already available
    compatible_existing = [m["name"] for m in suitable if m["name"] in existing]

    if compatible_existing:
        chosen = compatible_existing[0]
        console.print(f"\n[green]✓ Found compatible model already installed: {chosen}[/green]")
        use_existing = Confirm.ask(f"Use {chosen}?", default=True)
        if use_existing:
            return {"provider": "local", "model": chosen,
                    "ollama_host": "http://localhost:11434", "api_key": None}

    # ── No compatible model — show options ──
    console.print("\n[bold]Step 4 — Choose a model to pull[/bold]")
    console.print("[dim]Models compatible with your hardware:[/dim]\n")

    for i, m in enumerate(suitable, 1):
        tag = "[bold green] ← recommended[/bold green]" if m["recommended"] else ""
        console.print(f"  {i}. [cyan]{m['name']}[/cyan]{tag}")
        console.print(f"     {m['description']}")
        console.print(f"     Needs: {m['ram_gb']}GB RAM / {m['vram_gb']}GB VRAM\n")

    choice = Prompt.ask(
        "Choose model",
        choices=[str(i) for i in range(1, len(suitable) + 1)],
        default="1"
    )
    chosen_model = suitable[int(choice) - 1]["name"]

    success = pull_ollama_model(chosen_model)
    if not success:
        console.print(f"[red]Failed to pull {chosen_model}. Check your internet and try again.[/red]")
        sys.exit(1)

    console.print(f"[green]✓ {chosen_model} ready.[/green]")
    return {"provider": "local", "model": chosen_model,
            "ollama_host": "http://localhost:11434", "api_key": None}


# ── Cloud flow ────────────────────────────────────────────────────────────────

def flow_cloud() -> dict:
    console.print("\n[bold]Step 2 — Choose a cloud provider[/bold]\n")

    provider_keys = list(CLOUD_PROVIDERS.keys())
    for i, key in enumerate(provider_keys, 1):
        p = CLOUD_PROVIDERS[key]
        free_tag = "[green](free tier)[/green]" if p["free"] else "[dim](paid)[/dim]"
        console.print(f"  {i}. {p['label']} {free_tag}")

    choice = Prompt.ask("\nChoose provider", choices=["1", "2", "3"], default="1")
    provider_key = provider_keys[int(choice) - 1]
    provider = CLOUD_PROVIDERS[provider_key]

    console.print(f"\n[bold]Step 3 — Get your API key[/bold]")
    console.print(f"Get your key here: [link={provider['key_url']}]{provider['key_url']}[/link]\n")

    api_key = Prompt.ask("Paste your API key", password=True)

    # Choose model
    console.print(f"\n[bold]Step 4 — Choose a model[/bold]")
    for i, m in enumerate(provider["models"], 1):
        console.print(f"  {i}. {m}")

    model_choice = Prompt.ask(
        "Choose model",
        choices=[str(i) for i in range(1, len(provider["models"]) + 1)],
        default="1"
    )
    chosen_model = provider["models"][int(model_choice) - 1]

    # Validate
    console.print("\n[cyan]Validating API key...[/cyan]")
    if not validate_api_key(provider_key, api_key, chosen_model):
        console.print("[red]Could not validate API key. Check the key and try again.[/red]")
        sys.exit(1)

    console.print("[green]✓ API key validated.[/green]")

    return {
        "provider": provider_key,
        "model": chosen_model,
        "ollama_host": "http://localhost:11434",
        "api_key": api_key,
    }


# ── Main entry ────────────────────────────────────────────────────────────────

def run_wizard():
    step_welcome()

    # Check if config already exists
    if CONFIG_PATH.exists():
        if not Confirm.ask(
            f"\n[yellow]Existing config found at {CONFIG_PATH}. Overwrite?[/yellow]",
            default=False
        ):
            console.print("[dim]Setup cancelled. Existing config kept.[/dim]")
            return

    provider_type = step_local_or_cloud()

    if provider_type == "local":
        cfg = flow_local()
    else:
        cfg = flow_cloud()

    # Common config fields
    cfg["watch_debounce_seconds"] = 2
    cfg["ignore_patterns"] = [
        "*.pyc", "__pycache__", ".git", "node_modules",
        ".pm", "*.log", "dist", "build", ".venv", "venv"
    ]
    cfg["prompt_output"] = "stdout"

    write_config(cfg)

    console.print(Panel.fit(
        f"[bold green]Setup complete![/bold green]\n\n"
        f"Provider: [cyan]{cfg['provider']}[/cyan]\n"
        f"Model:    [cyan]{cfg['model']}[/cyan]\n\n"
        "Run [bold cyan]pm-agent init[/bold cyan] in any project folder to get started.",
        title="✓ Ready",
        border_style="green"
    ))