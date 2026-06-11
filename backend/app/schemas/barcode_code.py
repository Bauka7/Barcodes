from datetime import datetime

from pydantic import BaseModel


class BarcodeCodeRead(BaseModel):
    id: int
    code: str
    name: str | None
    category: str | None
    status: str
    owner: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
