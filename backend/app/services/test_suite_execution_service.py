"""Service layer for test suite execution.

Handles:
- Syncing flow_definition nodes into test_suite_step rows (BFS order)
- Fetching page_id from test_scenario table via scenario_id
- Creating and managing TestSuiteExecution records
- Listing executions and their steps
"""

from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from shared_orm.models.test_suite import TestSuite
from shared_orm.models.test_suite_step import TestSuiteStep
from shared_orm.models.test_suite_execution import TestSuiteExecution
from shared_orm.models.test_scenario import TestScenario
from shared_orm.models.user import User
from app.config.logger import logger


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _bfs_ordered_nodes(flow_definition: dict) -> list[dict]:
    """Return flow nodes in BFS order starting from the start node."""
    nodes: dict[str, dict] = {n["id"]: n for n in flow_definition.get("nodes", [])}
    edges: list[dict] = flow_definition.get("edges", [])

    adj: dict[str, list[str]] = {}
    for edge in edges:
        adj.setdefault(edge.get("source", ""), []).append(edge.get("target", ""))

    start_node = next(
        (n for n in nodes.values() if n.get("data", {}).get("node_type") == "start"),
        None,
    )

    if not start_node:
        logger.warning("[SUITE_STEPS] No start node found; using insertion order")
        return list(nodes.values())

    visited: set[str] = set()
    ordered: list[dict] = []
    queue: deque[str] = deque([start_node["id"]])

    while queue:
        node_id = queue.popleft()
        if node_id in visited or node_id not in nodes:
            continue
        visited.add(node_id)
        ordered.append(nodes[node_id])
        for neighbor in adj.get(node_id, []):
            if neighbor not in visited:
                queue.append(neighbor)

    # include any disconnected nodes
    for nid, node in nodes.items():
        if nid not in visited:
            ordered.append(node)

    return ordered


def _normalise_site_attributes(site_attributes: list[dict]) -> dict | None:
    """Store site_attributes in the canonical format.

    Accepts both formats produced by the frontend:
      - flow_definition format: {"site_attribute_key": ..., "site_attribute_value": ...}
      - builder state format:   {"key": ..., "value": ...}
    """
    if not site_attributes:
        return None

    normalised = []
    for attr in site_attributes:
        key = attr.get("site_attribute_key") or attr.get("key", "")
        val = attr.get("site_attribute_value") or attr.get("value", "")
        if key:
            normalised.append({"site_attribute_key": key, "site_attribute_value": val})

    return {"site_attributes": normalised} if normalised else None


