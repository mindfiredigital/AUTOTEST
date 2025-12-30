from __future__ import annotations
from sqlalchemy import Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class PageLinkTestCase(Base):
    __tablename__ = "page_link_test_case"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_link_id: Mapped[int] = mapped_column(ForeignKey("page_link.id"), nullable=False, index=True)
    # specific test_case_id that belongs to source page
    test_case_id_source: Mapped[int] = mapped_column(ForeignKey("test_case.id"), nullable=False, index=True)
    # whether redirected URL is correct / redirection is desired
    # verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    page_link: Mapped["PageLink"] = relationship("PageLink", back_populates="test_cases_map")
    test_case_source: Mapped["TestCase"] = relationship("TestCase")
