"""
Shared pytest fixtures.

Provides a FastAPI TestClient wired to a fake LLM provider, so no test
in this suite ever makes a real network call to Groq.
"""

from typing import AsyncIterator, Optional

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_llm_service
from app.main import app
from app.providers.base import LLMProvider
from app.services.llm_service import LLMService


class FakeProvider(LLMProvider):
    """A fake LLMProvider returning fixed, predictable data -- no network calls."""

    async def chat(
        self,
        message: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> dict:
        return {"text": "This is a fake response.", "tokens_used": 42}

    async def chat_stream(
        self,
        message: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncIterator[str]:
        for chunk in ["This ", "is ", "a ", "fake ", "stream."]:
            yield chunk


@pytest.fixture
def client() -> TestClient:
    """A TestClient with the real LLMService, but wired to FakeProvider."""

    fake_service = LLMService(provider=FakeProvider())

    # FastAPI's dependency_overrides lets us swap out get_llm_service just
    # for tests, without touching app/api/dependencies.py at all.
    app.dependency_overrides[get_llm_service] = lambda: fake_service

    test_client = TestClient(app)
    yield test_client

    # Clean up the override after each test so tests don't leak state into each other.
    app.dependency_overrides.clear()