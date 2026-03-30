from __future__ import annotations
from datetime import datetime
from sqlalchemy import JSON, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from shared_orm.db.base import Base


class TestSuiteStep(Base):
    __tablename__ = "test_suite_step"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_suite_id: Mapped[int] = mapped_column(ForeignKey("test_suite.id"), nullable=False, index=True)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    node_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    node_id: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    page_id: Mapped[int | None] = mapped_column(ForeignKey("page.id"), nullable=True)
    scenario_id: Mapped[int | None] = mapped_column(ForeignKey("test_scenario.id"), nullable=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    test_suite_step_attribute: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
