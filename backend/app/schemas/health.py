"""
Response schema for the Health Check API.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response returned by GET /health"""

    status: str