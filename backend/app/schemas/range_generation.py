from pydantic import BaseModel


class RangeGenerateRequest(BaseModel):
    quantity: int
    notes: str | None = None


class RangeCancelRequest(BaseModel):
    reason: str


class RangeRemainingResponse(BaseModel):
    range_id: int
    remaining: int
    current_number: int
    end_number: int
    status: str
