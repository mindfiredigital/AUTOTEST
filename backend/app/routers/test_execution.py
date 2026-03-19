
"""Test execution routes.

Provides endpoints to query test executions, currently by test case.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.services.test_execution_service import TestExecutionService
from app.schemas.test_execution_schema import TestExecutionResponse
from shared_orm.models.user import User
from app.middleware.auth_middleware import auth_required


router = APIRouter(
    prefix="/test-executions",
    tags=["Test Executions"]
)

service = TestExecutionService()


@router.get(
    "/test-case/{test_case_id}",
    response_model=List[TestExecutionResponse]
)
def get_test_executions_by_test_case(
    test_case_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(auth_required)
):
    """Return executions for a given `test_case_id`."""

    return service.get_executions_by_test_case(
        test_case_id=test_case_id,
        db=db,
        user=user
    )