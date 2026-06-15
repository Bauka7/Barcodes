from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import GeneratedBarcode, GeneratedBatch, PrintedBatch, User
from app.schemas import (
    BarcodeDepartmentInfo,
    BarcodeDetailResponse,
    BarcodeLifecycleListResponse,
    BarcodeNumberRequest,
    BarcodeNumberResponse,
    BarcodeRangeInfo,
    GeneratedBarcodeItem,
    GeneratedBarcodeSearchResponse,
    GeneratedBatchDetail,
    GeneratedBatchItem,
    PrintedBatchItem,
    PrintBatchRequest,
)
from app.services.barcode_history_service import (
    batch_belongs_to_departments,
    get_batch_detail,
    list_batches,
    list_batches_for_departments,
    search_barcode,
)
from app.services.barcode_number_service import (
    CounterNotFoundError,
    generate_barcode_numbers_with_history,
)
from app.services.audit_service import safe_log_user_action
from app.services.auth_service import require_roles
from app.services.barcode_lifecycle_service import (
    GeneratedBarcodeNotFoundError,
    get_barcode_detail,
    list_barcodes_by_lifecycle,
)
from app.services.pdf_label_service import (
    GeneratedBatchNotFoundError,
    generate_batch_pdf_and_track_print,
    generate_batch_pdf_preview,
)
from app.services.print_tracking_service import (
    list_print_history,
)
from app.services.department_scope_service import (
    DepartmentScopeError,
    can_access_department,
    get_user_department_scope_ids,
)

router = APIRouter(prefix="/barcodes", tags=["barcodes"])


