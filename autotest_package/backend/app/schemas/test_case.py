from datetime import datetime
from pydantic import BaseModel, Field

class TestCaseBase(BaseModel):
    page_id: int
    test_scenario_id: int
    title: str | None = Field(default=None, max_length=200)
    type: str = "auto-generated"  # auto-generated | manual
    data: dict | None = None
    expected_outcome: dict | None = None
    validation: dict | None = None
    is_valid: bool = True
    is_valid_default: bool = False
    last_test_execution_id: int | None = None

class TestCaseCreate(BaseModel):
    page_id: int
    test_scenario_id: int
    title: str | None = Field(default=None, max_length=200)
    type: str | None = None
    data: dict | None = None
    expected_outcome: dict | None = None
    validation: dict | None = None
    is_valid: bool | None = None
    is_valid_default: bool | None = None
    last_test_execution_id: int | None = None
    created_on: datetime | None = None
    created_by: int | None = None

class TestCaseUpdate(BaseModel):
    page_id: int | None = None
    test_scenario_id: int | None = None
    title: str | None = Field(default=None, max_length=200)
    type: str | None = None
    data: dict | None = None
    expected_outcome: dict | None = None
    validation: dict | None = None
    is_valid: bool | None = None
    is_valid_default: bool | None = None
    last_test_execution_id: int | None = None
    updated_on: datetime | None = None
    updated_by: int | None = None

class TestCaseOut(TestCaseBase):
    id: int
    created_on: datetime | None = None
    created_by: int | None = None
    updated_on: datetime | None = None
    updated_by: int | None = None
