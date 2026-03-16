import json
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def generate_questions(client, analysis: dict) -> list[str]:
    """Ask LLM to generate clarifying architecture/decision questions."""
    prompt = f"""You are a technical lead reviewing a new project.

Project summary:
- Purpose: {analysis.get('purpose', 'unknown')}
- Stack: {', '.join(analysis.get('stack', []))}
- Architecture: {analysis.get('architecture', 'unknown')}

Generate 4-6 short, specific questions to understand the WHY behind key decisions.
Focus on: tech choices, architecture trade-offs, constraints, future plans.

Respond ONLY with a JSON array of question strings:
["question 1", "question 2", ...]"""

    raw = client.complete(prompt)
    try:
        clean = raw.strip().strip("```json").strip("```").strip()
        questions = json.loads(clean)
        if isinstance(questions, list):
            return questions
    except Exception:
        pass

    # Fallback questions
    return [
        "Why did you choose this tech stack over alternatives?",
        "What are the main constraints or limitations of this project?",
        "What does success look like for this project?",
        "Are there any known technical debts or shortcuts taken?",
    ]


def run_questioner(client, analysis: dict) -> list[dict]:
    """
    Run interactive Q&A with user. Returns list of {question, answer} dicts.
    """
    decisions = []

    console.print("\n[bold yellow]Clarifying Questions[/bold yellow]")
    console.print("[dim]Answer these to capture your design decisions. Press Enter to skip.[/dim]\n")

    questions = generate_questions(client, analysis)

    for i, q in enumerate(questions, 1):
        answer = Prompt.ask(f"[cyan]{i}. {q}[/cyan]")
        if answer.strip():
            decisions.append({"question": q, "answer": answer.strip()})

    # Let user add their own
    console.print("\n[bold yellow]Anything the AI missed?[/bold yellow]")
    console.print("[dim]Add your own decisions (empty line to finish):[/dim]\n")

    while True:
        custom = Prompt.ask("[cyan]+ Add decision (or Enter to finish)[/cyan]", default="")
        if not custom.strip():
            break
        decisions.append({"question": "Manual entry", "answer": custom.strip()})

    return decisions
