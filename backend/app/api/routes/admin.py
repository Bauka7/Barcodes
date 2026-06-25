from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import User
from app.schemas import (
    MissingShpiRegionDepartmentItem,
    MissingShpiRegionDepartmentResponse,
)
from app.schemas.shpi_map import ShpiMapResponse
from app.services.audit_service import safe_log_user_action
from app.services.auth_service import require_roles
from app.services.department_service import list_departments_missing_shpi_region
from app.services.filpassport_department_import_service import (
    FilPassportImportError,
    import_departments_from_filpassport,
)
from app.services.shpi_map_service import get_shpi_map

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/shpi-map",
    response_model=ShpiMapResponse,
    status_code=status.HTTP_200_OK,
)
async def get_admin_shpi_map(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> ShpiMapResponse:
    data = await get_shpi_map(session=session)
    return ShpiMapResponse.model_validate(data)


@router.get(
    "/departments/missing-shpi-region",
    response_model=MissingShpiRegionDepartmentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_departments_missing_shpi_region(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin")),
) -> MissingShpiRegionDepartmentResponse:
    departments = await list_departments_missing_shpi_region(session=session)
    items = [
        MissingShpiRegionDepartmentItem(
            id=department.id,
            code=department.code,
            name=department.name,
            department_type=department.department_type,
            full_path=department.full_path,
        )
        for department in departments
    ]
    return MissingShpiRegionDepartmentResponse(items=items, total=len(items))


@router.post(
    "/departments/import-filpassport",
    status_code=status.HTTP_200_OK,
)
async def import_filpassport_departments(
    request: Request,
    dry_run: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin")),
) -> dict[str, object]:
    try:
        result = await import_departments_from_filpassport(
            session=session,
            dry_run=dry_run,
        )
    except FilPassportImportError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    await safe_log_user_action(
        session=session,
        action="filpassport_departments_import_dry_run"
        if dry_run
        else "filpassport_departments_imported",
        user=current_user,
        request=request,
        entity_type="departments",
        details=result.to_dict(),
    )
    return result.to_dict()
