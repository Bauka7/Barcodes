from datetime import datetime

from pydantic import BaseModel


class RangeGenerateRequest(BaseModel):
    quantity: int
    notes: str | None = None


class RangeCancelRequest(BaseModel):
    reason: str


class RangeRenewRequest(BaseModel):
    # Новый срок действия диапазона (должен быть в будущем).
    expires_at: datetime


class RangeRemainingResponse(BaseModel):
    range_id: int
    remaining: int
    current_number: int
    end_number: int
    status: str
