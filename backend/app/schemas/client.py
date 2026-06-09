from datetime import datetime

from pydantic import BaseModel


class ClientCreate(BaseModel):
    name: str
    contact_person: str | None = None
    contact_phone: str | None = None
    email: str | None = None
    notes: str | None = None
    is_active: bool = True


class ClientUpdate(BaseModel):
    name: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    email: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class ClientRead(BaseModel):
    id: int
    name: str
    contact_person: str | None
    contact_phone: str | None
    email: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
