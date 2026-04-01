"""RabbitMQ consumer worker for the TEST_SUITE_EXECUTION_QUEUE.

Responsibilities
----------------
- Decode incoming queue messages (bytes / str / dict).
- Validate that execution_id and suite_id are present.
- Delegate all business logic to TestSuiteExecutionService.run_suite_execution().
- Handle unexpected errors so the consumer loop never crashes.

This module contains NO business logic — it is purely transport/wiring code.
All orchestration lives in service/test_suite_execution_service.py.

Queue message schema
--------------------
{
    "execution_id": int,   # PK of the TestSuiteExecution row
    "suite_id":     int,   # PK of the TestSuite to run
    "user_id":      int    # ID of the triggering user (for audit columns)
}
"""

import asyncio
import json
from typing import Dict, Optional, Union

from app.config.database import SessionLocal
from app.config.logger import logger
from app.services.test_suite_execution_service import run_suite_execution


class TestSuiteExecutionWorker:
    """
    Async RabbitMQ message handler for TEST_SUITE_EXECUTION_QUEUE.

    process_test_suite_execution() is registered as the queue callback.
    It offloads the synchronous DB + subprocess work to a thread via
    asyncio.to_thread so the event loop is never blocked.
    """

    async def process_test_suite_execution(
        self,
        message: Union[bytes, str, Dict],
    ) -> None:
        """
        Entry point called by the RabbitMQ consumer for each queue message.

        Parameters
        ----------
        message : bytes | str | dict
            Raw queue payload — decoded here before delegating to the service.
        """
        try:
            body = self._decode_message(message)
        except json.JSONDecodeError:
            logger.exception("[SUITE_EXEC_WORKER] Failed to decode message JSON")
            return

        execution_id: Optional[int] = body.get("execution_id")
        suite_id: Optional[int] = body.get("suite_id")
        user_id: int = body.get("user_id", 0)

        if not execution_id or not suite_id:
            logger.error(
                f"[SUITE_EXEC_WORKER] Invalid message — "
                f"execution_id or suite_id missing: {body}"
            )
            return

        logger.info(
            f"[SUITE_EXEC_WORKER] Received | "
            f"execution_id={execution_id}  suite_id={suite_id}  user_id={user_id}"
        )

        await asyncio.to_thread(
            self._run_with_session,
            execution_id,
            suite_id,
            user_id,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _decode_message(message: Union[bytes, str, Dict]) -> Dict:
        """Normalise the raw queue payload to a plain dict."""
        if isinstance(message, (bytes, bytearray)):
            return json.loads(message.decode("utf-8"))
        if isinstance(message, str):
            return json.loads(message)
        return message  # already a dict

    @staticmethod
    def _run_with_session(
        execution_id: int,
        suite_id: int,
        user_id: int,
    ) -> None:
        """
        Open a DB session, delegate to the service, and guarantee cleanup.

        Wraps the service call in a try/except so a fatal error in one
        execution cannot crash the worker process.
        """
        db = SessionLocal()
        try:
            run_suite_execution(
                execution_id=execution_id,
                suite_id=suite_id,
                user_id=user_id,
                db=db,
            )
        except Exception as exc:
            logger.exception(
                f"[SUITE_EXEC_WORKER] Unhandled error for "
                f"execution_id={execution_id}: {exc}"
            )
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

#: Primary singleton — used by the queue router to register the handler.
test_suite_execution_worker = TestSuiteExecutionWorker()

#: Alias kept for backward compatibility with the LLM service queue_router.
worker_test_suite_execution_service = test_suite_execution_worker