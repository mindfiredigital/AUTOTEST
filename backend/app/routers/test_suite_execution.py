"""Router for test suite execution endpoints.

Endpoints:
  POST   /test-suites/{suite_id}/execute               - Trigger execution
  GET    /test-suites/{suite_id}/executions            - List executions for a suite
  GET    /test-suites/{suite_id}/steps                 - List synced steps for a suite
  GET    /test-suites/executions/{execution_id}        - Get a single execution
  PATCH  /test-suites/executions/{execution_id}/status - Update execution status
"""

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.setting import settings
from app.middleware.auth_middleware import auth_required
from app.messaging.rabbitmq_producer import rabbitmq_producer
from shared_orm.models.user import User
from app.services.test_suite_execution_service import TestSuiteExecutionService
from app.schemas.test_suite_execution import (
    TestSuiteExecutionResponse,
    TestSuiteExecutionListResponse,
    TestSuiteExecutionStatusUpdate,
)
from app.schemas.test_suite_step import TestSuiteStepListResponse
from app.config.logger import logger

router = APIRouter(prefix="/test-suites", tags=["Test Suite Execution"])
execution_service = TestSuiteExecutionService()


@router.post(
    "/{suite_id}/execute",
    response_model=TestSuiteExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger test suite execution",
)
async def execute_test_suite(
    suite_id: int = Path(..., description="ID of the test suite to execute"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    # 1. Sync steps + create execution record (synchronous DB work)
    execution = execution_service.create_execution(
        suite_id=suite_id, db=db, user=current_user
    )

    # 2. Publish execution task to worker queue
    published = await rabbitmq_producer.publish_message(
        queue_name=settings.TEST_SUITE_EXECUTION_QUEUE,
        message={
            "execution_id": execution.id,
            "suite_id": suite_id,
            "user_id": current_user.id,
        },
    )

    if not published:
        logger.error(
            f"[SUITE_EXEC_ROUTER] Failed to publish to {settings.TEST_SUITE_EXECUTION_QUEUE} "
            f"for execution_id={execution.id}"
        )

    return execution


@router.get(
    "/{suite_id}/execution-result",
    response_model=TestSuiteExecutionResponse,
    summary="Get the latest execution result (summary + logs) for a test suite",
)
def get_execution_result(
    suite_id: int = Path(..., description="ID of the test suite"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    return execution_service.get_latest_execution(suite_id=suite_id, db=db, user=current_user)


@router.get(
    "/{suite_id}/executions",
    response_model=TestSuiteExecutionListResponse,
    summary="List executions for a test suite",
)
def list_executions(
    suite_id: int = Path(...),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    total, items = execution_service.list_executions(
        suite_id=suite_id, db=db, user=current_user, page=page, limit=limit
    )
    return {"items": items, "total": total}


@router.get(
    "/{suite_id}/steps",
    response_model=TestSuiteStepListResponse,
    summary="List synced steps for a test suite",
)
def list_steps(
    suite_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    total, items = execution_service.list_steps(
        suite_id=suite_id, db=db, user=current_user
    )
    return {"items": items, "total": total}


@router.get(
    "/executions/{execution_id}",
    response_model=TestSuiteExecutionResponse,
    summary="Get a single test suite execution",
)
def get_execution(
    execution_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    return execution_service.get_execution(
        execution_id=execution_id, db=db, user=current_user
    )


@router.patch(
    "/executions/{execution_id}/status",
    response_model=TestSuiteExecutionResponse,
    summary="Update execution status",
)
def update_execution_status(
    payload: TestSuiteExecutionStatusUpdate,
    execution_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    return execution_service.update_execution_status(
        execution_id=execution_id,
        new_status=payload.status,
        db=db,
        user=current_user,
        execution_summary=payload.execution_summary,
        ended_at=payload.ended_at,
    )
