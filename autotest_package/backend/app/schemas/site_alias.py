from pydantic import BaseModel, Field

class SiteAliasBase(BaseModel):
    site_id: int
    site_alias_title: str | None = None
    site_alias_url: str

class SiteAliasCreate(BaseModel):
    site_id: int
    site_alias_title: str | None = None
    site_alias_url: str

class SiteAliasUpdate(BaseModel):
    site_alias_title: str | None = None
    site_alias_url: str | None = None

class SiteAliasOut(SiteAliasBase):
    id: int
