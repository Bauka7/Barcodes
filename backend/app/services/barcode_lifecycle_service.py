from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BarcodeRange, Department, GeneratedBarcode, GeneratedBatch, User
from app.services.barcode_number_service import validate_package_type

BARCODE_LIFECYCLE_STATUSES = {"generated", "printed", "used", "cancelled"}


class GeneratedBarcodeNotFoundError(LookupError):
    pass


async def get_barcode_detail(
    session: AsyncSession,
    barcode: str,
) -> tuple[GeneratedBarcode, GeneratedBatch, BarcodeRange | None, Department | None]:
    normalized_barcode = barcode.strip().upper()
    result = await session.execute(
        select(GeneratedBarcode).where(GeneratedBarcode.barcode == normalized_barcode)
    )
    generated_barcode = result.scalar_one_or_none()

    if generated_barcode is None:
        raise GeneratedBarcodeNotFoundError(
            f"Generated barcode '{normalized_barcode}' was not found."
        )

    batch_result = await session.execute(
        select(GeneratedBatch).where(GeneratedBatch.id == generated_barcode.batch_id)
    )
    batch = batch_result.scalar_one()

    barcode_range = None
    if generated_barcode.range_id is not None:
        range_result = await session.execute(
            select(BarcodeRange).where(BarcodeRange.id == generated_barcode.range_id)
        )
        barcode_range = range_result.scalar_one_or_none()

    department = None
    if generated_barcode.department_id is not None:
        department_result = await session.execute(
            select(Department).where(Department.id == generated_barcode.department_id)
        )
        department = department_result.scalar_one_or_none()

    return generated_barcode, batch, barcode_range, department


async def _get_barcode_for_update(
    session: AsyncSession,
    barcode: str,
) -> GeneratedBarcode:
    normalized_barcode = barcode.strip().upper()
    result = await session.execute(
        select(GeneratedBarcode)
        .where(GeneratedBarcode.barcode == normalized_barcode)
        .with_for_update()
    )
    generated_barcode = result.scalar_one_or_none()

    if generated_barcode is None:
        raise GeneratedBarcodeNotFoundError(
            f"Generated barcode '{normalized_barcode}' was not found."
        )

    return generated_barcode


async def cancel_barcode(
    session: AsyncSession,
    barcode: str,
    current_user: User,
    reason: str,
) -> GeneratedBarcode:
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise ValueError("reason is required.")

    generated_barcode = await _get_barcode_for_update(session=session, barcode=barcode)

    if generated_barcode.status == "used":
        raise ValueError("Used barcodes cannot be cancelled.")

    if generated_barcode.status == "cancelled":
        raise ValueError("Barcode is already cancelled.")

    if generated_barcode.status not in {"generated", "printed"}:
        raise ValueError("Only generated or printed barcodes can be cancelled.")

    generated_barcode.status = "cancelled"
    generated_barcode.cancelled_at = datetime.now(timezone.utc)
    generated_barcode.cancelled_by = current_user.username
    generated_barcode.cancellation_reason = normalized_reason
    await session.flush()
    return generated_barcode


async def mark_barcode_used(
    session: AsyncSession,
    barcode: str,
    current_user: User,
    notes: str | None = None,
) -> GeneratedBarcode:
    generated_barcode = await _get_barcode_for_update(session=session, barcode=barcode)

    if generated_barcode.status == "cancelled":
        raise ValueError("Cancelled barcodes cannot be marked as used.")

    if generated_barcode.status == "used":
        raise ValueError("Barcode is already marked as used.")

    if generated_barcode.status not in {"generated", "printed"}:
        raise ValueError("Only generated or printed barcodes can be marked as used.")

    generated_barcode.status = "used"
    generated_barcode.used_at = datetime.now(timezone.utc)
    generated_barcode.used_by = current_user.username
    generated_barcode.usage_notes = notes
    await session.flush()
    return generated_barcode


def _validate_lifecycle_pagination(limit: int, offset: int) -> tuple[int, int]:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0.")

    return limit, offset


async def list_barcodes_by_lifecycle(
    session: AsyncSession,
    status: str | None = None,
    package_type: str | None = None,
    department_id: int | None = None,
    printed: bool | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[GeneratedBarcode]:
    validated_limit, validated_offset = _validate_lifecycle_pagination(limit, offset)
    statement = select(GeneratedBarcode).order_by(GeneratedBarcode.generated_at.desc())

    if status:
        normalized_status = status.strip().lower()
        if normalized_status not in BARCODE_LIFECYCLE_STATUSES:
            raise ValueError("status must be one of: generated, printed, used, cancelled.")
        statement = statement.where(GeneratedBarcode.status == normalized_status)

    if package_type:
        statement = statement.where(
            GeneratedBarcode.package_type == validate_package_type(package_type)
        )

    if department_id is not None:
        statement = statement.where(GeneratedBarcode.department_id == department_id)

    if printed is not None:
        statement = statement.where(GeneratedBarcode.printed == printed)

    statement = statement.limit(validated_limit).offset(validated_offset)
    result = await session.execute(statement)
    return list(result.scalars().all())
