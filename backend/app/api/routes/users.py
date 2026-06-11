from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import user_to_schema
from app.db.database import get_db_session
from app.models import User
from app.schemas import UserCreate, UserRead, UserUpdate
from app.services.audit_service import create_audit_log
from app.services.auth_service import (
    create_user,
    get_user_by_id,
    require_roles,
    update_user,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    payload: UserCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin")),
) -> UserRead:
    try:
        async with session.begin():
            user = await create_user(session=session, payload=payload)
            await create_audit_log(
                session=session,
                action="user_created",
                user=current_user,
                request=request,
                entity_type="user",
                entity_id=str(user.id),
                details={"username": user.username, "role": user.role},
            )
            await session.refresh(user)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return user_to_schema(user)


@router.get("", response_model=list[UserRead], status_code=status.HTTP_200_OK)
async def list_users(
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin")),
) -> list[UserRead]:
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 100.",
        )

    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="offset must be greater than or equal to 0.",
        )

    result = await session.execute(
        select(User).order_by(User.id).limit(limit).offset(offset)
    )
    return [user_to_schema(user) for user in result.scalars().all()]


@router.get("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_user_endpoint(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin")),
) -> UserRead:
    user = await get_user_by_id(session=session, user_id=user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found.",
        )

    return user_to_schema(user)


@router.patch("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
async def update_user_endpoint(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin")),
) -> UserRead:
    try:
        async with session.begin():
            user = await get_user_by_id(session=session, user_id=user_id)

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {user_id} was not found.",
                )

            await update_user(user=user, payload=payload)
            await session.flush()
            await session.refresh(user)
            await create_audit_log(
                session=session,
                action="user_updated",
                user=current_user,
                request=request,
                entity_type="user",
                entity_id=str(user.id),
                details=payload.model_dump(exclude_unset=True),
            )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return user_to_schema(user)
