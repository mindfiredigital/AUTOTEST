from datetime import datetime
from pydantic import BaseModel, Field

class SettingBase(BaseModel):
    key: str = Field(max_length=255)
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    type: str  # Text | Number | Date | Dropdown | Radio Button | Checkbox
    possible_values: str | None = Field(default=None, max_length=1000)
    default_value: str | None = Field(default=None, max_length=1000)
    actual_value: str | None = Field(default=None, max_length=1000)

class SettingCreate(BaseModel):
    key: str = Field(max_length=255)
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    type: str
    possible_values: str | None = Field(default=None, max_length=1000)
    default_value: str | None = Field(default=None, max_length=1000)
    actual_value: str | None = Field(default=None, max_length=1000)
    updated_on: datetime | None = None
    updated_by: int | None = None

class SettingUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    type: str | None = None
    possible_values: str | None = Field(default=None, max_length=1000)
    default_value: str | None = Field(default=None, max_length=1000)
    actual_value: str | None = Field(default=None, max_length=1000)
    updated_on: datetime | None = None
    updated_by: int | None = None

class SettingOut(SettingBase):
    id: int
    updated_on: datetime | None = None
    updated_by: int | None = None
