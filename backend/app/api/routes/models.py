"""
Available Models route.
"""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_llm_service
from app.schemas.models import ModelsResponse
from app.services.llm_service import LLMService

router = APIRouter()


@router.get("/api/v1/models", response_model=ModelsResponse)
async def list_models(
    service: LLMService = Depends(get_llm_service),
) -> ModelsResponse:
    """Return the list of models supported by this service."""
    models = service.list_models()
    return ModelsResponse(models=models)