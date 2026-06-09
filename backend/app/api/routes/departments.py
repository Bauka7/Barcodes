from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import User
from app.schemas import DepartmentItem, DepartmentTreeItem
from app.services.auth_service import get_current_user
from app.services.department_service import get_departments_tree, list_departments

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentItem], status_code=status.HTTP_200_OK)
async def get_departments(
    search: str | None = Query(default=None),
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[DepartmentItem]:
    try:
        departments = await list_departments(
            session=session,
            search=search,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [
        DepartmentItem(
            id=department.id,
            code=department.code,
            name=department.name,
            region=department.region,
            parent_id=department.parent_id,
            department_type=department.department_type,
            full_path=department.full_path,
        )
        for department in departments
    ]


@router.get("/tree", response_model=list[DepartmentTreeItem], status_code=status.HTTP_200_OK)
async def get_department_tree(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[DepartmentTreeItem]:
    items = await get_departments_tree(session=session)
    return [DepartmentTreeItem.model_validate(item) for item in items]
