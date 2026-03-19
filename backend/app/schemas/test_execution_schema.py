"""Schemas for test execution API responses."""

from pydantic import BaseModel, Field
from datetime import datetime


class TestExecutionResponse(BaseModel):
    """Response model representing a test execution record."""

    id: int = Field(..., description="Execution id")
    status: str | None = Field(None, description="Execution status")
    logs: str | None = Field(None, description="Execution logs/text")
    executed_on: datetime | None = Field(None, description="When the execution ran")

    class Config:
        from_attributes = True