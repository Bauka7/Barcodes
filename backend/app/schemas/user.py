from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str | None = None
    email: str | None = None
    phone: str | None = None
    full_name: str | None = None
    role: str
    department_id: int | None = None
    client_id: int | None = None
    is_active: bool = True


class UserUpdate(BaseModel):
    email: str | None = None
    phone: str | None = None
    full_name: str | None = None
    role: str | None = None
    department_id: int | None = None
    client_id: int | None = None
    is_active: bool | None = None


class UserDepartmentRead(BaseModel):
    id: int
    code: str
    name: str
    region: str | None
    department_type: str | None
    full_path: str | None


class UserModeratorRead(BaseModel):
    id: int
    username: str
    full_name: str | None
    email: str | None
    phone: str | None
    role: str


class UserRead(BaseModel):
    id: int
    username: str
    email: str | None
    phone: str | None
    full_name: str | None
    role: str
    role_label: str
    department_id: int | None
    client_id: int | None
    is_active: bool
    department: UserDepartmentRead | None = None
    moderator: UserModeratorRead | None = None
    created_at: datetime
    updated_at: datetime
