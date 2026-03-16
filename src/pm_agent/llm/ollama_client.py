import ollama
from pm_agent.llm.base import LLMClient


class OllamaClient(LLMClient):
    def __init__(self, model: str = "qwen2.5-coder:3b", host: str = None):
        self.model = model
        self.host = host or "http://localhost:11434"
        self._client = ollama.Client(host=self.host)

    def complete(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat(model=self.model, messages=messages)
        return response["message"]["content"]

    def __repr__(self):
        return f"OllamaClient(model={self.model})"
