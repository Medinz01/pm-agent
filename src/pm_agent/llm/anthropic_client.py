import anthropic
from pm_agent.llm.base import LLMClient


class AnthropicClient(LLMClient):
    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str = None):
        self.model = model
        self._client = anthropic.Anthropic(api_key=api_key)

    def complete(self, prompt: str, system: str = "") -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        response = self._client.messages.create(**kwargs)
        return response.content[0].text

    def __repr__(self):
        return f"AnthropicClient(model={self.model})"
