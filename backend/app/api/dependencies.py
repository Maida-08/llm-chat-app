"""
Shared FastAPI dependencies.

Centralizes how services and providers get constructed and injected into
routes. Routes declare a dependency (e.g. `service: LLMService = Depends(get_llm_service)`)
without knowing or caring how LLMService or its provider are built.

This is also the ONE place you'd change to swap GroqProvider for a
different provider -- nothing in routes or services needs to change.
"""

from functools import lru_cache

from app.core.config import settings
from app.providers.groq_provider import GroqProvider
from app.services.llm_service import LLMService


@lru_cache
def get_llm_service() -> LLMService:
    """
    Build (once) and return the LLMService, wired to GroqProvider.

    @lru_cache means this function's body only runs the first time it's
    called -- every subsequent request reuses the same LLMService/provider
    instance instead of reconstructing it per-request.
    """
    provider = GroqProvider(api_key=settings.groq_api_key, timeout=settings.llm_timeout)
    return LLMService(provider=provider)