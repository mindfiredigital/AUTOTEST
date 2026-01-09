from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class PageCreate(BaseModel):
    page_url: HttpUrl
    page_title: Optional[str] = None
    site_id: Optional[int] = None


class PageResponse(BaseModel):
    id: int
    site_id: Optional[int]
    page_url: str
    page_title: Optional[str]
    status: str
    created_on: Optional[datetime]

    class Config:
        from_attributes = True


class PaginatedPageResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[PageResponse]
