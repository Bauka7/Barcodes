from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BarcodeRange, GeneratedBarcode, GeneratedBatch, PrintedBatch


async def create_printed_batch(
    session: AsyncSession,
    batch: GeneratedBatch,
    barcodes: list[GeneratedBarcode],
    printed_by: str | None = None,
    printer_name: str | None = None,
    notes: str | None = None,
) -> PrintedBatch:
    if not barcodes:
        raise ValueError("Cannot print an empty batch.")

    result = await session.execute(
        select(GeneratedBarcode)
        .where(GeneratedBarcode.batch_id == batch.id)
        .order_by(GeneratedBarcode.id)
        .with_for_update()
    )
    locked_barcodes = list(result.scalars().all())
    if not locked_barcodes:
        raise ValueError("Cannot print an empty batch.")

    unsupported_statuses = {
        barcode.status
        for barcode in locked_barcodes
        if barcode.status not in {"generated", "printed"}
    }
    if unsupported_statuses:
        statuses = ", ".join(sorted(unsupported_statuses))
        raise ValueError(
            "Only generated or already printed barcodes can be printed. "
            f"Unsupported statuses found: {statuses}."
        )

    now = datetime.now(timezone.utc)
    printed_batch = PrintedBatch(
        generated_batch_id=batch.id,
        department_id=batch.department_id,
        printed_count=len(locked_barcodes),
        first_barcode=locked_barcodes[0].barcode,
        last_barcode=locked_barcodes[-1].barcode,
        printed_by=printed_by,
        printer_name=printer_name,
        status="printed",
        printed_at=now,
        notes=notes,
    )
    session.add(printed_batch)

    for barcode in locked_barcodes:
        barcode.printed = True
        if barcode.printed_at is None:
            barcode.printed_at = now
        if barcode.printed_by is None:
            barcode.printed_by = printed_by
        if barcode.status == "generated":
            barcode.status = "printed"

    await session.flush()
    return printed_batch


def _validate_print_history_pagination(limit: int, offset: int) -> tuple[int, int]:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0.")

    return limit, offset


async def list_print_history(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    department_id: int | None = None,
    department_ids: list[int] | None = None,
    generated_batch_id: int | None = None,
) -> list[PrintedBatch]:
    validated_limit, validated_offset = _validate_print_history_pagination(limit, offset)
    statement = select(PrintedBatch).order_by(PrintedBatch.printed_at.desc())

    if department_id is not None:
        statement = statement.where(PrintedBatch.department_id == department_id)

    if department_ids is not None:
        if not department_ids:
            return []
        statement = statement.where(PrintedBatch.department_id.in_(department_ids))

    if generated_batch_id is not None:
        statement = statement.where(PrintedBatch.generated_batch_id == generated_batch_id)

    statement = statement.limit(validated_limit).offset(validated_offset)
    result = await session.execute(statement)
    return list(result.scalars().all())


async def list_print_history_for_client(
    session: AsyncSession,
    client_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[PrintedBatch]:
    """История печати по партиям организации клиента."""

    validated_limit, validated_offset = _validate_print_history_pagination(limit, offset)
    statement = (
        select(PrintedBatch)
        .join(GeneratedBatch, PrintedBatch.generated_batch_id == GeneratedBatch.id)
        .join(BarcodeRange, GeneratedBatch.range_id == BarcodeRange.id)
        .where(BarcodeRange.issued_to_client_id == client_id)
        .order_by(PrintedBatch.printed_at.desc())
        .limit(validated_limit)
        .offset(validated_offset)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())
