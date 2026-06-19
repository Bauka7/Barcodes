from datetime import datetime

from pydantic import BaseModel, Field, field_validator


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


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None

        normalized = value.strip()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("email must be a valid email address.")
        return normalized

    @field_validator("full_name", "phone")
    @classmethod
    def normalize_empty_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


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


class UserScopeRead(BaseModel):
    type: str
    label: str


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
    scope: UserScopeRead
    created_at: datetime
    updated_at: datetime
