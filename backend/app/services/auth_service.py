from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token, hash_password, verify_password
from app.db.database import get_db_session
from app.models import User
from app.schemas import UserCreate, UserUpdate

VALID_ROLES = {"admin", "operator", "client"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def validate_role(role: str) -> str:
    normalized_role = role.strip().lower()

    if normalized_role not in VALID_ROLES:
        raise ValueError("role must be one of: admin, operator, client.")

    return normalized_role


async def get_user_by_username(
    session: AsyncSession,
    username: str,
) -> User | None:
    result = await session.execute(
        select(User).where(User.username == username.strip())
    )
    return result.scalar_one_or_none()


async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(
    session: AsyncSession,
    username: str,
    password: str,
) -> User | None:
    user = await get_user_by_username(session=session, username=username)

    if user is None or not user.is_active:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


async def create_user(
    session: AsyncSession,
    payload: UserCreate,
) -> User:
    username = payload.username.strip()

    if not username:
        raise ValueError("username is required.")

    if len(payload.password) < 6:
        raise ValueError("password must contain at least 6 characters.")

    existing_user = await get_user_by_username(session=session, username=username)
    if existing_user is not None:
        raise ValueError(f"User '{username}' already exists.")

    user = User(
        username=username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=validate_role(payload.role),
        department_id=payload.department_id,
        is_active=payload.is_active,
    )
    session.add(user)
    await session.flush()
    return user


async def update_user(
    user: User,
    payload: UserUpdate,
) -> User:
    updated_fields = payload.model_fields_set

    if "full_name" in updated_fields:
        user.full_name = payload.full_name

    if "role" in updated_fields and payload.role is not None:
        user.role = validate_role(payload.role)

    if "department_id" in updated_fields:
        user.department_id = payload.department_id

    if "is_active" in updated_fields and payload.is_active is not None:
        user.is_active = payload.is_active

    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session, use_cache=False),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
    except JWTError as error:
        raise credentials_exception from error

    if not isinstance(username, str) or not username:
        raise credentials_exception

    user = await get_user_by_username(session=session, username=username)
    if user is None or not user.is_active:
        raise credentials_exception

    return user


def require_roles(*roles: str) -> Callable:
    allowed_roles = {validate_role(role) for role in roles}

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions.",
            )

        return current_user

    return dependency
