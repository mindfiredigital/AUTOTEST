from datetime import datetime
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Literal


class SiteBase(BaseModel):
    site_title: str
    site_url: HttpUrl


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    site_title: Optional[str] = None
    site_url: Optional[HttpUrl] = None
    status: Optional[Literal["New", "Processing", "Pause", "Done"]] = None


class SiteResponse(SiteBase):
    id: int
    status: Optional[Literal["New", "Processing", "Pause", "Done", ""]] = None
    created_on: Optional[datetime]

    class Config:
        from_attributes = True


class PaginatedSiteResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[SiteResponse]
