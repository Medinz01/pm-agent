from pm_agent.llm.ollama_client import OllamaClient
from pm_agent.llm.openai_client import OpenAIClient
from pm_agent.llm.anthropic_client import AnthropicClient


def get_client(cfg: dict):
    provider = cfg.get("provider", "local")
    model = cfg.get("model", "qwen2.5-coder:3b")
    api_key = cfg.get("api_key")

    if provider == "local":
        return OllamaClient(model=model, host=cfg.get("ollama_host"))
    elif provider in ("openai", "groq"):
        base_url = None
        if provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
        return OpenAIClient(model=model, api_key=api_key, base_url=base_url)
    elif provider == "anthropic":
        return AnthropicClient(model=model, api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")