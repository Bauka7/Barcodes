from datetime import datetime

from pydantic import BaseModel


class PrintBatchRequest(BaseModel):
    printed_by: str | None = None
    printer_name: str | None = None
    notes: str | None = None


class PrintedBatchItem(BaseModel):
    id: int
    generated_batch_id: int
    department_id: int | None
    printed_count: int
    first_barcode: str
    last_barcode: str
    printed_by: str | None
    printer_name: str | None
    status: str
    printed_at: datetime
    notes: str | None
