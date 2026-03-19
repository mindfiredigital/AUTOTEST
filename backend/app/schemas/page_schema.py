"""Pydantic schemas for page endpoints.

Defines request and response models used by the pages router.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class PageCreate(BaseModel):
    """Request model to create a page (URL required)."""

    page_url: HttpUrl = Field(..., description="Canonical URL of the page")
    page_title: Optional[str] = Field(None, description="Optional page title")
    site_id: Optional[int] = Field(None, description="Optional linked site id")


class PageResponse(BaseModel):
    """Representation returned for a single page."""

    id: int
    site_id: Optional[int]
    page_url: str = Field(..., description="Page URL")
    page_title: Optional[str]
    status: str
    created_on: Optional[datetime]

    class Config:
        from_attributes = True


class PaginatedPageResponse(BaseModel):
    """Standard paginated response wrapper for pages."""

    total: int
    page: int
    limit: int
    data: List[PageResponse]


class PageInfoResponse(BaseModel):
    """Detailed information about a page, including counts."""

    page_id: int
    page_title: str | None
    page_url: str
    status: str

    created_on: datetime | None
    updated_on: datetime | None

    test_scenario_count: int
    test_case_count: int
    scheduled_test_case_count: int


class PageUpdateTitleRequest(BaseModel):
    """Request to update a page's title."""

    page_title: str = Field(..., min_length=1, max_length=255, description="New page title")
    

class PageCreateRequest(BaseModel):
    """Alternate create request used by some endpoints (URL required)."""

    page_title: Optional[str] = Field(None, description="Optional page title")
    page_url: str = Field(..., description="Page URL")

