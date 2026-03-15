from datetime import datetime


PROMPT_TEMPLATE = """
# Project Context — pm-agent

## About This Project
{doc}

---

## Your Task
{task}

---

## Instructions
- Use the project context above to understand the codebase before responding.
- Match the existing architecture, naming conventions, and stack.
- If you need to create new files, place them where they logically belong per the architecture.
- After completing the task, note any design decisions made and why.

"""


def build_prompt(writer, task: str) -> str:
    doc = writer.read_doc()
    if not doc:
        doc = "(PROJECT.md not found — run `pm init` first)"

    prompt = PROMPT_TEMPLATE.format(doc=doc, task=task)

    # Save to file
    import os
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(writer.root, ".pm", "prompts", f"prompt_{timestamp}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    return prompt
