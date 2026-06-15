from datetime import datetime

from pydantic import BaseModel, Field


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
    range_id: int | None = None
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
    range_id: int | None = None
    sequence_number: int
    printed: bool
    printed_at: datetime | None
    generated_by: str | None = None
    printed_by: str | None = None
    status: str = Field(
        default="generated",
        description="MVP statuses: generated or printed. Legacy rows may contain older values.",
    )
    cancelled_at: datetime | None = None
    cancelled_by: str | None = None
    cancellation_reason: str | None = None
    used_at: datetime | None = None
    used_by: str | None = None
    usage_notes: str | None = None
    generated_at: datetime


class GeneratedBatchDetail(GeneratedBatchItem):
    barcodes: list[GeneratedBarcodeItem]


class GeneratedBarcodeSearchResponse(GeneratedBarcodeItem):
    batch: GeneratedBatchItem


class BarcodeDepartmentInfo(BaseModel):
    id: int
    code: str
    name: str
    region: str


class BarcodeRangeInfo(BaseModel):
    id: int
    package_type: str
    start_number: int
    end_number: int
    current_number: int
    status: str


class BarcodeDetailResponse(GeneratedBarcodeItem):
    batch: GeneratedBatchItem
    range: BarcodeRangeInfo | None = None
    department: BarcodeDepartmentInfo | None = None


class BarcodeLifecycleListResponse(BaseModel):
    items: list[GeneratedBarcodeItem]
    count: int
