from pydantic import BaseModel, Field

class PageLinkBase(BaseModel):
    page_id_source: int
    test_scenario_id_source: int | None = None
    page_id_target: int
    event_selector: str | None = Field(default=None, max_length=512)
    event_description: str | None = Field(default=None, max_length=1024)

class PageLinkCreate(BaseModel):
    page_id_source: int
    test_scenario_id_source: int | None = None
    page_id_target: int
    event_selector: str | None = Field(default=None, max_length=512)
    event_description: str | None = Field(default=None, max_length=1024)

class PageLinkUpdate(BaseModel):
    test_scenario_id_source: int | None = None
    page_id_target: int | None = None
    event_selector: str | None = Field(default=None, max_length=512)
    event_description: str | None = Field(default=None, max_length=1024)

class PageLinkOut(PageLinkBase):
    id: int
