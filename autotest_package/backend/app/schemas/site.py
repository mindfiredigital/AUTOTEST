from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

class SiteBase(BaseModel):
    site_title: str = Field(max_length=200)
    site_url: HttpUrl  # keep as string; validate URL client-side or switch to HttpUrl if strict
    status: str = "New"  # New | Processing | Pause | Done

class SiteCreate(BaseModel):
    site_title: str = Field(max_length=200)
    site_url: str
    status: str | None = None  # default handled server-side
    created_on: datetime | None = None
    created_by: int | None = None

class SiteUpdate(BaseModel):
    site_title: str | None = Field(default=None, max_length=200)
    site_url: str | None = None
    status: str | None = None
    updated_on: datetime | None = None
    updated_by: int | None = None

class SiteOut(SiteBase):
    id: int
    created_on: datetime | None = None
    created_by: int | None = None
    updated_on: datetime | None = None
    updated_by: int | None = None
