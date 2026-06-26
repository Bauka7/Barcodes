from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import BarcodeRange, GeneratedBatch, User
from app.schemas import (
    BarcodeNumberResponse,
    BarcodeRangeRead,
    GeneratedBatchItem,
    RangeCancelRequest,
    RangeGenerateRequest,
    RangeRemainingResponse,
)
from app.services.audit_service import create_audit_log, log_user_action, safe_log_user_action
from app.services.auth_service import require_roles
from app.services.barcode_range_service import (
    cancel_range,
    get_range_by_id,
    get_range_by_id_for_update,
    list_ranges,
)
from app.services.department_scope_service import (
    DepartmentScopeError,
    get_user_department_scope_ids,
    require_department_access,
)
from app.services.range_generation_service import (
    BarcodeRangeNotFoundError,
    calculate_range_remaining,
    generate_barcodes_from_range,
    get_range_remaining,
    list_batches_for_range,
)

router = APIRouter(prefix="/ranges", tags=["ranges"])


def _barcode_range_to_schema(barcode_range: BarcodeRange) -> BarcodeRangeRead:
    return BarcodeRangeRead(
        id=barcode_range.id,
        package_type=barcode_range.package_type,
        region_code=barcode_range.region_code,
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
        cancellation_reason=barcode_range.cancellation_reason,
        cancelled_by=barcode_range.cancelled_by,
        cancelled_at=barcode_range.cancelled_at,
        notes=barcode_range.notes,
        created_at=barcode_range.created_at,
        updated_at=barcode_range.updated_at,
    )


def _batch_to_schema(batch: GeneratedBatch) -> GeneratedBatchItem:
    return GeneratedBatchItem(
        id=batch.id,
        package_type=batch.package_type,
        quantity=batch.quantity,
        first_barcode=batch.first_barcode,
        last_barcode=batch.last_barcode,
        department_id=batch.department_id,
        range_id=batch.range_id,
        generated_by=batch.generated_by,
        source=batch.source,
        status=batch.status,
        generated_at=batch.generated_at,
        notes=batch.notes,
    )


def _legacy_unused_range_client_access(current_user: User, barcode_range: BarcodeRange) -> None:
    """Сотрудники видят все диапазоны; клиент — только диапазоны своей организации."""

    if current_user.role in {"admin", "operator"}:
        return

    if (
        current_user.role == "client"
        and current_user.client_id is not None
        and barcode_range.issued_to_client_id == current_user.client_id
    ):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions.",
    )


async def _assert_range_department_access(
    session: AsyncSession,
    current_user: User,
    barcode_range: BarcodeRange,
) -> None:
    try:
        await require_department_access(
            session=session,
            user=current_user,
            department_id=barcode_range.issued_to_department_id,
        )
    except DepartmentScopeError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error


