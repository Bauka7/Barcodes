from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Department, GeneratedBarcode, GeneratedBatch


async def create_generation_history(
    session: AsyncSession,
    package_type: str,
    barcodes: list[str],
    sequence_numbers: list[int],
    department_id: int | None = None,
    range_id: int | None = None,
    generated_by: str | None = None,
    source: str = "api",
    notes: str | None = None,
) -> GeneratedBatch:
    if not barcodes:
        raise ValueError("At least one barcode is required.")

    if len(barcodes) != len(sequence_numbers):
        raise ValueError("Barcode and sequence number counts do not match.")

    if department_id is not None:
        result = await session.execute(
            select(Department.id).where(Department.id == department_id)
        )
        if result.scalar_one_or_none() is None:
            raise ValueError(f"Department with id {department_id} was not found.")

    batch = GeneratedBatch(
        package_type=package_type,
        quantity=len(barcodes),
        first_barcode=barcodes[0],
        last_barcode=barcodes[-1],
        department_id=department_id,
        range_id=range_id,
        generated_by=generated_by,
        source=source,
        status="generated",
        notes=notes,
    )
    session.add(batch)
    await session.flush()

    for barcode, sequence_number in zip(barcodes, sequence_numbers, strict=True):
        session.add(
            GeneratedBarcode(
                batch_id=batch.id,
                barcode=barcode,
                package_type=package_type,
                department_id=department_id,
                range_id=range_id,
                sequence_number=sequence_number,
            )
        )

    await session.flush()
    return batch


def _validate_history_pagination(limit: int, offset: int) -> tuple[int, int]:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0.")

    return limit, offset


async def list_batches(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    package_type: str | None = None,
    department_id: int | None = None,
) -> list[GeneratedBatch]:
    validated_limit, validated_offset = _validate_history_pagination(limit, offset)
    statement = select(GeneratedBatch).order_by(GeneratedBatch.generated_at.desc())

    normalized_package_type = (package_type or "").strip().upper()
    if normalized_package_type:
        statement = statement.where(GeneratedBatch.package_type == normalized_package_type)

    if department_id is not None:
        statement = statement.where(GeneratedBatch.department_id == department_id)

    statement = statement.limit(validated_limit).offset(validated_offset)
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_batch_detail(
    session: AsyncSession,
    batch_id: int,
) -> tuple[GeneratedBatch, list[GeneratedBarcode]] | None:
    batch_result = await session.execute(
        select(GeneratedBatch).where(GeneratedBatch.id == batch_id)
    )
    batch = batch_result.scalar_one_or_none()

    if batch is None:
        return None

    barcodes_result = await session.execute(
        select(GeneratedBarcode)
        .where(GeneratedBarcode.batch_id == batch_id)
        .order_by(GeneratedBarcode.id)
    )
    return batch, list(barcodes_result.scalars().all())


async def search_barcode(
    session: AsyncSession,
    barcode: str,
) -> tuple[GeneratedBarcode, GeneratedBatch] | None:
    normalized_barcode = barcode.strip().upper()
    barcode_result = await session.execute(
        select(GeneratedBarcode).where(GeneratedBarcode.barcode == normalized_barcode)
    )
    generated_barcode = barcode_result.scalar_one_or_none()

    if generated_barcode is None:
        return None

    batch_result = await session.execute(
        select(GeneratedBatch).where(GeneratedBatch.id == generated_barcode.batch_id)
    )
    batch = batch_result.scalar_one()
    return generated_barcode, batch
