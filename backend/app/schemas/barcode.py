from datetime import datetime

from pydantic import BaseModel


class BarcodeNumberRequest(BaseModel):
    package_type: str
    quantity: int
    department_id: int | None = None
    generated_by: str | None = None
    notes: str | None = None


class BarcodeNumberResponse(BaseModel):
    batch_id: int
    items: list[str]
    count: int
    first_barcode: str
    last_barcode: str


class GeneratedBatchItem(BaseModel):
    id: int
    package_type: str
    quantity: int
    first_barcode: str
    last_barcode: str
    department_id: int | None
    generated_by: str | None
    source: str | None
    status: str
    generated_at: datetime
    notes: str | None


class GeneratedBarcodeItem(BaseModel):
    id: int
    batch_id: int
    barcode: str
    package_type: str
    department_id: int | None
    sequence_number: int
    printed: bool
    printed_at: datetime | None
    generated_at: datetime


class GeneratedBatchDetail(GeneratedBatchItem):
    barcodes: list[GeneratedBarcodeItem]


class GeneratedBarcodeSearchResponse(GeneratedBarcodeItem):
    batch: GeneratedBatchItem
