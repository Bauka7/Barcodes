from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import find_nearest_moderator, user_to_schema
from app.db.database import get_db_session
from app.models import Department, User
from app.schemas import UserCreate, UserProfileUpdate, UserRead, UserUpdate
from app.services.audit_service import create_audit_log
from app.services.auth_service import (
    create_user,
    get_current_user,
    get_user_by_id,
    require_roles,
    update_user,
)
from app.services.shpi_region_service import get_inherited_department_shpi_region_code

router = APIRouter(prefix="/users", tags=["users"])


async def _user_profile_to_schema(
    session: AsyncSession,
    user: User,
) -> UserRead:
    department = None
    department_shpi_region_code = None
    if user.department_id is not None:
        department_result = await session.execute(
            select(Department).where(Department.id == user.department_id)
        )
        department = department_result.scalar_one_or_none()
        department_shpi_region_code = await get_inherited_department_shpi_region_code(
            session=session,
            department_id=user.department_id,
        )

    moderator = await find_nearest_moderator(session=session, department=department)
    return user_to_schema(
        user,
        department=department,
        moderator=moderator,
        department_shpi_region_code=department_shpi_region_code,
    )


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
                department_id=user.department_id,
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


@router.patch("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def update_my_profile(
    payload: UserProfileUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    async with session.begin():
        user = await get_user_by_id(session=session, user_id=current_user.id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {current_user.id} was not found.",
            )

        updated_fields = payload.model_fields_set
        if "full_name" in updated_fields:
            user.full_name = payload.full_name
        if "email" in updated_fields:
            user.email = payload.email
        if "phone" in updated_fields:
            user.phone = payload.phone

        await session.flush()
        await session.refresh(user)
        await create_audit_log(
            session=session,
            action="user_profile_updated",
            user=user,
            request=request,
            entity_type="user",
            entity_id=str(user.id),
            department_id=user.department_id,
            details=payload.model_dump(exclude_unset=True),
        )

    return await _user_profile_to_schema(session=session, user=user)


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

            await update_user(session=session, user=user, payload=payload)
            await session.flush()
            await session.refresh(user)
            audit_action = "user_updated"
            if "is_active" in payload.model_fields_set:
                audit_action = "user_activated" if user.is_active else "user_deactivated"

            await create_audit_log(
                session=session,
                action=audit_action,
                user=current_user,
                request=request,
                entity_type="user",
                entity_id=str(user.id),
                department_id=user.department_id,
                details=payload.model_dump(exclude_unset=True),
            )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return user_to_schema(user)
