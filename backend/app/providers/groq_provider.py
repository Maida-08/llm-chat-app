"""
Groq implementation of the LLMProvider interface.

This is the ONLY file in the entire application allowed to import and use
the `groq` SDK. Routes and services never see this import — they interact
only through the LLMProvider interface defined in base.py.
"""

from typing import AsyncIterator, Optional

from groq import AsyncGroq

from app.providers.base import LLMProvider
import groq as groq_sdk

from app.core.exceptions import (
    EmptyResponseError,
    ProviderAPIError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)

class GroqProvider(LLMProvider):
    """LLM provider backed by the Groq API."""

    def __init__(self, api_key: str, timeout: int = 30):
        # AsyncGroq is the async client - matches our async route/service functions.
        self._client = AsyncGroq(api_key=api_key, timeout=timeout)

    def _build_messages(self, message: str, system_prompt: Optional[str]) -> list[dict]:
        """Assemble the OpenAI-style messages array Groq's API expects."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        return messages

    async def chat(
        self,
        message: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> dict:
        try:
            completion = await self._client.chat.completions.create(
                model=model,
                messages=self._build_messages(message, system_prompt),
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
        except groq_sdk.AuthenticationError:
            raise ProviderAuthenticationError()
        except groq_sdk.RateLimitError:
            raise ProviderRateLimitError()
        except groq_sdk.APITimeoutError:
            raise ProviderTimeoutError(timeout_seconds=self._client.timeout)
        except groq_sdk.APIError as exc:
            raise ProviderAPIError(str(exc))

        text = completion.choices[0].message.content
        finish_reason = completion.choices[0].finish_reason

        if not text and finish_reason == "length":
            raise EmptyResponseError()

        return {
            "text": text,
            "tokens_used": completion.usage.total_tokens,
        }

    async def chat_stream(
        self,
        message: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=model,
            messages=self._build_messages(message, system_prompt),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta