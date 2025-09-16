from pydantic import BaseModel

class PageLinkTestCaseBase(BaseModel):
    page_link_id: int
    test_case_id_source: int
    verified: bool = False

class PageLinkTestCaseCreate(BaseModel):
    page_link_id: int
    test_case_id_source: int
    verified: bool | None = None

class PageLinkTestCaseUpdate(BaseModel):
    verified: bool | None = None

class PageLinkTestCaseOut(PageLinkTestCaseBase):
    id: int
