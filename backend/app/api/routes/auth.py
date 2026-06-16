from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.core.config import get_settings
from app.db.database import get_db_session
from app.models import User
from app.schemas import Token, UserRead
from app.services.audit_service import log_user_action
from app.services.auth_service import (
    authenticate_external_password,
    authenticate_local_admin,
    authenticate_user,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def user_to_schema(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        department_id=user.department_id,
        client_id=user.client_id,
        is_active=user.is_active,
        created_at=user.created_at,    
        updated_at=user.updated_at,
    )


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
        await log_user_action(
            session=session,
            action="login_success",
            user=user,
            request=request,
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
                await log_user_action(
                    session=session,
                    action="local_admin_login_success",
                    user=admin_user,
                    request=request,
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
        await log_user_action(
            session=session,
            action="keycloak_login_success",
            user=user,
            request=request,
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
            await log_user_action(
                session=session,
                action="login_success",
                user=user,
                request=request,
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
        await log_user_action(
            session=session,
            action="keycloak_login_success",
            user=user,
            request=request,
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
    await log_user_action(
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
) -> UserRead:
    return user_to_schema(current_user)
