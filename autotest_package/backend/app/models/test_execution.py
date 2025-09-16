from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

# Status per XLSX: None | Passed | Partially Passed | Failed
# Include "Script Generated" or "Executing" only if desired; the latest XLSX shows final outcome states.
TestExecutionStatusEnum = Enum(
    "None",
    "Passed",
    "Partially Passed",
    "Failed",
    name="test_execution_status",
)

class TestExecution(Base):
    __tablename__ = "test_execution"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("page.id"), nullable=False, index=True)
    test_scenario_id: Mapped[int] = mapped_column(ForeignKey("test_scenario.id"), nullable=False, index=True)
    test_case_id: Mapped[int | None] = mapped_column(ForeignKey("test_case.id"), nullable=True, index=True)  # can be NULL
    test_suite_id: Mapped[int | None] = mapped_column(ForeignKey("test_suite.id"), nullable=True, index=True)  # optional
    status: Mapped[str] = mapped_column(TestExecutionStatusEnum, nullable=False, default="None")
    logs: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    executed_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    page: Mapped["Page"] = relationship("Page")
    scenario: Mapped["TestScenario"] = relationship("TestScenario")
    # case: Mapped["TestCase | None"] = relationship("TestCase")
    # Disambiguate: this relationship uses test_case_id -> test_case.id
    case: Mapped["TestCase | None"] = relationship(
        "TestCase",
        foreign_keys="[TestExecution.test_case_id]",
        back_populates="executions",   # optional; see below
    )
    suite: Mapped["TestSuite | None"] = relationship("TestSuite")
