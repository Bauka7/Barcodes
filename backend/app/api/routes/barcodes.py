from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.schemas import BarcodeNumberRequest, BarcodeNumberResponse
from app.services.barcode_number_service import CounterNotFoundError, generate_barcode_numbers

router = APIRouter(prefix="/barcodes", tags=["barcodes"])


@router.post("/numbers", response_model=BarcodeNumberResponse, status_code=status.HTTP_200_OK)
async def create_barcode_numbers(
    payload: BarcodeNumberRequest,
    session: AsyncSession = Depends(get_db_session),
) -> BarcodeNumberResponse:
    try:
        items = await generate_barcode_numbers(
            session=session,
            package_type=payload.package_type,
            quantity=payload.quantity,
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

    return BarcodeNumberResponse(items=items, count=len(items))
