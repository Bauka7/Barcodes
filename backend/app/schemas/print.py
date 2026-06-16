from datetime import datetime

from pydantic import BaseModel, Field


class PrintLayoutSettings(BaseModel):
    offset_left: float = Field(default=0, ge=0)
    offset_top: float = Field(default=0, ge=0)
    gap_x: float = Field(default=0, ge=0)
    gap_y: float = Field(default=0, ge=0)
    rows: int = Field(default=1, ge=1)
    columns: int = Field(default=1, ge=1)


class PrintBatchRequest(BaseModel):
    printed_by: str | None = None
    printer_name: str | None = None
    notes: str | None = None
    print_layout: PrintLayoutSettings | None = None


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
