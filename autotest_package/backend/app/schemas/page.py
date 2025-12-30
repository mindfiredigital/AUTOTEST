from datetime import datetime
from pydantic import BaseModel, Field

class PageBase(BaseModel):
    site_id: int | None = None
    page_url: str
    status: str = "new"  # new|generating_metadata|generating_test_scenarios|generating_test_cases|test_cases_generated|generating_test_scripts|done
    page_title: str | None = Field(default=None, max_length=200)
    page_source: str | None = None
    page_metadata: dict | None = None

class PageCreate(BaseModel):
    site_id: int | None = None
    page_url: str
    status: str | None = None
    page_title: str | None = Field(default=None, max_length=200)
    page_source: str | None = None
    page_metadata: dict | None = None
    created_on: datetime | None = None
    created_by: int | None = None

class PageUpdate(BaseModel):
    site_id: int | None = None
    page_url: str | None = None
    status: str | None = None
    page_title: str | None = Field(default=None, max_length=200)
    page_source: str | None = None
    page_metadata: dict | None = None
    updated_on: datetime | None = None
    updated_by: int | None = None

class PageOut(PageBase):
    id: int
    created_on: datetime | None = None
    created_by: int | None = None
    updated_on: datetime | None = None
    updated_by: int | None = None
