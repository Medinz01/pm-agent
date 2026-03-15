from openai import OpenAI
from llm.base import LLMClient


class OpenAIClient(LLMClient):
    def __init__(self, model: str = "gpt-4o", api_key: str = None, base_url: str = None):
        self.model = model
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)

    def complete(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000,
        )
        return response.choices[0].message.content

    def __repr__(self):
        return f"OpenAIClient(model={self.model})"
