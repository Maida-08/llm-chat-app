"""
Response schema for the Available Models API.
"""

from typing import List
from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Metadata describing a single supported model."""

    id: str
    description: str


class ModelsResponse(BaseModel):
    """Response returned by GET /api/v1/models"""

    models: List[ModelInfo]