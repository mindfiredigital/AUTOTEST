from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
# from app.models.site import Site

class SiteAlias(Base):
    __tablename__ = "site_alias"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id"), nullable=False, index=True)
    site_alias_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    site_alias_url: Mapped[str] = mapped_column(String(255), nullable=False)

    site: Mapped["Site"] = relationship("Site", back_populates="aliases")
