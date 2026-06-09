from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import GeneratedBarcode, GeneratedBatch
from app.schemas import (
    BarcodeNumberRequest,
    BarcodeNumberResponse,
    GeneratedBarcodeItem,
    GeneratedBarcodeSearchResponse,
    GeneratedBatchDetail,
    GeneratedBatchItem,
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
