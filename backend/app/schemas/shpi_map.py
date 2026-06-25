from pydantic import BaseModel


class ShpiMapCodeItem(BaseModel):
    code: str
    region_code: str
    current_value: int
    status: str


class ShpiMapRegionItem(BaseModel):
    code: str
    name: str


class ShpiMapResponse(BaseModel):
    regions: list[ShpiMapRegionItem]
    region_codes: list[str]
    codes: list[str]
    cells: list[ShpiMapCodeItem]
