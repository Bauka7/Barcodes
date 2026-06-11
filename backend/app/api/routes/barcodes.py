from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import GeneratedBarcode, GeneratedBatch, PrintedBatch, User
from app.schemas import (
    BarcodeCancelRequest,
    BarcodeDepartmentInfo,
    BarcodeDetailResponse,
    BarcodeLifecycleListResponse,
    BarcodeMarkUsedRequest,
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
    batch_belongs_to_client,
    get_batch_detail,
    list_batches,
    list_batches_for_client,
    search_barcode,
)
from app.services.barcode_number_service import (
    CounterNotFoundError,
    generate_barcode_numbers_with_history,
)
from app.services.audit_service import create_audit_log, log_user_action
from app.services.auth_service import require_roles
from app.services.barcode_lifecycle_service import (
    GeneratedBarcodeNotFoundError,
    cancel_barcode,
    get_barcode_detail,
    list_barcodes_by_lifecycle,
    mark_barcode_used,
)
from app.services.pdf_label_service import (
    GeneratedBatchNotFoundError,
    generate_batch_pdf_and_track_print,
    generate_batch_pdf_preview,
)
from app.services.print_tracking_service import (
    list_print_history,
    list_print_history_for_client,
)

router = APIRouter(prefix="/barcodes", tags=["barcodes"])


@router.post("/numbers", response_model=BarcodeNumberResponse, status_code=status.HTTP_200_OK)
async def create_barcode_numbers(
    payload: BarcodeNumberRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> BarcodeNumberResponse:
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

    await log_user_action(
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
        barcodes = await list_barcodes_by_lifecycle(
            session=session,
            status=status_filter,
            package_type=package_type,
            department_id=department_id,
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

    await log_user_action(
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


@router.post(
    "/{barcode}/cancel",
    response_model=GeneratedBarcodeItem,
    status_code=status.HTTP_200_OK,
)
async def cancel_barcode_endpoint(
    barcode: str,
    payload: BarcodeCancelRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> GeneratedBarcodeItem:
    try:
        async with session.begin():
            barcode_record = await cancel_barcode(
                session=session,
                barcode=barcode,
                current_user=current_user,
                reason=payload.reason,
            )
            await create_audit_log(
                session=session,
                action="barcode_cancelled",
                user=current_user,
                request=request,
                entity_type="generated_barcode",
                entity_id=str(barcode_record.id),
                details={
                    "barcode": barcode_record.barcode,
                    "reason": payload.reason,
                },
            )
    except GeneratedBarcodeNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return _barcode_to_schema(barcode_record)


@router.post(
    "/{barcode}/mark-used",
    response_model=GeneratedBarcodeItem,
    status_code=status.HTTP_200_OK,
)
async def mark_barcode_used_endpoint(
    barcode: str,
    payload: BarcodeMarkUsedRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> GeneratedBarcodeItem:
    try:
        async with session.begin():
            barcode_record = await mark_barcode_used(
                session=session,
                barcode=barcode,
                current_user=current_user,
                notes=payload.notes,
            )
            await create_audit_log(
                session=session,
                action="barcode_marked_used",
                user=current_user,
                request=request,
                entity_type="generated_barcode",
                entity_id=str(barcode_record.id),
                details={
                    "barcode": barcode_record.barcode,
                    "notes": payload.notes,
                },
            )
    except GeneratedBarcodeNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return _barcode_to_schema(barcode_record)


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
        batches = await list_batches(
            session=session,
            limit=limit,
            offset=offset,
            package_type=package_type,
            department_id=department_id,
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
    if current_user.client_id is None:
        return []

    try:
        batches = await list_batches_for_client(
            session=session,
            client_id=current_user.client_id,
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
    if current_user.client_id is None or not await batch_belongs_to_client(
        session=session,
        batch_id=batch_id,
        client_id=current_user.client_id,
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
    if current_user.client_id is None:
        return []

    try:
        printed_batches = await list_print_history_for_client(
            session=session,
            client_id=current_user.client_id,
            limit=limit,
            offset=offset,
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
    if current_user.role == "client" and (
        current_user.client_id is None
        or not await batch_belongs_to_client(
            session=session,
            batch_id=batch_id,
            client_id=current_user.client_id,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions.",
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

    await log_user_action(
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
    if current_user.role == "client" and (
        current_user.client_id is None
        or not await batch_belongs_to_client(
            session=session,
            batch_id=batch_id,
            client_id=current_user.client_id,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions.",
        )

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

    await log_user_action(
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
        printed_batches = await list_print_history(
            session=session,
            limit=limit,
            offset=offset,
            department_id=department_id,
            generated_batch_id=generated_batch_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [_printed_batch_to_schema(printed_batch) for printed_batch in printed_batches]
