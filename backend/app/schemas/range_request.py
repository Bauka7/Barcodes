from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RangeRequestCreate(BaseModel):
    # Клиент описывает потребность: назначение + количество + отделение-отправитель.
    purpose: str
    requested_quantity: int
    department_id: int
    # Код назначает модератор; клиент может лишь предложить пожелание.
    requested_code: str | None = None
    package_type: str | None = None
    client_id: int | None = None
    request_type: str = "issue_range"
    payload: dict[str, Any] | None = None
    notes: str | None = None


class RangeRequestDecision(BaseModel):
    # approved_code используется при одобрении (модератор назначает код).
    # reject/cancel поле игнорируют.
    approved_code: str | None = None
    notes: str | None = None


class RangeRequestRead(BaseModel):
    id: int
    requester_id: int
    client_id: int | None
    department_id: int | None
    package_type: str | None
    requested_quantity: int
    request_type: str
    purpose: str | None
    requested_code: str | None
    approved_code: str | None
    decision_notes: str | None
    payload: dict[str, Any] | None
    status: str
    handled_by: int | None
    handled_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
