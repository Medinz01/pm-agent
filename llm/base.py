class LLMClient:
    """Abstract base for all LLM providers."""

    def complete(self, prompt: str, system: str = "") -> str:
        raise NotImplementedError

    def __repr__(self):
        return f"{self.__class__.__name__}()"
