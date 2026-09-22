"""
LLM Service layer.

Sits between the API routes and the provider abstraction. Owns
application-level concerns: choosing the model, timing the call,
assembling response metadata, and validating that a requested model
is actually supported.

Routes call this service. This service calls the provider. The provider
is the only place that touches the Groq SDK.
"""

from typing import AsyncIterator, Optional

from app.core.config import settings
from app.core.exceptions import InvalidModelError
from app.providers.base import LLMProvider
from app.utils.timing import Timer
from app.core.logging import logger

# The models this service currently supports. Kept here (not in the schema)
# because "which models are supported" is business/config logic, not a
# pure data-shape rule -- it can change independently of request validation.
SUPPORTED_MODELS = {

    "openai/gpt-oss-120b": "OpenAI GPT-OSS 120B - open-weight reasoning model",
}


class LLMService:
    """Application-level orchestration for chat requests."""

    def __init__(self, provider: LLMProvider):
        # Depends on the LLMProvider interface, not a concrete provider.
        # Swapping providers means changing what gets passed in here --
        # nothing in this class's logic needs to change.
        self._provider = provider

    def _resolve_model(self, requested_model: Optional[str]) -> str:
        """Pick the model to use, and validate it's supported."""
        model = requested_model or settings.default_model
        if model not in SUPPORTED_MODELS:
            raise InvalidModelError(model, list(SUPPORTED_MODELS.keys()))
        return model

    async def chat(
        self,
        message: str,
        system_prompt: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> dict:
        """
        Run a single non-streaming chat request.

        Returns a dict matching ChatResponse's fields:
        response, model, tokens_used, latency_ms.
        """
        resolved_model = self._resolve_model(model)

        timer = Timer()
        timer.start()

        logger.info(
            "chat_request_started",
            extra={"model": resolved_model, "max_tokens": max_tokens},
        )

        try:
            result = await self._provider.chat(
                message=message,
                model=resolved_model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            logger.error(
                "chat_request_failed",
                extra={
                    "model": resolved_model,
                    "latency_ms": timer.elapsed_ms(),
                    "error_type": type(exc).__name__,
                },
            )
            raise

        latency_ms = timer.elapsed_ms()

        logger.info(
            "chat_request_completed",
            extra={
                "model": resolved_model,
                "tokens_used": result["tokens_used"],
                "latency_ms": latency_ms,
            },
        )

        return {
            "response": result["text"],
            "model": resolved_model,
            "tokens_used": result["tokens_used"],
            "latency_ms": latency_ms,
        }

    async def chat_stream(
        self,
        message: str,
        system_prompt: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        """Run a streaming chat request, yielding text chunks as they arrive."""
        resolved_model = self._resolve_model(model)

        async for chunk in self._provider.chat_stream(
            message=message,
            model=resolved_model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk

    def list_models(self) -> list[dict]:
        """Return supported models for the /models endpoint."""
        return [
            {"id": model_id, "description": description}
            for model_id, description in SUPPORTED_MODELS.items()
        ]