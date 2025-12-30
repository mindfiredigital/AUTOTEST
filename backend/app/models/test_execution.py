from __future__ import annotations
from xmlrpc.client import Boolean
# from backend.app.models.page import Page
# from backend.app.models.test_scenario import TestScenario
from sqlalchemy import Integer, String, Enum, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime

TestExecutionStatusEnum = Enum("NOne", "Passed", "Partially Passed", "Failed")

class TestExecution(Base):
    __tablename__ = "test_execution"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    page_id: Mapped[int] = mapped_column(
        ForeignKey("page.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    test_scenario_id: Mapped[int] = mapped_column(
        ForeignKey("test_scenario.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    test_case_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_case.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    test_suite_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_suite.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    status: Mapped[str | None] = mapped_column(TestExecutionStatusEnum, nullable=True)

    logs: Mapped[str | None] = mapped_column(Text, nullable=True)

    executed_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    executed_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    # relationships
    page: Mapped["Page"] = relationship("Page")
    test_scenario: Mapped["TestScenario"] = relationship("TestScenario")

    test_case: Mapped["TestCase | None"] = relationship(
        "TestCase",
        back_populates="executions",
        foreign_keys=[test_case_id]
    )

    test_suite: Mapped["TestSuite | None"] = relationship("TestSuite")
