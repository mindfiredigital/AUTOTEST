from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import JSON
from app.db.base import Base
# from app.models.page import Page

# Enums per XLSX
ScenarioTypeEnum = Enum("auto-generated", "manual", name="scenario_type")
ScenarioCategoryEnum = Enum(
    "functional",
    "auth-positive",
    "auth-negative",
    "ui-validation",
    "validation",
    "navigation",
    "form",
    name="scenario_category",
)


class TestScenario(Base):
    __tablename__ = "test_scenario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("page.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # scenario details JSON (selectors, steps, etc.)
    type: Mapped[str] = mapped_column(ScenarioTypeEnum, nullable=False, default="auto-generated")
    category: Mapped[str | None] = mapped_column(ScenarioCategoryEnum, nullable=True)
    script: Mapped[str | None] = mapped_column(Text, nullable=True)  # python-selenium content
    script_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    page: Mapped["Page"] = relationship("Page")
    test_cases: Mapped[list["TestCase"]] = relationship(
        "TestCase", back_populates="scenario", cascade="all, delete-orphan"
    )