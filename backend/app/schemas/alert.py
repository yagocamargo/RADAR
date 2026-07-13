import uuid
from datetime import datetime
from pydantic import BaseModel


class AlertOut(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    type: str
    priority: str
    status: str
    company_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    items: list[AlertOut]
    unread_count: int
