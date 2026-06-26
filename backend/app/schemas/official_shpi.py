from datetime import datetime

from pydantic import BaseModel


class OfficialShpiConnectionResponse(BaseModel):
    enabled: bool
    ok: bool
    message: str


class OfficialShpiPreviewItem(BaseModel):
    barcode: str
    registered_at: datetime | None = None
    package_type: str
    region_code: str
    sequence_number: int
    check_digit: str
    country: str


class OfficialShpiCounterItem(BaseModel):
    package_type: str
    region_code: str
    current_value: int
    used_count: int
    last_used_date: datetime | None = None


class OfficialShpiSyncResponse(BaseModel):
    total_official_counters: int
    created: int
    updated: int
    unchanged: int
    skipped_invalid_package_type: int
    skipped_invalid_region_code: int
    message: str

