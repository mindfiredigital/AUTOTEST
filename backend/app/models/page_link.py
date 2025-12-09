from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.page import Page
# from app.models.test_scenario import TestScenario


class PageLink(Base):
    __tablename__ = "page_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # page_id of source page where navigation/redirection was initiated
    page_id_source: Mapped[int] = mapped_column(ForeignKey("page.id"), nullable=False, index=True)
    # from the test scenario it redirects/navigates to (source scenario)
    # test_scenario_id_source: Mapped[int | None] = mapped_column(ForeignKey("test_scenario.id"), nullable=True, index=True)
    test_scenario_id_source: Mapped[int] = mapped_column(ForeignKey("test_scenario.id"), nullable=False, index=True)
    # target page id; create the page record if it does not exist (same site/domain logic handled in app layer)
    page_id_target: Mapped[int] = mapped_column(ForeignKey("page.id"), nullable=False, index=True)
    # CSS selector that triggered the event
    event_selector: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Brief step-by-step description of how redirection occurred
    event_description: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # relationships (optional backrefs, not strictly required)
    source_page: Mapped["Page"] = relationship("Page", foreign_keys=[page_id_source])
    target_page: Mapped["Page"] = relationship("Page", foreign_keys=[page_id_target])
    source_scenario: Mapped["TestScenario | None"] = relationship("TestScenario", foreign_keys=[test_scenario_id_source])

    test_cases_map: Mapped[list["PageLinkTestCase"]] = relationship(
        "PageLinkTestCase", back_populates="page_link", cascade="all, delete-orphan"
    )