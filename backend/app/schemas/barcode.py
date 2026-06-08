from pydantic import BaseModel


class BarcodeNumberRequest(BaseModel):
    package_type: str
    quantity: int


class BarcodeNumberResponse(BaseModel):
    items: list[str]
    count: int
