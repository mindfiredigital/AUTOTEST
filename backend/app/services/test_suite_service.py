from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from shared_orm.models.test_suite import TestSuite
from shared_orm.models.test_suite_step import TestSuiteStep
from shared_orm.models.test_suite_execution import TestSuiteExecution
from shared_orm.models.site import Site
from shared_orm.models.user import User
from app.config.logger import logger
from app.services.test_suite_execution_service import TestSuiteExecutionService


class TestSuiteService:

    # ─────────────────────────────────────────
    # LIST
    # ─────────────────────────────────────────
    def list_test_suites(
        self,
        db: Session,
        site_id: int,
        page: int,
        limit: int,
        user: User,
    ) -> tuple[int, list[TestSuite]]:
        query = db.query(TestSuite).filter(TestSuite.site_id == site_id)
        total = query.count()
        items = query.order_by(TestSuite.created_on.desc()).offset((page - 1) * limit).limit(limit).all()
        return total, items

    # ─────────────────────────────────────────
    # CREATE
    # ─────────────────────────────────────────
    def create_test_suite(
        self,
        db: Session,
        payload: dict,
        user: User,
    ) -> TestSuite:
        site = db.query(Site).filter(Site.id == payload["site_id"]).first()
        if not site:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

        now = datetime.now(timezone.utc)
        suite = TestSuite(
            site_id=payload["site_id"],
            title=payload["title"],
            description=payload.get("description"),
            status=payload.get("status", "draft"),
            flow_definition=payload.get("flow_definition", {"nodes": [], "edges": []}),
            scenario_count=payload.get("scenario_count"),
            test_case_count=payload.get("test_case_count"),
            created_on=now,
            created_by=user.id,
            updated_on=now,
            updated_by=user.id,
        )
        db.add(suite)
        db.commit()
        db.refresh(suite)
        logger.info(f"[TEST_SUITE_CREATED] id={suite.id} site_id={site.id} by={user.id}")
        return suite

    # ─────────────────────────────────────────
    # GET BY ID
    # ─────────────────────────────────────────
    def get_test_suite(self, db: Session, suite_id: int, user: User) -> TestSuite:
        suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")
        return suite

    # ─────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────
    def update_test_suite(
        self,
        db: Session,
        suite_id: int,
        payload: dict,
        user: User,
    ) -> TestSuite:
        suite = self.get_test_suite(db, suite_id, user)

        for field in ("title", "description", "status", "flow_definition", "scenario_count", "test_case_count"):
            if field in payload:
                setattr(suite, field, payload[field])

        suite.updated_on = datetime.now(timezone.utc)
        suite.updated_by = user.id

        # Rebuild test_suite_step rows to reflect the updated flow_definition
        if "flow_definition" in payload:
            TestSuiteExecutionService().sync_steps(suite, db, user)

        db.commit()
        db.refresh(suite)
        logger.info(f"[TEST_SUITE_UPDATED] id={suite_id} by={user.id}")
        return suite

    # ─────────────────────────────────────────
    # DELETE
    # ─────────────────────────────────────────
    def delete_test_suite(self, db: Session, suite_id: int, user: User) -> None:
        suite = self.get_test_suite(db, suite_id, user)

        db.query(TestSuiteStep).filter(
            TestSuiteStep.test_suite_id == suite_id
        ).delete(synchronize_session=False)

        db.query(TestSuiteExecution).filter(
           TestSuiteExecution.test_suite_id == suite_id
        ).delete(synchronize_session=False)

        db.delete(suite)
        db.commit()
        logger.info(f"[TEST_SUITE_DELETED] id={suite_id} by={user.id}")
