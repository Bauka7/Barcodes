from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BarcodeRange, GeneratedBatch
from app.services.barcode_history_service import create_generation_history
from app.services.barcode_number_service import (
    DEFAULT_COUNTRY_SUFFIX,
    DEFAULT_OBL_CODE,
    build_barcode_number,
    get_setting_value,
    validate_quantity,
)


class BarcodeRangeNotFoundError(LookupError):
    pass


@dataclass(slots=True)
class RangeGenerationResult:
    batch_id: int
    range_id: int
    items: list[str]
    first_barcode: str
    last_barcode: str
    remaining: int
    range_status: str


def calculate_range_remaining(barcode_range: BarcodeRange) -> int:
    if barcode_range.status != "active":
        return 0

    return max(0, barcode_range.end_number - barcode_range.current_number + 1)


async def get_range_remaining(
    session: AsyncSession,
    range_id: int,
) -> BarcodeRange:
    result = await session.execute(
        select(BarcodeRange).where(BarcodeRange.id == range_id)
    )
    barcode_range = result.scalar_one_or_none()

    if barcode_range is None:
        raise BarcodeRangeNotFoundError(f"Barcode range with id {range_id} was not found.")

    return barcode_range


async def list_batches_for_range(
    session: AsyncSession,
    range_id: int,
    limit: int = 100,
    offset: int = 0,
) -> list[GeneratedBatch]:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0.")

    statement = (
        select(GeneratedBatch)
        .where(GeneratedBatch.range_id == range_id)
        .order_by(GeneratedBatch.generated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def generate_barcodes_from_range(
    session: AsyncSession,
    range_id: int,
    quantity: int,
    generated_by: str,
    notes: str | None = None,
) -> RangeGenerationResult:
    validated_quantity = validate_quantity(quantity)

    async with session.begin():
        result = await session.execute(
            select(BarcodeRange)
            .where(BarcodeRange.id == range_id)
            .with_for_update()
        )
        barcode_range = result.scalar_one_or_none()

        if barcode_range is None:
            raise BarcodeRangeNotFoundError(f"Barcode range with id {range_id} was not found.")

        # Защита: истёкший по сроку диапазон генерировать нельзя
        # (статус будет помечен expired при ближайшем чтении списка).
        if (
            barcode_range.status == "active"
            and barcode_range.expires_at is not None
            and barcode_range.expires_at < datetime.now(timezone.utc)
        ):
            raise ValueError("Range has expired and can no longer generate SHPI.")

        if barcode_range.status != "active":
            raise ValueError("Only active barcode ranges can generate SHPI.")

        remaining = calculate_range_remaining(barcode_range)
        if validated_quantity > remaining:
            raise ValueError(
                f"Not enough numbers remaining in range. Remaining: {remaining}."
            )

        obl_code = await get_setting_value(session, "obl_code", DEFAULT_OBL_CODE)
        suffix = (await get_setting_value(session, "country_suffix", DEFAULT_COUNTRY_SUFFIX)).upper()

        start_number = barcode_range.current_number
        end_number = start_number + validated_quantity - 1
        sequence_numbers = list(range(start_number, end_number + 1))
        items = [
            build_barcode_number(
                package_type=barcode_range.package_type,
                obl_code=obl_code,
                counter_value=sequence_number,
                suffix=suffix,
            )
            for sequence_number in sequence_numbers
        ]

        if end_number >= barcode_range.end_number:
            barcode_range.current_number = barcode_range.end_number
            barcode_range.status = "exhausted"
        else:
            barcode_range.current_number = end_number + 1

        batch = await create_generation_history(
            session=session,
            package_type=barcode_range.package_type,
            barcodes=items,
            sequence_numbers=sequence_numbers,
            department_id=barcode_range.issued_to_department_id,
            range_id=barcode_range.id,
            generated_by=generated_by,
            source="range",
            notes=notes,
        )
        remaining_after_generation = calculate_range_remaining(barcode_range)

    return RangeGenerationResult(
        batch_id=batch.id,
        range_id=range_id,
        items=items,
        first_barcode=items[0],
        last_barcode=items[-1],
        remaining=remaining_after_generation,
        range_status=barcode_range.status,
    )
