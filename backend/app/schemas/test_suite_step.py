from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime


class TestSuiteStepResponse(BaseModel):
    id: int
    test_suite_id: int
    step_number: int
    step_order: int
    node_type: Optional[str] = None
    node_id: Optional[int] = None
    label: Optional[str] = None
    page_id: Optional[int] = None
    scenario_id: Optional[int] = None
    test_suite_step_attribute: Optional[Dict[str, Any]] = None
    test_case_ids: Optional[str] = None
    created_on: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class TestSuiteStepListResponse(BaseModel):
    items: List[TestSuiteStepResponse]
    total: int