@router.post("/numbers", response_model=BarcodeNumberResponse, status_code=status.HTTP_200_OK)
async def create_barcode_numbers(
    payload: BarcodeNumberRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> BarcodeNumberResponse:
    if payload.department_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="department_id is required.",
        )

    if not await _department_is_visible(
        session=session,
        department_id=payload.department_id,
        current_user=current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions for this department.",
        )

    await session.rollback()

    try:
        result = await generate_barcode_numbers_with_history(
            session=session,
            package_type=payload.package_type,
            quantity=payload.quantity,
            department_id=payload.department_id,
            generated_by=current_user.username if current_user else payload.generated_by,
            notes=payload.notes,
        )
    except CounterNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Generated barcode already exists. The transaction was rolled back.",
        ) from error

    await safe_log_user_action(
        session=session,
        action="barcode_generated",
        user=current_user,
        request=request,
        entity_type="generated_batch",
        entity_id=str(result.batch_id),
        details={
            "package_type": payload.package_type,
            "quantity": payload.quantity,
            "department_id": payload.department_id,
            "first_barcode": result.first_barcode,
            "last_barcode": result.last_barcode,
        },
    )

    return BarcodeNumberResponse(
        batch_id=result.batch_id,
        items=result.items,
        count=len(result.items),
        first_barcode=result.first_barcode,
        last_barcode=result.last_barcode,
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


def _barcode_to_schema(barcode: GeneratedBarcode) -> GeneratedBarcodeItem:
    return GeneratedBarcodeItem(
        id=barcode.id,
        batch_id=barcode.batch_id,
        barcode=barcode.barcode,
        package_type=barcode.package_type,
        department_id=barcode.department_id,
        range_id=barcode.range_id,
        sequence_number=barcode.sequence_number,
        printed=barcode.printed,
        printed_at=barcode.printed_at,
        generated_by=barcode.generated_by,
        printed_by=barcode.printed_by,
        status=barcode.status,
        cancelled_at=barcode.cancelled_at,
        cancelled_by=barcode.cancelled_by,
        cancellation_reason=barcode.cancellation_reason,
        used_at=barcode.used_at,
        used_by=barcode.used_by,
        usage_notes=barcode.usage_notes,
        generated_at=barcode.generated_at,
    )


def _printed_batch_to_schema(printed_batch: PrintedBatch) -> PrintedBatchItem:
    return PrintedBatchItem(
        id=printed_batch.id,
        generated_batch_id=printed_batch.generated_batch_id,
        department_id=printed_batch.department_id,
        printed_count=printed_batch.printed_count,
        first_barcode=printed_batch.first_barcode,
        last_barcode=printed_batch.last_barcode,
        printed_by=printed_batch.printed_by,
        printer_name=printed_batch.printer_name,
        status=printed_batch.status,
        printed_at=printed_batch.printed_at,
        notes=printed_batch.notes,
    )


def _pdf_response(
    pdf_bytes: bytes,
    filename: str,
) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _get_scope_ids_or_400(
    session: AsyncSession,
    current_user: User,
) -> list[int] | None:
    try:
        return await get_user_department_scope_ids(session=session, user=current_user)
    except DepartmentScopeError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


async def _batch_is_visible(
    session: AsyncSession,
    batch_id: int,
    current_user: User,
) -> bool:
    scope_ids = await _get_scope_ids_or_400(session=session, current_user=current_user)
    if scope_ids is None:
        return True

    return await batch_belongs_to_departments(
        session=session,
        batch_id=batch_id,
        department_ids=scope_ids,
    )


async def _department_is_visible(
    session: AsyncSession,
    department_id: int | None,
    current_user: User,
) -> bool:
    try:
        return await can_access_department(
            session=session,
            user=current_user,
            department_id=department_id,
        )
    except DepartmentScopeError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    "/lifecycle",
    response_model=BarcodeLifecycleListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_barcode_lifecycle_items(
    status_filter: str | None = Query(default=None, alias="status"),
    package_type: str | None = Query(default=None),
    department_id: int | None = Query(default=None),
    printed: bool | None = Query(default=None),
    limit: int = Query(default=20),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> BarcodeLifecycleListResponse:
    try:
        department_ids = await _get_scope_ids_or_400(
            session=session,
            current_user=current_user,
        )
        if department_id is not None and not await _department_is_visible(
            session=session,
            department_id=department_id,
            current_user=current_user,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions for this department.",
            )
        barcodes = await list_barcodes_by_lifecycle(
            session=session,
            status=status_filter,
            package_type=package_type,
            department_id=department_id,
            department_ids=department_ids,
            printed=printed,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    items = [_barcode_to_schema(barcode) for barcode in barcodes]
    return BarcodeLifecycleListResponse(items=items, count=len(items))


def _barcode_detail_to_schema(
    barcode: GeneratedBarcode,
    batch: GeneratedBatch,
    barcode_range,
    department,
) -> BarcodeDetailResponse:
    range_info = None
    if barcode_range is not None:
        range_info = BarcodeRangeInfo(
            id=barcode_range.id,
            package_type=barcode_range.package_type,
            start_number=barcode_range.start_number,
            end_number=barcode_range.end_number,
            current_number=barcode_range.current_number,
            status=barcode_range.status,
        )

    department_info = None
    if department is not None:
        department_info = BarcodeDepartmentInfo(
            id=department.id,
            code=department.code,
            name=department.name,
            region=department.region,
        )

    barcode_item = _barcode_to_schema(barcode)
    return BarcodeDetailResponse(
        **barcode_item.model_dump(),
        batch=_batch_to_schema(batch),
        range=range_info,
        department=department_info,
    )


@router.get(
    "/{barcode}/detail",
    response_model=BarcodeDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_barcode_detail_endpoint(
    barcode: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> BarcodeDetailResponse:
    try:
        barcode_record, batch, barcode_range, department = await get_barcode_detail(
            session=session,
            barcode=barcode,
        )
    except GeneratedBarcodeNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    if not await _department_is_visible(
        session=session,
        department_id=barcode_record.department_id,
        current_user=current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated barcode '{barcode}' was not found.",
        )

    await safe_log_user_action(
        session=session,
        action="barcode_detail_viewed",
        user=current_user,
        request=request,
        entity_type="generated_barcode",
        entity_id=str(barcode_record.id),
        details={"barcode": barcode_record.barcode},
    )

    return _barcode_detail_to_schema(
        barcode=barcode_record,
        batch=batch,
        barcode_range=barcode_range,
        department=department,
    )


@router.get(
    "/history/batches",
    response_model=list[GeneratedBatchItem],
    status_code=status.HTTP_200_OK,
)
async def get_generation_batches(
    limit: int = Query(default=20),
    offset: int = Query(default=0),
    package_type: str | None = Query(default=None),
    department_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> list[GeneratedBatchItem]:
    try:
        department_ids = await _get_scope_ids_or_400(
            session=session,
            current_user=current_user,
        )
        if department_id is not None and not await _department_is_visible(
            session=session,
            department_id=department_id,
            current_user=current_user,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions for this department.",
            )
        batches = await list_batches(
            session=session,
            limit=limit,
            offset=offset,
            package_type=package_type,
            department_id=department_id,
            department_ids=department_ids,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [_batch_to_schema(batch) for batch in batches]


@router.get(
    "/history/batches/{batch_id}",
    response_model=GeneratedBatchDetail,
    status_code=status.HTTP_200_OK,
)
async def get_generation_batch_detail(
    batch_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> GeneratedBatchDetail:
    result = await get_batch_detail(session=session, batch_id=batch_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated batch with id {batch_id} was not found.",
        )

    batch, barcodes = result
    if not await _batch_is_visible(
        session=session,
        batch_id=batch.id,
        current_user=current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated batch with id {batch_id} was not found.",
        )

    batch_item = _batch_to_schema(batch)
    return GeneratedBatchDetail(
        **batch_item.model_dump(),
        barcodes=[_barcode_to_schema(barcode) for barcode in barcodes],
    )


@router.get(
    "/history/search",
    response_model=GeneratedBarcodeSearchResponse,
    status_code=status.HTTP_200_OK,
)
async def search_generated_barcode(
    barcode: str = Query(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> GeneratedBarcodeSearchResponse:
    result = await search_barcode(session=session, barcode=barcode)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated barcode '{barcode}' was not found.",
        )

    generated_barcode, batch = result
    if not await _department_is_visible(
        session=session,
        department_id=generated_barcode.department_id,
        current_user=current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated barcode '{barcode}' was not found.",
        )

    barcode_item = _barcode_to_schema(generated_barcode)
    return GeneratedBarcodeSearchResponse(
        **barcode_item.model_dump(),
        batch=_batch_to_schema(batch),
    )


@router.get(
    "/my-batches",
    response_model=list[GeneratedBatchItem],
    status_code=status.HTTP_200_OK,
)
async def get_my_batches(
    limit: int = Query(default=20),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> list[GeneratedBatchItem]:
    scope_ids = await _get_scope_ids_or_400(session=session, current_user=current_user)
    if scope_ids is not None and not scope_ids:
        return []

    try:
        if scope_ids is None:
            batches = await list_batches(
                session=session,
                limit=limit,
                offset=offset,
            )
        else:
            batches = await list_batches_for_departments(
                session=session,
                department_ids=scope_ids,
                limit=limit,
                offset=offset,
            )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [_batch_to_schema(batch) for batch in batches]


@router.get(
    "/my-batches/{batch_id}",
    response_model=GeneratedBatchDetail,
    status_code=status.HTTP_200_OK,
)
async def get_my_batch_detail(
    batch_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> GeneratedBatchDetail:
    if not await _batch_is_visible(
        session=session,
        batch_id=batch_id,
        current_user=current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated batch with id {batch_id} was not found.",
        )

    result = await get_batch_detail(session=session, batch_id=batch_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated batch with id {batch_id} was not found.",
        )

    batch, barcodes = result
    batch_item = _batch_to_schema(batch)
    return GeneratedBatchDetail(
        **batch_item.model_dump(),
        barcodes=[_barcode_to_schema(barcode) for barcode in barcodes],
    )


@router.get(
    "/my-print-history",
    response_model=list[PrintedBatchItem],
    status_code=status.HTTP_200_OK,
)
async def get_my_print_history(
    limit: int = Query(default=20),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> list[PrintedBatchItem]:
    scope_ids = await _get_scope_ids_or_400(session=session, current_user=current_user)
    if scope_ids is not None and not scope_ids:
        return []

    try:
        printed_batches = await list_print_history(
            session=session,
            limit=limit,
            offset=offset,
            department_ids=scope_ids,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [_printed_batch_to_schema(printed_batch) for printed_batch in printed_batches]


@router.get(
    "/batches/{batch_id}/pdf-preview",
    response_class=Response,
    status_code=status.HTTP_200_OK,
)
async def preview_batch_pdf(
    batch_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> Response:
    # Клиент может смотреть PDF только своих партий (партий своей организации).
    if not await _batch_is_visible(
        session=session,
        batch_id=batch_id,
        current_user=current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated batch with id {batch_id} was not found.",
        )

    try:
        pdf_bytes = await generate_batch_pdf_preview(
            session=session,
            batch_id=batch_id,
        )
    except GeneratedBatchNotFoundError as error:
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
        action="pdf_preview_generated",
        user=current_user,
        request=request,
        entity_type="generated_batch",
        entity_id=str(batch_id),
    )

    return _pdf_response(
        pdf_bytes=pdf_bytes,
        filename=f"barcodes_batch_{batch_id}_preview.pdf",
    )


@router.post(
    "/batches/{batch_id}/pdf",
    response_class=Response,
    status_code=status.HTTP_200_OK,
)
async def print_batch_pdf(
    batch_id: int,
    payload: PrintBatchRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> Response:
    # Клиент может печатать только свои партии (партий своей организации).
    if not await _batch_is_visible(
        session=session,
        batch_id=batch_id,
        current_user=current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated batch with id {batch_id} was not found.",
        )

    await session.rollback()

    try:
        pdf_bytes = await generate_batch_pdf_and_track_print(
            session=session,
            batch_id=batch_id,
            printed_by=current_user.username if current_user else payload.printed_by,
            printer_name=payload.printer_name,
            notes=payload.notes,
        )
    except GeneratedBatchNotFoundError as error:
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
        action="client_pdf_downloaded" if current_user.role == "client" else "batch_printed",
        user=current_user,
        request=request,
        entity_type="generated_batch",
        entity_id=str(batch_id),
        details={"printer_name": payload.printer_name},
    )

    return _pdf_response(
        pdf_bytes=pdf_bytes,
        filename=f"barcodes_batch_{batch_id}.pdf",
    )


@router.get(
    "/print-history",
    response_model=list[PrintedBatchItem],
    status_code=status.HTTP_200_OK,
)
async def get_print_history(
    limit: int = Query(default=20),
    offset: int = Query(default=0),
    department_id: int | None = Query(default=None),
    generated_batch_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> list[PrintedBatchItem]:
    try:
        department_ids = await _get_scope_ids_or_400(
            session=session,
            current_user=current_user,
        )
        if department_id is not None and not await _department_is_visible(
            session=session,
            department_id=department_id,
            current_user=current_user,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions for this department.",
            )
        printed_batches = await list_print_history(
            session=session,
            limit=limit,
            offset=offset,
            department_id=department_id,
            department_ids=department_ids,
            generated_batch_id=generated_batch_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [_printed_batch_to_schema(printed_batch) for printed_batch in printed_batches]
