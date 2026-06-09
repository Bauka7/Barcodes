from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str | None = None
    role: str
    department_id: int | None = None
    is_active: bool = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    department_id: int | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    id: int
    username: str
    full_name: str | None
    role: str
    department_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
