from __future__ import annotations
from sqlalchemy import Integer, String, Enum, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime

is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

TestCaseTypeEnum = Enum("auto-generated", "manual")

class TestCase(Base):
    __tablename__ = "test_case"

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

    last_test_execution_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_execution.id", ondelete="SET NULL"),
        nullable=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(TestCaseTypeEnum, nullable=False, default="auto-generated")

    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expected_outcome: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    validation: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_valid_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    # relationships
    page: Mapped["Page"] = relationship("Page", back_populates="test_cases")

    test_scenario: Mapped["TestScenario"] = relationship("TestScenario")

    last_execution: Mapped["TestExecution | None"] = relationship(
        "TestExecution",
        foreign_keys=[last_test_execution_id]
    )

    executions: Mapped[list["TestExecution"]] = relationship(
        "TestExecution",
        back_populates="test_case",
        foreign_keys="TestExecution.test_case_id",
        cascade="all, delete-orphan"
    )

    page_links_source: Mapped[list["PageLinkTestCase"]] = relationship(
        "PageLinkTestCase",
        back_populates="test_case_source",
        foreign_keys="PageLinkTestCase.test_case_id_source"
    )