def _fetch_scenario_page_map(scenario_ids: list[int], db: Session) -> dict[int, int]:
    """Batch-fetch page_id for each scenario_id in one query."""
    if not scenario_ids:
        return {}
    rows = (
        db.query(TestScenario.id, TestScenario.page_id)
        .filter(TestScenario.id.in_(scenario_ids))
        .all()
    )
    return {row.id: row.page_id for row in rows}


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class TestSuiteExecutionService:

    # -----------------------------------------------------------------------
    # SYNC STEPS
    # -----------------------------------------------------------------------

    def sync_steps(self, suite: TestSuite, db: Session, user: User) -> list[TestSuiteStep]:
        """Parse flow_definition and rebuild test_suite_step rows in BFS order.

        - Deletes all existing steps for the suite first.
        - Only scenario (step / suite_ref) nodes are persisted; flow-control
          nodes (start, end, branch) are skipped.
        - page_id is resolved from the test_scenario table using scenario_id.
        """
        logger.info(f"[SUITE_STEPS_SYNC] suite_id={suite.id} by={user.id}")

        # Remove stale steps
        deleted = (
            db.query(TestSuiteStep)
            .filter(TestSuiteStep.test_suite_id == suite.id)
            .delete(synchronize_session=False)
        )
        if deleted:
            logger.info(f"[SUITE_STEPS_SYNC] Removed {deleted} stale steps for suite_id={suite.id}")

        flow: dict = suite.flow_definition or {"nodes": [], "edges": []}
        ordered_nodes = _bfs_ordered_nodes(flow)

        # Collect all scenario IDs from step nodes for a single batch query
        scenario_ids = [
            int(n["data"]["scenario_id"])
            for n in ordered_nodes
            if n.get("data", {}).get("node_type") == "step"
            and n["data"].get("scenario_id") is not None
        ]
        scenario_page_map = _fetch_scenario_page_map(scenario_ids, db)
        logger.info(
            f"[SUITE_STEPS_SYNC] Resolved page_id for {len(scenario_page_map)} scenarios "
            f"in suite_id={suite.id}"
        )

        steps: list[TestSuiteStep] = []
        now = datetime.now(timezone.utc)
        step_order = 0

        for node in ordered_nodes:
            data: dict[str, Any] = node.get("data", {})
            node_type: str = data.get("node_type") or node.get("type", "unknown")

            # Only persist runnable nodes
            if node_type not in {"step", "suite_ref"}:
                continue

            scenario_id: int | None = data.get("scenario_id")

            if node_type == "step":
                if not scenario_id:
                    logger.warning(
                        f"[SUITE_STEPS_SYNC] Skipping step node with no scenario_id "
                        f"in suite_id={suite.id}"
                    )
                    continue

                page_id: int | None = scenario_page_map.get(int(scenario_id))
                if not page_id:
                    logger.warning(
                        f"[SUITE_STEPS_SYNC] Skipping scenario_id={scenario_id} — "
                        f"scenario not found in DB (suite_id={suite.id})"
                    )
                    continue
            else:
                # suite_ref nodes don't have a page_id
                page_id = None

            step_order += 1
            label: str = data.get("label", "")
            site_attributes: list[dict] = data.get("site_attributes") or []

            # Serialize test_case_ids as comma-separated string e.g. "2245, 2246, 2247"
            raw_tc_ids: list = data.get("test_case_ids") or []
            test_case_ids_str: str | None = (
                ", ".join(str(tc_id) for tc_id in raw_tc_ids) if raw_tc_ids else None
            )

            step = TestSuiteStep(
                test_suite_id=suite.id,
                step_number=step_order,
                step_order=step_order,
                node_type=node_type,
                node_id=step_order,
                label=label[:200] if label else None,
                page_id=page_id,
                scenario_id=scenario_id,
                test_suite_step_attribute=_normalise_site_attributes(site_attributes),
                test_case_ids=test_case_ids_str,
                created_on=now,
                created_by=user.id,
            )
            db.add(step)
            steps.append(step)

        db.flush()
        logger.info(
            f"[SUITE_STEPS_SYNC] Inserted {len(steps)} steps for suite_id={suite.id} "
            f"(skipped {len(ordered_nodes) - len(steps)} flow-control nodes)"
        )
        return steps

    # -----------------------------------------------------------------------
    # CREATE EXECUTION
    # -----------------------------------------------------------------------

    def create_execution(
        self, suite_id: int, db: Session, user: User
    ) -> TestSuiteExecution:
        """Sync steps, create execution record, and set suite status to 'running'."""
        suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")

        logger.info(f"[SUITE_EXECUTION_CREATE] suite_id={suite_id} triggered by user={user.id}")
        existing_executions = (
            db.query(TestSuiteExecution)
            .filter(TestSuiteExecution.test_suite_id == suite_id)
            .all()
        )

        if existing_executions:
            logger.info(f"[DELETE_EXISTING_EXECUTIONS] count={len(existing_executions)} for suite_id={suite_id}")

            for exec in existing_executions:
                db.delete(exec)

            db.flush()
            
        # 1. Sync steps from current flow_definition
        steps = self.sync_steps(suite, db, user)

        now = datetime.now(timezone.utc)

        # 2. Create execution record
        execution = TestSuiteExecution(
            test_suite_id=suite_id,
            status="running",
            started_at=now,
            ended_at=None,
            execution_summary={
                "total": len(steps),
                "passed": 0,
                "failed": 0,
                "skipped": 0,
            },
            executed_by=user.id,
            created_on=now,
            created_by=user.id,
            updated_on=now,
            updated_by=user.id,
        )
        db.add(execution)

        # 3. Mark the suite itself as running
        suite.status = "running"
        suite.updated_on = now
        suite.updated_by = user.id

        db.commit()
        db.refresh(execution)

        logger.info(
            f"[SUITE_EXECUTION_CREATED] execution_id={execution.id} suite_id={suite_id} "
            f"steps={len(steps)} status=running"
        )
        logger.info(f"[SUITE_STATUS_UPDATED] suite_id={suite_id} status=running")
        return execution

    # -----------------------------------------------------------------------
    # LIST EXECUTIONS
    # -----------------------------------------------------------------------

    def list_executions(
        self,
        suite_id: int,
        db: Session,
        user: User,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[int, list[TestSuiteExecution]]:
        """Return paginated executions for a suite, newest first."""
        if not db.query(TestSuite).filter(TestSuite.id == suite_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")

        query = db.query(TestSuiteExecution).filter(TestSuiteExecution.test_suite_id == suite_id)
        total = query.count()
        items = (
            query.order_by(TestSuiteExecution.created_on.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return total, items

    # -----------------------------------------------------------------------
    # GET EXECUTION
    # -----------------------------------------------------------------------

    def get_execution(self, execution_id: int, db: Session, user: User) -> TestSuiteExecution:
        execution = db.query(TestSuiteExecution).filter(TestSuiteExecution.id == execution_id).first()
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found",
            )
        return execution

    # -----------------------------------------------------------------------
    # GET LATEST EXECUTION RESULT
    # -----------------------------------------------------------------------

    def get_latest_execution(self, suite_id: int, db: Session, user: User) -> TestSuiteExecution:
        """Return the most recent execution (with logs + summary) for a suite."""
        if not db.query(TestSuite).filter(TestSuite.id == suite_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")

        execution = (
            db.query(TestSuiteExecution)
            .filter(TestSuiteExecution.test_suite_id == suite_id)
            .order_by(TestSuiteExecution.created_on.desc())
            .first()
        )
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No execution found for this test suite",
            )
        return execution

    # -----------------------------------------------------------------------
    # LIST STEPS
    # -----------------------------------------------------------------------

    def list_steps(
        self,
        suite_id: int,
        db: Session,
        user: User,
    ) -> tuple[int, list[TestSuiteStep]]:
        """Return all steps for a suite ordered by step_order."""
        if not db.query(TestSuite).filter(TestSuite.id == suite_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")

        items = (
            db.query(TestSuiteStep)
            .filter(TestSuiteStep.test_suite_id == suite_id)
            .order_by(TestSuiteStep.step_order)
            .all()
        )
        return len(items), items

    # -----------------------------------------------------------------------
    # UPDATE EXECUTION STATUS
    # -----------------------------------------------------------------------

    def update_execution_status(
        self,
        execution_id: int,
        new_status: str,
        db: Session,
        user: User,
        execution_summary: dict | None = None,
        ended_at: datetime | None = None,
    ) -> TestSuiteExecution:
        """Update status (and optionally summary / ended_at) of an execution."""
        valid_statuses = {"pending", "running", "passed", "partially_passed", "failed", "error"}
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status '{new_status}'. Must be one of: {sorted(valid_statuses)}",
            )

        execution = self.get_execution(execution_id, db, user)
        execution.status = new_status
        execution.updated_on = datetime.now(timezone.utc)
        execution.updated_by = user.id

        if execution_summary is not None:
            execution.execution_summary = execution_summary
        if ended_at is not None:
            execution.ended_at = ended_at

        db.commit()
        db.refresh(execution)

        logger.info(
            f"[SUITE_EXECUTION_STATUS_UPDATED] execution_id={execution_id} "
            f"status={new_status} by={user.id}"
        )
        return execution
