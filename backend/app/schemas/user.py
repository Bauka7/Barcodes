from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str | None = None
    email: str | None = None
    full_name: str | None = None
    role: str
    department_id: int | None = None
    client_id: int | None = None
    is_active: bool = True


class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    role: str | None = None
    department_id: int | None = None
    client_id: int | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    id: int
    username: str
    email: str | None
    full_name: str | None
    role: str
    department_id: int | None
    client_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
