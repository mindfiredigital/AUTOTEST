from datetime import datetime
from pydantic import BaseModel, Field

class TestScenarioBase(BaseModel):
    page_id: int
    title: str = Field(max_length=200)
    data: dict | None = None
    type: str = "auto-generated"  # auto-generated | manual
    category: str | None = None   # functional | auth-positive | auth-negative | ui-validation | validation | navigation | form
    script: str | None = None
    script_path: str | None = None

class TestScenarioCreate(BaseModel):
    page_id: int
    title: str = Field(max_length=200)
    data: dict | None = None
    type: str | None = None
    category: str | None = None
    script: str | None = None
    script_path: str | None = None
    created_on: datetime | None = None
    created_by: int | None = None

class TestScenarioUpdate(BaseModel):
    page_id: int | None = None
    title: str | None = Field(default=None, max_length=200)
    data: dict | None = None
    type: str | None = None
    category: str | None = None
    script: str | None = None
    script_path: str | None = None
    updated_on: datetime | None = None
    updated_by: int | None = None

class TestScenarioOut(TestScenarioBase):
    id: int
    created_on: datetime | None = None
    created_by: int | None = None
    updated_on: datetime | None = None
    updated_by: int | None = None
