from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import decode_access_token, hash_password, verify_password
from app.db.database import get_db_session
from app.models import Client, Department, User
from app.schemas import UserCreate, UserUpdate
from app.services.external_auth_service import (
    ExternalAuthConfigurationError,
    external_auth_is_configured,
    validate_external_token,
)

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


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    result = await session.execute(
        select(User).where(User.email == email.strip())
    )
    return result.scalar_one_or_none()


async def _validate_department_exists(
    session: AsyncSession,
    department_id: int | None,
) -> None:
    if department_id is None:
        return

    result = await session.execute(
        select(Department.id).where(Department.id == department_id)
    )
    if result.scalar_one_or_none() is None:
        raise ValueError(f"Department with id {department_id} was not found.")


async def _validate_active_client_exists(
    session: AsyncSession,
    client_id: int | None,
) -> None:
    if client_id is None:
        return

    result = await session.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if client is None:
        raise ValueError(f"Client with id {client_id} was not found.")

    if not client.is_active:
        raise ValueError(f"Client with id {client_id} is inactive.")


async def _validate_user_references(
    session: AsyncSession,
    role: str,
    client_id: int | None,
    department_id: int | None,
) -> None:
    if role in {"operator", "client"} and department_id is None:
        raise ValueError(f"{role} role requires department_id.")

    await _validate_active_client_exists(session=session, client_id=client_id)
    await _validate_department_exists(session=session, department_id=department_id)


async def authenticate_user(
    session: AsyncSession,
    username: str,
    password: str,
) -> User | None:
    user = await get_user_by_username(session=session, username=username)

    if user is None or not user.is_active:
        return None

    if user.hashed_password is None:
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

    if payload.password is None or len(payload.password) < 6:
        raise ValueError("password must contain at least 6 characters.")

    existing_user = await get_user_by_username(session=session, username=username)
    if existing_user is not None:
        raise ValueError(f"User '{username}' already exists.")

    role = validate_role(payload.role)
    await _validate_user_references(
        session=session,
        role=role,
        client_id=payload.client_id,
        department_id=payload.department_id,
    )

    user = User(
        username=username,
        hashed_password=hash_password(payload.password),
        email=payload.email,
        full_name=payload.full_name,
        role=role,
        department_id=payload.department_id,
        client_id=payload.client_id,
        is_active=payload.is_active,
    )
    session.add(user)
    await session.flush()
    return user


async def update_user(
    session: AsyncSession,
    user: User,
    payload: UserUpdate,
) -> User:
    updated_fields = payload.model_fields_set

    if "full_name" in updated_fields:
        user.full_name = payload.full_name

    if "email" in updated_fields:
        user.email = payload.email

    if "role" in updated_fields and payload.role is not None:
        user.role = validate_role(payload.role)

    if "department_id" in updated_fields:
        user.department_id = payload.department_id

    if "client_id" in updated_fields:
        user.client_id = payload.client_id

    if "is_active" in updated_fields and payload.is_active is not None:
        user.is_active = payload.is_active

    await _validate_user_references(
        session=session,
        role=user.role,
        client_id=user.client_id,
        department_id=user.department_id,
    )

    return user


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _get_current_user_from_local_token(
    token: str,
    session: AsyncSession,
) -> User:
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
    except JWTError as error:
        raise _credentials_exception() from error

    if not isinstance(username, str) or not username:
        raise _credentials_exception()

    user = await get_user_by_username(session=session, username=username)
    if user is None or not user.is_active:
        raise _credentials_exception()

    return user


async def _get_current_user_from_external_token(
    token: str,
    session: AsyncSession,
) -> User:
    settings = get_settings()
    try:
        external_user = await validate_external_token(token=token, settings=settings)
    except ExternalAuthConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    except JWTError as error:
        raise _credentials_exception() from error

    user = await get_user_by_username(
        session=session,
        username=external_user.username,
    )
    if user is None and external_user.email:
        user = await get_user_by_email(session=session, email=external_user.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "User exists in external identity provider but is not registered "
                "in QazPostWeb."
            ),
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive in QazPostWeb.",
        )

    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session, use_cache=False),
) -> User:
    auth_mode = get_settings().auth_mode.strip().lower()

    if auth_mode == "local":
        return await _get_current_user_from_local_token(token=token, session=session)

    if auth_mode == "external":
        return await _get_current_user_from_external_token(token=token, session=session)

    if auth_mode == "hybrid":
        try:
            return await _get_current_user_from_local_token(token=token, session=session)
        except HTTPException as local_error:
            if not external_auth_is_configured(get_settings()):
                raise local_error
            return await _get_current_user_from_external_token(
                token=token,
                session=session,
            )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="AUTH_MODE must be one of: local, external, hybrid.",
    )


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
