from __future__ import annotations  # enables forward-referenced type hints
from datetime import datetime
from sqlalchemy import Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
# from app.models.page import Page
# from app.models.site_alias import SiteAlias

# MySQL ENUM values from the XLSX: New | Processing | Pause | Done
SiteStatusEnum = Enum("New", "Processing", "Pause", "Done", name="site_status")

class Site(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_title: Mapped[str] = mapped_column(String(200), nullable=False)
    site_url: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(SiteStatusEnum, nullable=False, default="New")
    created_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    # relationships
    aliases: Mapped[list["SiteAlias"]] = relationship("SiteAlias", 
                 back_populates="site" ,
    cascade="all, delete-orphan")
    pages: Mapped[list["Page"]] = relationship("Page", back_populates="site")