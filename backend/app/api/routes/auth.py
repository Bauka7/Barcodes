from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.core.config import get_settings
from app.db.database import get_db_session
from app.models import Department, User
from app.schemas import Token, UserRead
from app.services.audit_service import safe_log_user_action
from app.services.auth_service import (
    authenticate_external_password,
    authenticate_local_admin,
    authenticate_user,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])

ROLE_LABELS = {
    "admin": "Администратор",
    "operator": "Модератор",
    "client": "Сотрудник отделения",
}

SCOPE_LABELS = {
    "all": "Все подразделения",
    "subtree": "Свое подразделение и дочерние отделения",
    "own": "Свое подразделение",
}


def get_user_scope(user: User) -> dict[str, str]:
    if user.role == "admin":
        scope_type = "all"
    elif user.role == "operator":
        scope_type = "subtree"
    else:
        scope_type = "own"

    return {
        "type": scope_type,
        "label": SCOPE_LABELS[scope_type],
    }


def user_to_schema(
    user: User,
    department: Department | None = None,
    moderator: User | None = None,
) -> UserRead:
    return UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        role=user.role,
        role_label=ROLE_LABELS.get(user.role, user.role),
        department_id=user.department_id,
        client_id=user.client_id,
        is_active=user.is_active,
        department=(
            {
                "id": department.id,
                "code": department.code,
                "name": department.name,
                "region": department.region,
                "department_type": department.department_type,
                "full_path": department.full_path,
            }
            if department is not None
            else None
        ),
        moderator=(
            {
                "id": moderator.id,
                "username": moderator.username,
                "full_name": moderator.full_name,
                "email": moderator.email,
                "phone": moderator.phone,
                "role": moderator.role,
            }
            if moderator is not None
            else None
        ),
        scope=get_user_scope(user),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


async def find_nearest_moderator(
    session: AsyncSession,
    department: Department | None,
) -> User | None:
    if department is None:
        return None

    parent_id = department.parent_id
    visited_department_ids: set[int] = set()

    while parent_id is not None and parent_id not in visited_department_ids:
        visited_department_ids.add(parent_id)

        moderator_result = await session.execute(
            select(User)
            .where(
                User.department_id == parent_id,
                User.role == "operator",
                User.is_active.is_(True),
            )
            .order_by(User.id)
            .limit(1)
        )
        moderator = moderator_result.scalar_one_or_none()
        if moderator is not None:
            return moderator

        department_result = await session.execute(
            select(Department).where(Department.id == parent_id)
        )
        parent_department = department_result.scalar_one_or_none()
        parent_id = parent_department.parent_id if parent_department is not None else None

    return None


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> Token:
    settings = get_settings()
    auth_mode = settings.auth_mode.strip().lower()

    if auth_mode == "local":
        user = await authenticate_user(
            session=session,
            username=form_data.username,
            password=form_data.password,
        )

        if user is None:
            await _log_failed_login(session, request, form_data.username)
            raise _invalid_login_exception()

        access_token = create_access_token(
            subject=user.username,
            extra_claims={"role": user.role},
        )
        await safe_log_user_action(
            session=session,
            action="login_success",
            user=user,
            request=request,
            department_id=user.department_id,
        )
        return Token(access_token=access_token)

    if auth_mode in {"external", "keycloak"}:
        if settings.local_admin_login_enabled:
            admin_user = await authenticate_local_admin(
                session=session,
                username=form_data.username,
                password=form_data.password,
            )
            if admin_user is not None:
                access_token = create_access_token(
                    subject=admin_user.username,
                    extra_claims={"role": admin_user.role, "auth_source": "local_admin"},
                )
                await safe_log_user_action(
                    session=session,
                    action="local_admin_login_success",
                    user=admin_user,
                    request=request,
                    department_id=admin_user.department_id,
                )
                return Token(access_token=access_token)

        try:
            token, user = await authenticate_external_password(
                session=session,
                username=form_data.username,
                password=form_data.password,
            )
        except HTTPException:
            await _log_failed_login(session, request, form_data.username)
            raise
        await safe_log_user_action(
            session=session,
            action="keycloak_login_success",
            user=user,
            request=request,
            department_id=user.department_id,
        )
        return Token(access_token=token.access_token, token_type=token.token_type)

    if auth_mode == "hybrid":
        user = await authenticate_user(
            session=session,
            username=form_data.username,
            password=form_data.password,
        )
        if user is not None:
            access_token = create_access_token(
                subject=user.username,
                extra_claims={"role": user.role},
            )
            await safe_log_user_action(
                session=session,
                action="login_success",
                user=user,
                request=request,
                department_id=user.department_id,
            )
            return Token(access_token=access_token)

        try:
            token, user = await authenticate_external_password(
                session=session,
                username=form_data.username,
                password=form_data.password,
            )
        except HTTPException:
            await _log_failed_login(session, request, form_data.username)
            raise
        await safe_log_user_action(
            session=session,
            action="keycloak_login_success",
            user=user,
            request=request,
            department_id=user.department_id,
        )
        return Token(access_token=token.access_token, token_type=token.token_type)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="AUTH_MODE must be one of: local, external, keycloak, hybrid.",
    )


async def _log_failed_login(
    session: AsyncSession,
    request: Request,
    username: str,
) -> None:
    await safe_log_user_action(
        session=session,
        action="login_failed",
        username=username,
        request=request,
    )


def _invalid_login_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def read_current_user(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserRead:
    department = None
    if current_user.department_id is not None:
        result = await session.execute(
            select(Department).where(Department.id == current_user.department_id)
        )
        department = result.scalar_one_or_none()

    moderator = await find_nearest_moderator(session=session, department=department)

    return user_to_schema(
        current_user,
        department=department,
        moderator=moderator,
    )
