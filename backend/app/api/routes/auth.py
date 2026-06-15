from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.database import get_db_session
from app.models import User
from app.schemas import Token, UserRead
from app.services.audit_service import log_user_action
from app.services.auth_service import authenticate_user, get_current_user

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
    user = await authenticate_user(
        session=session,
        username=form_data.username,
        password=form_data.password,
    )

    if user is None:
        await log_user_action(
            session=session,
            action="login_failed",
            username=form_data.username,
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

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


@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return user_to_schema(current_user)