@router.get("/my", response_model=list[BarcodeRangeRead], status_code=status.HTTP_200_OK)
async def get_my_ranges(
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    status_filter: str | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> list[BarcodeRangeRead]:
    if current_user.department_id is None:
        return []

    try:
        department_ids = await get_user_department_scope_ids(
            session=session,
            user=current_user,
        )
        ranges = await list_ranges(
            session=session,
            limit=limit,
            offset=offset,
            status=status_filter,
            department_ids=department_ids,
        )
    except (DepartmentScopeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [_barcode_range_to_schema(barcode_range) for barcode_range in ranges]


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
        department_ids = await get_user_department_scope_ids(
            session=session,
            user=current_user,
        )
        ranges = await list_ranges(
            session=session,
            limit=limit,
            offset=offset,
            package_type=package_type,
            status=status_filter,
            client_id=client_id,
            department_id=department_id,
            department_ids=department_ids,
        )
    except (DepartmentScopeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [_barcode_range_to_schema(barcode_range) for barcode_range in ranges]


@router.post(
    "/{range_id}/generate",
    response_model=BarcodeNumberResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_from_range_endpoint(
    range_id: int,
    payload: RangeGenerateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> BarcodeNumberResponse:
    # Клиент может генерировать только из диапазона своей организации.
    barcode_range = await get_range_by_id(session=session, range_id=range_id)
    if barcode_range is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Barcode range with id {range_id} was not found.",
        )
    await _assert_range_department_access(
        session=session,
        current_user=current_user,
        barcode_range=barcode_range,
    )

    await log_user_action(
        session=session,
        action="range_generation_started",
        user=current_user,
        request=request,
        entity_type="barcode_range",
        entity_id=str(range_id),
        department_id=barcode_range.issued_to_department_id,
        details={"quantity": payload.quantity},
    )

    try:
        result = await generate_barcodes_from_range(
            session=session,
            range_id=range_id,
            quantity=payload.quantity,
            generated_by=current_user.username,
            notes=payload.notes,
        )
    except BarcodeRangeNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    await safe_log_user_action(
        session=session,
                action="shpi_generated",
        user=current_user,
        request=request,
        entity_type="generated_batch",
        entity_id=str(result.batch_id),
        department_id=barcode_range.issued_to_department_id,
        details={
            "range_id": result.range_id,
            "quantity": len(result.items),
            "first_barcode": result.first_barcode,
            "last_barcode": result.last_barcode,
            "remaining": result.remaining,
            "range_status": result.range_status,
        },
    )

    if current_user.role == "client":
        await safe_log_user_action(
            session=session,
            action="client_range_generated",
            user=current_user,
            request=request,
            entity_type="generated_batch",
            entity_id=str(result.batch_id),
            department_id=barcode_range.issued_to_department_id,
            details={"range_id": result.range_id, "quantity": len(result.items)},
        )

    if result.range_status == "exhausted":
        await safe_log_user_action(
            session=session,
            action="range_exhausted",
            user=current_user,
            request=request,
            entity_type="barcode_range",
            entity_id=str(range_id),
            department_id=barcode_range.issued_to_department_id,
            details={"batch_id": result.batch_id},
        )

    return BarcodeNumberResponse(
        batch_id=result.batch_id,
        items=result.items,
        count=len(result.items),
        first_barcode=result.first_barcode,
        last_barcode=result.last_barcode,
    )


@router.get(
    "/{range_id}/remaining",
    response_model=RangeRemainingResponse,
    status_code=status.HTTP_200_OK,
)
async def get_range_remaining_endpoint(
    range_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> RangeRemainingResponse:
    try:
        barcode_range = await get_range_remaining(session=session, range_id=range_id)
    except BarcodeRangeNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    await _assert_range_department_access(
        session=session,
        current_user=current_user,
        barcode_range=barcode_range,
    )

    return RangeRemainingResponse(
        range_id=barcode_range.id,
        remaining=calculate_range_remaining(barcode_range),
        current_number=barcode_range.current_number,
        end_number=barcode_range.end_number,
        status=barcode_range.status,
    )


@router.post(
    "/{range_id}/cancel",
    response_model=BarcodeRangeRead,
    status_code=status.HTTP_200_OK,
)
async def cancel_range_endpoint(
    range_id: int,
    payload: RangeCancelRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> BarcodeRangeRead:
    try:
        async with session.begin():
            barcode_range = await get_range_by_id_for_update(
                session=session,
                range_id=range_id,
            )

            if barcode_range is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Barcode range with id {range_id} was not found.",
                )

            await _assert_range_department_access(
                session=session,
                current_user=current_user,
                barcode_range=barcode_range,
            )

            barcode_range = await cancel_range(
                session=session,
                barcode_range=barcode_range,
                cancelled_by_user=current_user,
                reason=payload.reason,
            )
            await session.refresh(barcode_range)
            await create_audit_log(
                session=session,
                action="barcode_range_cancelled",
                user=current_user,
                request=request,
                entity_type="barcode_range",
                entity_id=str(range_id),
                department_id=barcode_range.issued_to_department_id,
                details={"reason": payload.reason},
            )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return _barcode_range_to_schema(barcode_range)


@router.get(
    "/{range_id}/batches",
    response_model=list[GeneratedBatchItem],
    status_code=status.HTTP_200_OK,
)
async def get_range_batches(
    range_id: int,
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> list[GeneratedBatchItem]:
    barcode_range = await get_range_by_id(session=session, range_id=range_id)
    if barcode_range is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Barcode range with id {range_id} was not found.",
        )
    await _assert_range_department_access(
        session=session,
        current_user=current_user,
        barcode_range=barcode_range,
    )

    try:
        batches = await list_batches_for_range(
            session=session,
            range_id=range_id,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [_batch_to_schema(batch) for batch in batches]


@router.get("/{range_id}", response_model=BarcodeRangeRead, status_code=status.HTTP_200_OK)
async def get_range_endpoint(
    range_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> BarcodeRangeRead:
    barcode_range = await get_range_by_id(session=session, range_id=range_id)

    if barcode_range is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Barcode range with id {range_id} was not found.",
        )

    await _assert_range_department_access(
        session=session,
        current_user=current_user,
        barcode_range=barcode_range,
    )

    return _barcode_range_to_schema(barcode_range)
