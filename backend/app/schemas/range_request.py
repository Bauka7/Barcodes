from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RangeRequestCreate(BaseModel):
    client_id: int | None = None
    department_id: int | None = None
    package_type: str
    requested_quantity: int
    request_type: str = "issue_range"
    payload: dict[str, Any] | None = None
    notes: str | None = None


class RangeRequestDecision(BaseModel):
    notes: str | None = None


class RangeRequestRead(BaseModel):
    id: int
    requester_id: int
    client_id: int | None
    department_id: int | None
    package_type: str
    requested_quantity: int
    request_type: str
    payload: dict[str, Any] | None
    status: str
    handled_by: int | None
    handled_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
