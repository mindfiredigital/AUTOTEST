"""Schemas for test case endpoints.

Provides concise request and response models used by the test case router.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class TestCaseDetailResponse(BaseModel):
    """Detailed test case representation returned by the API."""

    id: int = Field(..., description="Test case id")
    title: str = Field(..., description="Test case title")
    type: str = Field(..., description="Test case type")
    data: Optional[Dict] = Field(None, description="Raw input data for the case")
    expected_outcome: Optional[Dict] = Field(None, description="Expected output structure")
    validation: Optional[Dict] = Field(None, description="Validation rules")
    is_valid: bool = Field(..., description="Whether this case is currently valid")
    is_valid_default: bool = Field(..., description="Default validity flag")
    created_on: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_on: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class UpdateTestCaseRequest(BaseModel):
    """Fields accepted when updating a test case (all optional)."""

    title: Optional[str] = Field(None, description="New title")
    type: Optional[str] = Field(None, description="New type")
    data: Optional[Dict] = Field(None, description="Updated data")
    expected_outcome: Optional[Dict] = Field(None, description="Updated expected outcome")
    validation: Optional[Dict] = Field(None, description="Updated validation rules")
    is_valid: Optional[bool] = Field(None, description="Updated validity")
    is_valid_default: Optional[bool] = Field(None, description="Updated default validity")


class TestCaseBase(BaseModel):
    """Base fields for creating a test case."""

    title: str = Field(..., max_length=200, description="Test case title")
    type: Optional[str] = Field("auto-generated", description="Type of test case")
    data: Optional[Dict] = Field(None, description="Input data for the test")
    expected_outcome: Optional[Dict] = Field(None, description="Expected outcome")
    validation: Optional[Dict] = Field(None, description="Validation rules")
    is_valid: Optional[bool] = Field(True, description="Whether the case is valid")
    is_valid_default: Optional[bool] = Field(False, description="Default validity flag")


class CreateTestCaseRequest(TestCaseBase):
    """Request to create a test case tied to a test scenario."""

    test_scenario_id: int = Field(..., description="Owning test scenario id")


class TestCaseResponse(BaseModel):
    """Compact response model for returning test case summaries."""

    id: int
    title: str
    type: str
    data: Optional[Dict]
    expected_outcome: Optional[Dict]
    validation: Optional[Dict]
    is_valid: bool
    is_valid_default: bool
    created_on: Optional[datetime]
    updated_on: Optional[datetime]

    class Config:
        from_attributes = True

