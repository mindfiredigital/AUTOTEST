"""Pydantic schemas for provider model endpoints.

Contains concise request/response models used by provider model routes.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional


class ProviderModelResponse(BaseModel):
    """Full provider model representation returned by the API."""

    id: int = Field(..., description="Primary identifier")
    provider_id: int = Field(..., description="Linked provider id")
    title: str = Field(..., description="Human-friendly title")
    prompt: Optional[str] = Field(None, description="Default prompt template")
    created_on: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_on: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: Optional[int] = Field(None, description="Creator user id")
    updated_by: Optional[int] = Field(None, description="Last updater user id")

    class Config:
        from_attributes = True


class ProviderModelUpdateResponse(BaseModel):
    """Partial provider model used for update responses."""

    id: Optional[int] = Field(None, description="Provider model id if present")
    provider_id: Optional[int] = Field(None, description="Linked provider id")
    title: Optional[str] = Field(None, description="Optional title")
    model: Optional[str] = Field(None, description="Model identifier, e.g., gpt-4")
    prompt: Optional[str] = Field(None, description="Prompt template")
    temperature: Optional[float] = Field(None, description="Sampling temperature")
    updated_by: Optional[int] = Field(None, description="Updater user id")
    updated_on: Optional[datetime] = Field(None, description="Update timestamp")


class ProviderModelUpdateRequest(BaseModel):
    """Request body when updating provider model parameters."""

    id: int = Field(..., description="Provider model id")
    model: str = Field(..., description="Model identifier to use")
    temperature: float = Field(..., description="Sampling temperature")
    prompt: str = Field(..., description="Prompt template")


class ProviderModelItemResponse(BaseModel):
    """Compact provider model representation used in lists."""

    id: int = Field(..., description="Provider model id")
    title: str = Field(..., description="Title")
    model: str = Field(..., description="Model identifier")
    temperature: float = Field(..., description="Temperature value")
    prompt: Optional[str] = Field(None, description="Optional prompt")

    class Config:
        from_attributes = True


class ProviderModelsByProviderResponse(BaseModel):
    """Response grouping provider models under a provider."""

    providerId: int = Field(..., description="Provider id")
    providerTitle: str = Field(..., description="Provider display title")
    models: List[ProviderModelItemResponse] = Field(..., description="List of provider models")