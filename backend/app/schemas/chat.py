"""
Request/response schemas for the Chat API.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Incoming payload for POST /api/v1/chat"""

    message: str = Field(
        ...,
        min_length=1,
        description="The user's message to send to the LLM.",
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional system instruction to steer the model's behavior.",
    )
    model: Optional[str] = Field(
        default=None,
        description="Model ID to use. Falls back to DEFAULT_MODEL if not provided.",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature. 0 = deterministic, 2 = very random.",
    )
    max_tokens: int = Field(
        default=1024,
        gt=0,
        le=8192,
        description="Maximum number of tokens to generate in the response.",
    )

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, v: str) -> str:
        """Reject messages that are empty or only whitespace."""
        if not v.strip():
            raise ValueError("message must not be empty or whitespace only")
        return v


class ChatResponse(BaseModel):
    """Response returned by POST /api/v1/chat"""

    response: str
    model: str
    tokens_used: int
    latency_ms: int