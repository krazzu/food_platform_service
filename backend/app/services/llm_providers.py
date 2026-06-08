"""
Strategy pattern for LLM providers.

Selection via LLM_PROVIDER env var: "anthropic" | "openai" | "ollama"

Each provider returns a LangChain BaseChatModel so the agent code stays
provider-agnostic. Provider-specific packages are imported lazily so
missing extras don't break startup when a different provider is selected.
"""
from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel

from ..config import settings


class LLMProvider(ABC):
    @abstractmethod
    def get_llm(self) -> BaseChatModel: ...

    @abstractmethod
    def is_available(self) -> bool: ...


class AnthropicProvider(LLMProvider):
    def is_available(self) -> bool:
        return bool(settings.anthropic_api_key)

    def get_llm(self) -> BaseChatModel:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0.3,
            max_tokens=2048,
        )


class OpenAIProvider(LLMProvider):
    def is_available(self) -> bool:
        return bool(settings.openai_api_key)

    def get_llm(self) -> BaseChatModel:
        from langchain_openai import ChatOpenAI  # pip: langchain-openai

        kwargs: dict = dict(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3,
            max_tokens=2048,
        )
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        return ChatOpenAI(**kwargs)


class OllamaProvider(LLMProvider):
    def is_available(self) -> bool:
        return True  # local; fails at call-time if Ollama isn't running

    def get_llm(self) -> BaseChatModel:
        from langchain_ollama import ChatOllama  # pip: langchain-ollama

        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.3,
        )


_REGISTRY: dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def get_provider() -> LLMProvider:
    cls = _REGISTRY.get(settings.llm_provider)
    if cls is None:
        supported = ", ".join(_REGISTRY)
        raise ValueError(
            f"Unknown LLM_PROVIDER={settings.llm_provider!r}. "
            f"Supported: {supported}"
        )
    return cls()
