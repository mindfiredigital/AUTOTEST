from datetime import datetime
from pydantic import BaseModel

class TestExecutionBase(BaseModel):
    page_id: int
    test_scenario_id: int
    test_case_id: int | None = None
    test_suite_id: int | None = None
    status: str = "None"   # None | Passed | Partially Passed | Failed
    logs: str | None = None
    executed_on: datetime | None = None
    executed_by: int | None = None

class TestExecutionCreate(BaseModel):
    page_id: int
    test_scenario_id: int
    test_case_id: int | None = None
    test_suite_id: int | None = None
    status: str | None = None
    logs: str | None = None
    executed_on: datetime | None = None
    executed_by: int | None = None

class TestExecutionUpdate(BaseModel):
    page_id: int | None = None
    test_scenario_id: int | None = None
    test_case_id: int | None = None
    test_suite_id: int | None = None
    status: str | None = None
    logs: str | None = None
    executed_on: datetime | None = None
    executed_by: int | None = None

class TestExecutionOut(TestExecutionBase):
    id: int
