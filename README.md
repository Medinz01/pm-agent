# pm-agent

> A local-first AI project management agent — reads your repo, documents it, watches for changes, and builds LLM prompts. Runs entirely on your machine. Zero API cost.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Ollama](https://img.shields.io/badge/Ollama-local-green?logo=ollama)
![PyPI](https://img.shields.io/pypi/v/pmagent-cli?color=orange&label=pmagent-cli)
![CI](https://github.com/Medinz01/pm-agent/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## What it does

pm-agent runs alongside your development workflow. Point it at any repo — new or existing — and it:

- **Reads** the entire codebase and maps every file, function, and class via AST
- **Asks** clarifying questions to capture *why* decisions were made
- **Writes** a living `.pm/PROJECT.md` — purpose, architecture, code map, decisions, git history, changelog
- **Watches** for file saves and auto-updates the doc in the background
- **Builds** context-rich prompts you can paste into any LLM to continue development
- **Auto-updates** `.gitignore` so API keys and internal state never get committed

No code leaves your machine unless you explicitly configure a cloud provider.

---

## Install

```bash
pip install pmagent-cli
```

Then run the setup wizard:

```bash
pmagent setup
```

The wizard detects your hardware, checks if Ollama is installed, recommends the best local model for your machine, and saves config to `~/.pm-agent/config.yaml`.

---

## Usage

### Initialize a project

```bash
pmagent init                          # current directory
pmagent init /path/to/your/project   # existing project
```

### Watch for changes

```bash
pmagent watch
```

Run in a second terminal while you develop. Every file save triggers an automatic changelog + code map update.

### Generate a task prompt

```bash
pmagent prompt "add user authentication"
pmagent prompt "find the bug in the payment flow"
pmagent prompt "refactor the database layer"
pmagent prompt "add rate limiting" --copy    # copies to clipboard
```

Paste the output into any LLM — Claude, ChatGPT, Gemini, whatever you have access to.

### Quick project summary

```bash
pmagent summary
```

Prints purpose, stack, stats (files mapped, symbols, decisions, changelog entries), and recent git commits.

### Add a decision manually

```bash
pmagent decision "chose SQLite over PostgreSQL — single user, no concurrency needed"
```

---

## Demo

```
$ pmagent init

── pm-agent init ────────────────────────────────────
Indexing repository...           Found 26 files.
Mapping functions and classes... Mapped 19 files, 80 symbols.
Found 3 recent git commits.
Analyzing with LLM...
Running clarifying questions...

1. Why choose Python for this project?
2. What constraints did you face selecting models?
...

Updating .gitignore...   .gitignore updated.
Done — .pm/PROJECT.md created
```

```
$ pmagent watch

Watching . for changes...
Detected 1 change(s), updating doc...
  ↻ Code Map updated
  + Added JWT token validation in auth.py
  + Updated config.yaml with jwt_secret field
```

```
$ pmagent summary

─────────────────── pm-agent ───────────────────

Purpose
  A local-first AI project management agent...

Stack
  Python, Ollama, OpenAI, Anthropic

Stats
  Code files mapped     19
  Symbols (fn/class)    80
  Design decisions       7
  Changelog entries     12
  Last change     2026-03-16

Recent commits
  c6ebf98 fix: remove unused cfg variable
  ba55feb feat: pm-agent v0.1.0
```

---

## Configuration

Config lives at `~/.pm-agent/config.yaml` after running `pmagent setup`. Edit to switch providers:

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

## Git History
- `a1b2c3d` 2026-03-16 — feat: add JWT auth  John Doe

## Design Decisions
| Question | Decision / Answer | Date |
|---|---|---|
| Why SQLite? | Single user, no concurrency needed | 2026-03-16 |

## Changelog
### 2026-03-16
- Added JWT token generation in auth.py
- Updated config to include jwt_secret
```

> `.pm/PROJECT.md` is committed to git — it's the value. Internal state files are auto-added to `.gitignore`.

---

## CI / Tests

Every push to `main` runs automated tests via GitHub Actions — no Ollama or API key required.

| Test | What it validates |
|---|---|
| `pyflakes` lint | No unused imports or variables across all modules |
| Config loader | `load_config()` returns valid defaults |
| Indexer | Walks repo, returns files, finds `main.py` in code map |
| AST code map | Detects `cli()` function correctly in `main.py` |
| Doc writer | Creates `PROJECT.md` with all required sections |
| Prompt builder | Builds prompt containing task text and project context |

---

## Hardware requirements

Tested on Intel i5 10th gen, 16GB RAM, GTX 1650 4GB VRAM.

| Model | VRAM needed | Speed on 4GB card |
|---|---|---|
| `qwen2.5-coder:3b` | ~2GB | ✅ Fast — fits in VRAM |
| `qwen2.5-coder:7b` | ~4.5GB | ⚠️ Slow — spills to RAM |
| Any cloud model | 0 | Depends on API |

---

## Project structure

```
src/pm_agent/
├── main.py              # CLI entry point
├── config.py            # Load config.yaml
├── indexer.py           # Repo walker + AST code map
├── analyzer.py          # LLM-based repo analysis
├── questioner.py        # Interactive Q&A
├── doc_writer.py        # Read/write PROJECT.md
├── diff_engine.py       # File hash diffing
├── watcher.py           # Watchdog file monitor + code map refresh
├── prompt_builder.py    # Task prompt generator
├── wizard.py            # First-run setup wizard
├── git_reader.py        # Git commit history awareness
├── summarizer.py        # Terminal project status summary
├── gitignore_manager.py # Auto-add entries to .gitignore
└── llm/
    ├── base.py          # Abstract LLM interface
    ├── factory.py       # Provider selector
    ├── ollama_client.py
    ├── openai_client.py
    └── anthropic_client.py
```

---

## Roadmap

- [x] Repo indexing and AST code map
- [x] LLM analysis and Q&A
- [x] Living PROJECT.md doc
- [x] File watcher with auto-changelog + code map refresh
- [x] Task prompt builder
- [x] Multi-provider support (Ollama, OpenAI, Groq, Anthropic)
- [x] First-run setup wizard with hardware detection
- [x] Git commit awareness
- [x] `pmagent summary` — quick status in terminal
- [x] PyPI package (`pip install pmagent-cli`)
- [x] Auto-gitignore management
- [ ] Promote engine — Reddit, HN, Dev.to, Slack
- [ ] VS Code extension

---

## License

MIT