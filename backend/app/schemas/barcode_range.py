from datetime import datetime

from pydantic import BaseModel


class BarcodeRangeRead(BaseModel):
    id: int
    package_type: str
    start_number: int
    end_number: int
    current_number: int
    status: str
    issued_to_client_id: int | None
    issued_to_department_id: int | None
    request_id: int | None
    issued_by: int | None
    issued_at: datetime | None
    expires_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
