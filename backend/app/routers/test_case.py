from fastapi import APIRouter, Depends, Path, status, Response
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.middleware.auth_middleware import auth_required
from shared_orm.models.user import User
from app.services.test_case_service import TestCaseService
from app.schemas.test_case_schema import (
    TestCaseDetailResponse,
    UpdateTestCaseRequest,
    TestCaseResponse, CreateTestCaseRequest
)

router = APIRouter(prefix="/test-cases", tags=["Test Cases"])

test_case_service = TestCaseService()

# -----------------------------------
# Create Test Case
# -----------------------------------
@router.post(
    "",
    response_model=TestCaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create test case"
)
def create_test_case(
    payload: CreateTestCaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    """
    Create a new test case under a given test scenario.
    Automatically derives page_id from scenario.
    """
    return test_case_service.create_test_case(
        db=db,
        test_scenario_id=payload.test_scenario_id,
        payload=payload.model_dump(exclude_unset=True),
        user=current_user
    )


# -----------------------------------------
# Get Test Case By ID
# -----------------------------------------
@router.get(
    "/{test_case_id}",
    response_model=TestCaseDetailResponse,
    summary="Get test case details",
)
def get_test_case(
    test_case_id: int = Path(..., description="ID of the test case"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    """
    Retrieve detailed information of a test case by its ID.
    """

    test_case = test_case_service.get_test_case_by_id(
        db=db,
        test_case_id=test_case_id,
    )

    return test_case


# -----------------------------------------
# Update Test Case
# -----------------------------------------
@router.patch(
    "/{test_case_id}",
    response_model=TestCaseDetailResponse,
    summary="Update test case",
)
def update_test_case(
    payload: UpdateTestCaseRequest,
    test_case_id: int = Path(..., description="ID of the test case"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    """
    Partially update allowed fields of a test case.

    Allowed fields:
    - title
    - type
    - data
    - expected_outcome
    - validation
    - is_valid
    - is_valid_default
    """

    updated_test_case = test_case_service.update_test_case(
        db=db,
        test_case_id=test_case_id,
        payload=payload.model_dump(exclude_unset=True),
        user=current_user,
    )

    return updated_test_case
@router.delete(
    "/{test_case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete test case",
)
def delete_test_case(
    test_case_id: int = Path(..., description="ID of the test case"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    """
    Permanently delete a test case.
    """

    test_case_service.delete_test_case(
        db=db,
        test_case_id=test_case_id,
        user=current_user,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

