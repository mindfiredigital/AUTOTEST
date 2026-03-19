from pydantic import BaseModel
from datetime import datetime

class ProviderResponse(BaseModel):
    id: int
    title: str
    is_active: bool
    created_on: datetime | None

    class Config:
        from_attributes = True   # VERY IMPORTANT for ORM

class ProviderBulkUpdate(BaseModel):
    provider_id: int
    key: str | None = None
    is_active: bool


class ActiveProviderResponse(BaseModel):
    providerId: int
    providerTitle: str
    
class ProviderModelMinimalResponse(BaseModel):
    providerModelId: int
    model: str
