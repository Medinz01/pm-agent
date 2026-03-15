# pm-agent

> A local-first AI project management agent — reads your repo, documents it, watches for changes, and builds LLM prompts. Runs entirely on your machine. Zero API cost.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Ollama](https://img.shields.io/badge/Ollama-local-green?logo=ollama)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Status](https://img.shields.io/badge/status-v0.1.0-orange)

---

## What it does

pm-agent runs alongside your development workflow. Point it at any repo — new or existing — and it:

- **Reads** the entire codebase and maps every file, function, and class
- **Asks** clarifying questions to capture *why* decisions were made
- **Writes** a living `PROJECT.md` — purpose, architecture, code map, decisions, changelog
- **Watches** for file saves and auto-updates the doc in the background
- **Builds** context-rich prompts you can paste into any LLM to continue development

No code leaves your machine unless you explicitly configure a cloud provider.

---

## Demo

```
$ python main.py init

── pm-agent init ──────────────────────────────
Indexing repository...        Found 20 files.
Mapping functions and classes... Mapped 16 files, 54 symbols.
Analyzing with LLM...
Running clarifying questions...

1. Why choose Python for this project?
2. What constraints did you face selecting models?
...

Done — .pm/PROJECT.md created
```

```
$ python main.py watch

Watching . for changes...
Detected 1 change(s), updating doc...
  + Added JWT token validation in auth.py
  + Updated config.yaml with jwt_secret field
```

```
$ python main.py prompt "add rate limiting to the API"

# Project Context — pm-agent
## About This Project ...
## Your Task
add rate limiting to the API
## Instructions ...
```

---

## Installation

```bash
git clone https://github.com/Medinz01/pm-agent.git
cd pm-agent
pip install -r requirements.txt
```

Install and start Ollama, then pull the recommended model:

```bash
ollama pull qwen2.5-coder:3b
```

---

## Usage

### Initialize a project

```bash
# Current directory
python main.py init

# Existing project elsewhere
python main.py init /path/to/your/project
```

### Watch for changes

```bash
python main.py watch
```

Run this in a second terminal while you develop. Every file save triggers an automatic changelog update.

### Generate a task prompt

```bash
python main.py prompt "add user authentication"
python main.py prompt "find the bug in the payment flow"
python main.py prompt "refactor the database layer"
```

Copy the output and paste into any LLM — Claude, ChatGPT, Gemini, whatever you have access to.

### Add a decision manually

```bash
python main.py decision "chose SQLite over PostgreSQL — single user, no concurrency needed"
```

---

## Configuration

Edit `config.yaml` to switch providers:

```yaml
# Local (default — free, private)
provider: local
model: qwen2.5-coder:3b
ollama_host: http://localhost:11434

# Groq (free tier — fast, 70B models)
provider: groq
model: llama-3.1-70b-versatile
api_key: your_groq_key

# OpenAI
provider: openai
model: gpt-4o
api_key: your_openai_key

# Anthropic
provider: anthropic
model: claude-sonnet-4-20250514
api_key: your_anthropic_key
```

---

## Supported Providers

| Provider | Free? | Recommended model |
|---|---|---|
| Ollama (local) | ✅ Always free | `qwen2.5-coder:3b` |
| Groq | ✅ Free tier | `llama-3.1-70b-versatile` |
| OpenAI | ❌ Paid | `gpt-4o` |
| Anthropic | ❌ Paid | `claude-sonnet-4-20250514` |

---

## Output — `.pm/PROJECT.md`

```markdown
# my-project

## Purpose
...

## Code Map
### auth.py
- `generate_token() — Creates a signed JWT for a given user ID`
- `verify_token() — Validates and decodes an incoming JWT`

## Design Decisions
| Question | Decision / Answer | Date |
|---|---|---|
| Why SQLite? | Single user, no concurrency | 2026-03-15 |

## Changelog
### 2026-03-15
- Added JWT token generation in auth.py
- Updated config to include jwt_secret
```

---

## Hardware requirements

Tested on Intel i5 10th gen, 16GB RAM, GTX 1650 4GB VRAM.

| Model | VRAM | Speed |
|---|---|---|
| `qwen2.5-coder:3b` | ~2GB | Fast |
| `qwen2.5-coder:7b` | ~4.5GB | Slow (spills to RAM) |
| Any cloud model | 0 | Depends on API |

---

## Project structure

```
pm-agent/
├── main.py              # CLI entry point
├── config.py            # Load config.yaml
├── indexer.py           # Repo walker + AST code map
├── analyzer.py          # LLM-based repo analysis
├── questioner.py        # Interactive Q&A
├── doc_writer.py        # Read/write PROJECT.md
├── diff_engine.py       # File hash diffing
├── watcher.py           # Watchdog file monitor
├── prompt_builder.py    # Task prompt generator
├── llm/
│   ├── base.py          # Abstract LLM interface
│   ├── factory.py       # Provider selector
│   ├── ollama_client.py
│   ├── openai_client.py
│   └── anthropic_client.py
└── config.yaml
```

---

## Roadmap

- [x] Repo indexing and AST code map
- [x] LLM analysis and Q&A
- [x] Living PROJECT.md doc
- [x] File watcher with auto-changelog
- [x] Task prompt builder
- [x] Multi-provider support (Ollama, OpenAI, Groq, Anthropic)
- [ ] Git commit awareness
- [ ] `pm summary` — quick status in terminal
- [ ] PyPI package
- [ ] VS Code extension

---

## License

MIT