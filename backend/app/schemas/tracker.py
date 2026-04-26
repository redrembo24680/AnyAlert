from datetime import datetime
from pydantic import BaseModel, ConfigDict

class TrackerBase(BaseModel):
    url: str
    network: str
    trigger_type: str
    trigger_value: float | None = None

class TrackerCreate(TrackerBase):
    pass

class TrackerResponse(TrackerBase):
    id: int
    user_id: int
    title: str | None = None
    last_price: float | None = None
    last_status: str | None = None
    last_checked_at: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class TrackerUpdate(BaseModel):
    title: str | None = None
    last_price: float | None = None
    last_status: str | None = None
    last_checked_at: datetime | None = None
