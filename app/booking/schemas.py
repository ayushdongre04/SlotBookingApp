from datetime import datetime
import uuid
from pydantic import BaseModel, EmailStr, Field
from app.booking.model import BookingStatus

class BookingCreate(BaseModel):
    slot_id: uuid.UUID = Field(..., description="The ID of the slot to book")
    customer_name: str = Field(..., description="The name of the customer")
    customer_email: EmailStr = Field(..., description="The email of the customer")


class BookingResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID = Field(..., description="The ID of the booking")
    tenant_id: uuid.UUID = Field(..., description="The ID of the tenant")
    slot_id: uuid.UUID = Field(..., description="The ID of the slot booked")
    customer_name: str = Field(..., description="The name of the customer")
    customer_email: EmailStr = Field(..., description="The email of the customer")
    status: BookingStatus = Field(..., description="The status of the booking")
    created_at: datetime = Field(..., description="The time the booking was created")


