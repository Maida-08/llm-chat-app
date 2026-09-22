"""
Abstract base class defining the interface every LLM provider must implement.

Nothing outside the `providers/` package should import a provider-specific
SDK (like `groq`, `openai`, `google-generativeai`, etc.) directly. Instead,
routes and services depend on this interface, so any provider can be swapped
in without changing code anywhere else in the app.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class LLMProvider(ABC):
    """Interface that all LLM provider implementations must follow."""

    @abstractmethod
    async def chat(
        self,
        message: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> dict:
        """
        Send a single chat message and return a complete response.

        Returns a dict with keys:
            - "text": str          (the generated response)
            - "tokens_used": int   (total tokens consumed, from the provider)
        """
        raise NotImplementedError

    @abstractmethod
    async def chat_stream(
        self,
        message: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncIterator[str]:
        """
        Send a single chat message and yield the response incrementally,
        chunk by chunk, as it's generated.
        """
        raise NotImplementedError
        yield  # pragma: no cover  (makes this an async generator for type-checkers)