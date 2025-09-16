from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import JSON
from app.db.base import Base
# from app.models.site import Site

# The XLSX shows a pipeline-like status. Use representative states as enum members.
PageStatusEnum = Enum("new", "generating_metadata", "generating_test_scenarios", "generating_test_cases", "test_cases_generated", "generating_test_scripts", "done", name="page_status")

class Page(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Optional foreign key to Site
    site_id: Mapped[int | None] = mapped_column(ForeignKey("site.id"), nullable=True, index=True)
    page_url: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(PageStatusEnum, nullable=False, default="new")
    page_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    page_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # JSON with authentication/forms/etc.
    created_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    site: Mapped["Site | None"] = relationship("Site", back_populates="pages")
