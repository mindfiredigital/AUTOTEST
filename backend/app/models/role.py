from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import JSON
from app.db.base import Base

class Role(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    access: Mapped[dict | None] = mapped_column(JSON, nullable=True)
