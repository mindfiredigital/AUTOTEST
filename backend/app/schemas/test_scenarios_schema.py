"""Schemas for test scenarios and related responses.

Contains lightweight response and request models used by the
test-scenarios endpoints. Docstrings are intentionally short.
"""

import json
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

_MAX_JSON_BYTES = 64 * 1024  # 64 KB


class ScenarioListItem(BaseModel):
    """List item returned in paginated scenario results."""

    id: int
    title: str
    type: str
    category: str | None
    test_case_count: int


class PaginatedScenarioResponse(BaseModel):
    """Paginated response for scenario list endpoints."""

    data: List[ScenarioListItem]
    page: int
    limit: int
    total: int


class TestCaseDetailResponse(BaseModel):
    """Minimal details about a test case within a scenario."""

    id: int
    title: str
    type: str
    is_valid: bool
    is_valid_default: bool


class ScenarioDetailResponse(BaseModel):
    """Detailed scenario payload including its test cases."""

    id: int
    title: str
    type: str
    category: str | None
    created_on: datetime | None
    data: Optional[Dict[str, Any]]
    test_cases: List[TestCaseDetailResponse]


class UpdateScenarioRequest(BaseModel):
    """Request model for partial scenario updates."""
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(None, description="New scenario title")
    category: Optional[str] = Field(None, description="Scenario category")
    type: Optional[str] = Field(None, description="Scenario type")
    data: Optional[Dict] = Field(None, description="Arbitrary scenario data")

    @field_validator("data", mode="before")
    @classmethod
    def limit_json_size(cls, v):
        if v is not None and len(json.dumps(v)) > _MAX_JSON_BYTES:
            raise ValueError("JSON payload exceeds the 64 KB size limit")
        return v
