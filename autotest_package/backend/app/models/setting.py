from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

# XLSX enum: Text, Number, Date, Dropdown, Radio Button, Checkbox
SettingTypeEnum = Enum(
    "Text",
    "Number",
    "Date",
    "Dropdown",
    "Radio Button",
    "Checkbox",
    name="setting_type",
)

class Setting(Base):
    __tablename__ = "setting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    type: Mapped[str] = mapped_column(SettingTypeEnum, nullable=False)

    # The sheet shows varchar; commas or pipes can separate values.
    possible_values: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    default_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    updated_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    updater: Mapped["User | None"] = relationship("User")
