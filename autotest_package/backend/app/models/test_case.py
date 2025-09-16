from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import JSON
from app.db.base import Base

TestCaseTypeEnum = Enum("auto-generated", "manual", name="test_case_type")

class TestCase(Base):
    __tablename__ = "test_case"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("page.id"), nullable=False, index=True)
    test_scenario_id: Mapped[int] = mapped_column(ForeignKey("test_scenario.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=True)  # optional human-friendly tag or title
    # NEW: last test execution id (tracks last execution; can be NULL)
    last_test_execution_id: Mapped[int | None] = mapped_column(ForeignKey("test_execution.id"), nullable=True, index=True)

    type: Mapped[str] = mapped_column(TestCaseTypeEnum, nullable=False, default="auto-generated")
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # per-case data (inputs, variants)
    expected_outcome: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    validation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # is_valid_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_valid_default: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=False)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    page: Mapped["Page"] = relationship("Page")
    scenario: Mapped["TestScenario"] = relationship("TestScenario", back_populates="test_cases")
    # last_execution: Mapped["TestExecution | None"] = relationship("TestExecution", foreign_keys=[last_test_execution_id])

    # Disambiguate: this relationship uses last_test_execution_id -> test_execution.id
    last_execution: Mapped["TestExecution | None"] = relationship(
        "TestExecution",
        foreign_keys="[TestCase.last_test_execution_id]",
    )

    # Optional: if you want a collection of all executions for a case:
    executions: Mapped[list["TestExecution"]] = relationship(
        "TestExecution",
        foreign_keys="[TestExecution.test_case_id]",
        back_populates="case",
        cascade="all, delete-orphan",
        passive_deletes=False,
    )

