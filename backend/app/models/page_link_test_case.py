from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.page import Page


class PageLinkTestCase(Base):
    __tablename__ = "page_link_test_case"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_link_id: Mapped[int] = mapped_column(ForeignKey("page_link.id", ondelete="CASCADE"), nullable=False, index=True)
    test_case_id_source: Mapped[int | None] = mapped_column(ForeignKey("test_case.id", ondelete="SET NULL"), nullable=True, index=True)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # relationships
    page_link: Mapped["PageLink"] = relationship(
        "PageLink",
        back_populates="test_cases"
    )

    test_case_source: Mapped["TestCase"] = relationship(
        "TestCase",
        back_populates="page_links_source",
        foreign_keys=[test_case_id_source]
    )