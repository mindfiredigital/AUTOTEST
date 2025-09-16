from datetime import datetime
from pydantic import BaseModel, Field

class TestSuiteBase(BaseModel):
    site_id: int
    title: str = Field(max_length=200)
    scenario_count: int | None = None
    test_case_count: int | None = None
    # If you decided to keep list fields as text per XLSX:
    # test_scenario_ids: str | None = None  # e.g., "[1,2,3]"
    # test_case_ids: str | None = None      # e.g., "[1,2,3,4,5]"

class TestSuiteCreate(BaseModel):
    site_id: int
    title: str = Field(max_length=200)
    scenario_count: int | None = None
    test_case_count: int | None = None
    # test_scenario_ids: str | None = None
    # test_case_ids: str | None = None
    created_on: datetime | None = None
    created_by: int | None = None

class TestSuiteUpdate(BaseModel):
    site_id: int | None = None
    title: str | None = Field(default=None, max_length=200)
    scenario_count: int | None = None
    test_case_count: int | None = None
    # test_scenario_ids: str | None = None
    # test_case_ids: str | None = None

class TestSuiteOut(TestSuiteBase):
    id: int
    created_on: datetime | None = None
    created_by: int | None = None
