"""
Chat route.

Accepts a validated ChatRequest, delegates to LLMService, and returns
a ChatResponse. This route knows nothing about Groq, the SDK, or how
metadata like latency is calculated -- that's all the service's job.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.api.dependencies import get_llm_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService

router = APIRouter()

@router.post("/api/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: LLMService = Depends(get_llm_service),
) -> ChatResponse:
    """Send a message to the LLM and return the full response."""
    result = await service.chat(
        message=request.message,
        system_prompt=request.system_prompt,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    return ChatResponse(**result)

@router.post("/api/v1/chat/stream")
async def chat_stream(
    request: ChatRequest,
    service: LLMService = Depends(get_llm_service),
) -> StreamingResponse:
    """Send a message to the LLM and stream the response back chunk by chunk."""

    async def event_generator():
        async for chunk in service.chat_stream(
            message=request.message,
            system_prompt=request.system_prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        ):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain")