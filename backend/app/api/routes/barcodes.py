from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import GeneratedBarcode, GeneratedBatch, PrintedBatch
from app.schemas import (
    BarcodeNumberRequest,
    BarcodeNumberResponse,
    GeneratedBarcodeItem,
    GeneratedBarcodeSearchResponse,
    GeneratedBatchDetail,
    GeneratedBatchItem,
    PrintedBatchItem,
    PrintBatchRequest,
)
from app.services.barcode_history_service import (
    get_batch_detail,
    list_batches,
    search_barcode,
)
from app.services.barcode_number_service import (
    CounterNotFoundError,
    generate_barcode_numbers_with_history,
)
from app.services.pdf_label_service import (
    GeneratedBatchNotFoundError,
    generate_batch_pdf_and_track_print,
    generate_batch_pdf_preview,
)
from app.services.print_tracking_service import list_print_history

router = APIRouter(prefix="/barcodes", tags=["barcodes"])


@router.post("/numbers", response_model=BarcodeNumberResponse, status_code=status.HTTP_200_OK)
async def create_barcode_numbers(
    payload: BarcodeNumberRequest,
    session: AsyncSession = Depends(get_db_session),
) -> BarcodeNumberResponse:
    try:
        result = await generate_barcode_numbers_with_history(
            session=session,
            package_type=payload.package_type,
            quantity=payload.quantity,
            department_id=payload.department_id,
            generated_by=payload.generated_by,
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
        sequence_number=barcode.sequence_number,
        printed=barcode.printed,
        printed_at=barcode.printed_at,
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
    "/batches/{batch_id}/pdf-preview",
    response_class=Response,
    status_code=status.HTTP_200_OK,
)
async def preview_batch_pdf(
    batch_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
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
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    try:
        pdf_bytes = await generate_batch_pdf_and_track_print(
            session=session,
            batch_id=batch_id,
            printed_by=payload.printed_by,
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
