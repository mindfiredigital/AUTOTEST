
"""Pydantic schemas for settings API requests and responses.

Keep these models concise — they are used as request/response
contracts for FastAPI endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SettingCategoryResponse(BaseModel):
    """Minimal representation of a setting category."""

    id: int
    title: str


class SettingUpdateActualValue(BaseModel):
    """Request body to update a single setting's actual value."""

    actual_value: str = Field(..., description="New actual value for the setting")


class SettingUpdateItem(BaseModel):
    """Item used within a bulk update request."""

    id: int = Field(..., description="Setting id")
    actual_value: Optional[str] = Field(None, description="New actual value")


class BulkSettingUpdateRequest(BaseModel):
    """Bulk update request containing multiple `SettingUpdateItem`s."""

    settings: List[SettingUpdateItem]


class SettingResponse(BaseModel):
    """Full setting response model returned by the API."""

    id: int
    key: str
    title: str
    description: Optional[str]
    type: str
    possible_values: Optional[str]
    default_value: Optional[str]
    actual_value: Optional[str]
    setting_category_id: int
    updated_on: Optional[datetime]
    updated_by: Optional[int]

    class Config:
        from_attributes = True
