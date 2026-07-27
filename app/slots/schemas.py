import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict

from app.slots.model import SlotStatus


class SlotCreateSchema(BaseModel):
    provider_id: uuid.UUID
    start_time: datetime
    end_time: datetime


class SlotResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    status: SlotStatus
