"""
Health check route.

Deliberately has no dependency on the LLM provider or any external
service -- it should reflect only "is this process up and responding,"
so load balancers and orchestrators can use it reliably.
"""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return the service's health status."""
    return HealthResponse(status="healthy")