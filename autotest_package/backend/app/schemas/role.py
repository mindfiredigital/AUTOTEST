from pydantic import BaseModel, Field

class RoleBase(BaseModel):
    type: str = Field(max_length=30)
    access: dict | None = None

class RoleOut(RoleBase):
    id: int
