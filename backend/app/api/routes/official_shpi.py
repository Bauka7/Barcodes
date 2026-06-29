from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import User
from app.schemas.official_shpi import (
    OfficialShpiConnectionResponse,
    OfficialShpiCounterItem,
    OfficialShpiPreviewItem,
    OfficialShpiSyncResponse,
)
from app.services.audit_service import create_audit_log
from app.services.auth_service import require_roles
from app.services.official_shpi_service import (
    OfficialShpiConfigurationError,
    OfficialShpiConnectionError,
    OfficialShpiDisabledError,
    get_counters,
    preview,
    sync_counters_to_local_db,
    test_connection,
)

router = APIRouter(prefix="/admin/official-shpi", tags=["admin official shpi"])


def _service_unavailable(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=detail,
    )


def _handle_official_shpi_error(error: Exception) -> HTTPException:
    if isinstance(error, OfficialShpiDisabledError):
        return _service_unavailable("Official SHPI database integration is disabled.")

    if isinstance(error, OfficialShpiConfigurationError):
        return _service_unavailable(str(error))

    if isinstance(error, OfficialShpiConnectionError):
        return _service_unavailable("Official SHPI database connection failed.")

    return _service_unavailable("Official SHPI database request failed.")


@router.get(
    "/test-connection",
    response_model=OfficialShpiConnectionResponse,
    status_code=status.HTTP_200_OK,
)
async def test_official_shpi_connection(
    current_user: User = Depends(require_roles("admin")),
) -> OfficialShpiConnectionResponse:
    try:
        result = await test_connection()
    except (
        OfficialShpiDisabledError,
        OfficialShpiConfigurationError,
        OfficialShpiConnectionError,
    ) as error:
        raise _handle_official_shpi_error(error) from error

    return OfficialShpiConnectionResponse.model_validate(result)


@router.get(
    "/preview",
    response_model=list[OfficialShpiPreviewItem],
    status_code=status.HTTP_200_OK,
)
async def preview_official_shpi_records(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> list[OfficialShpiPreviewItem]:
    try:
        rows = await preview(limit=limit)
    except (
        OfficialShpiDisabledError,
        OfficialShpiConfigurationError,
        OfficialShpiConnectionError,
    ) as error:
        raise _handle_official_shpi_error(error) from error

    return [OfficialShpiPreviewItem.model_validate(asdict(row)) for row in rows]


@router.get(
    "/counters",
    response_model=list[OfficialShpiCounterItem],
    status_code=status.HTTP_200_OK,
)
async def get_official_shpi_counters(
    fresh: bool = Query(default=False),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> list[OfficialShpiCounterItem]:
    try:
        counters = await get_counters(fresh=fresh)
    except (
        OfficialShpiDisabledError,
        OfficialShpiConfigurationError,
        OfficialShpiConnectionError,
    ) as error:
        raise _handle_official_shpi_error(error) from error

    return [OfficialShpiCounterItem.model_validate(asdict(counter)) for counter in counters]


@router.post(
    "/sync-counters",
    response_model=OfficialShpiSyncResponse,
    status_code=status.HTTP_200_OK,
)
async def sync_official_shpi_counters(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin")),
) -> OfficialShpiSyncResponse:
    try:
        async with session.begin():
            result = await sync_counters_to_local_db(session=session)
            result_dict = result.to_dict()
            await create_audit_log(
                session=session,
                action="official_shpi_counters_synced",
                user=current_user,
                request=request,
                entity_type="barcode_counters",
                department_id=current_user.department_id,
                details=result_dict,
            )
    except (
        OfficialShpiDisabledError,
        OfficialShpiConfigurationError,
        OfficialShpiConnectionError,
    ) as error:
        raise _handle_official_shpi_error(error) from error

    return OfficialShpiSyncResponse.model_validate(result_dict)
