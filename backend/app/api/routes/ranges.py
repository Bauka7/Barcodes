from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import BarcodeRange, User
from app.schemas import BarcodeRangeRead
from app.services.auth_service import require_roles
from app.services.barcode_range_service import get_range_by_id, list_ranges

router = APIRouter(prefix="/ranges", tags=["ranges"])


def _barcode_range_to_schema(barcode_range: BarcodeRange) -> BarcodeRangeRead:
    return BarcodeRangeRead(
        id=barcode_range.id,
        package_type=barcode_range.package_type,
        start_number=barcode_range.start_number,
        end_number=barcode_range.end_number,
        current_number=barcode_range.current_number,
        status=barcode_range.status,
        issued_to_client_id=barcode_range.issued_to_client_id,
        issued_to_department_id=barcode_range.issued_to_department_id,
        request_id=barcode_range.request_id,
        issued_by=barcode_range.issued_by,
        issued_at=barcode_range.issued_at,
        expires_at=barcode_range.expires_at,
        notes=barcode_range.notes,
        created_at=barcode_range.created_at,
        updated_at=barcode_range.updated_at,
    )


@router.get("", response_model=list[BarcodeRangeRead], status_code=status.HTTP_200_OK)
async def get_ranges(
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    package_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    client_id: int | None = Query(default=None),
    department_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> list[BarcodeRangeRead]:
    try:
        ranges = await list_ranges(
            session=session,
            limit=limit,
            offset=offset,
            package_type=package_type,
            status=status_filter,
            client_id=client_id,
            department_id=department_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [_barcode_range_to_schema(barcode_range) for barcode_range in ranges]


@router.get("/{range_id}", response_model=BarcodeRangeRead, status_code=status.HTTP_200_OK)
async def get_range_endpoint(
    range_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> BarcodeRangeRead:
    barcode_range = await get_range_by_id(session=session, range_id=range_id)

    if barcode_range is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Barcode range with id {range_id} was not found.",
        )

    return _barcode_range_to_schema(barcode_range)
