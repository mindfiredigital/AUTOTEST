from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime


class TestSuiteExecutionCreate(BaseModel):
    test_suite_id: int
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    execution_summary: Optional[Dict[str, Any]] = None
    executed_by: Optional[int] = None


class TestSuiteExecutionUpdate(BaseModel):
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    execution_summary: Optional[Dict[str, Any]] = None
    executed_by: Optional[int] = None


class TestSuiteExecutionDelete(BaseModel):
    id: int


class TestSuiteExecutionResponse(BaseModel):
    id: int
    test_suite_id: int
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    execution_summary: Optional[Dict[str, Any]] = None
    executed_by: Optional[int] = None
    created_on: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_on: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


class TestSuiteExecutionListResponse(BaseModel):
    items: List[TestSuiteExecutionResponse]
    total: int


class TestSuiteExecutionStatusUpdate(BaseModel):
    status: str
    execution_summary: Optional[Dict[str, Any]] = None
    ended_at: Optional[datetime] = None
