from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import BarcodeCodeCatalog, User
from app.schemas import BarcodeCodeRead
from app.services.auth_service import require_roles
from app.services.barcode_code_service import get_catalog_code, list_catalog_codes

router = APIRouter(prefix="/barcode-codes", tags=["barcode codes"])


def _to_schema(entry: BarcodeCodeCatalog) -> BarcodeCodeRead:
    return BarcodeCodeRead(
        id=entry.id,
        code=entry.code,
        name=entry.name,
        category=entry.category,
        status=entry.status,
        owner=entry.owner,
        notes=entry.notes,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.get("", response_model=list[BarcodeCodeRead], status_code=status.HTTP_200_OK)
async def list_barcode_codes(
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    status_filter: str | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> list[BarcodeCodeRead]:
    try:
        codes = await list_catalog_codes(
            session=session,
            limit=limit,
            offset=offset,
            status=status_filter,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [_to_schema(entry) for entry in codes]


@router.get("/{code}", response_model=BarcodeCodeRead, status_code=status.HTTP_200_OK)
async def get_barcode_code(
    code: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> BarcodeCodeRead:
    try:
        entry = await get_catalog_code(session=session, code=code)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Barcode code '{code}' was not found.",
        )

    return _to_schema(entry)
