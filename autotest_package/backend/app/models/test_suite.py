from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class TestSuite(Base):
    __tablename__ = "test_suite"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # counts and id lists are stored in dedicated fields per XLSX
    scenario_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    test_case_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    site: Mapped["Site"] = relationship("Site")
