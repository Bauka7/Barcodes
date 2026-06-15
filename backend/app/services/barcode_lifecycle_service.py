from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BarcodeRange, Department, GeneratedBarcode, GeneratedBatch, User
from app.services.barcode_number_service import validate_package_type

BARCODE_LIFECYCLE_STATUSES = {"generated", "printed"}


class GeneratedBarcodeNotFoundError(LookupError):
    pass


async def get_barcode_detail(
    session: AsyncSession,
    barcode: str,
) -> tuple[GeneratedBarcode, GeneratedBatch, BarcodeRange | None, Department | None, User | None]:
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
    range_created_by = None
    if generated_barcode.range_id is not None:
        range_result = await session.execute(
            select(BarcodeRange).where(BarcodeRange.id == generated_barcode.range_id)
        )
        barcode_range = range_result.scalar_one_or_none()
        if barcode_range is not None and barcode_range.issued_by is not None:
            user_result = await session.execute(
                select(User).where(User.id == barcode_range.issued_by)
            )
            range_created_by = user_result.scalar_one_or_none()

    department = None
    if generated_barcode.department_id is not None:
        department_result = await session.execute(
            select(Department).where(Department.id == generated_barcode.department_id)
        )
        department = department_result.scalar_one_or_none()

    return generated_barcode, batch, barcode_range, department, range_created_by


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
    department_ids: list[int] | None = None,
    printed: bool | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[GeneratedBarcode]:
    validated_limit, validated_offset = _validate_lifecycle_pagination(limit, offset)
    statement = select(GeneratedBarcode).order_by(GeneratedBarcode.generated_at.desc())

    if status:
        normalized_status = status.strip().lower()
        if normalized_status not in BARCODE_LIFECYCLE_STATUSES:
            raise ValueError("status must be one of: generated, printed.")
        statement = statement.where(GeneratedBarcode.status == normalized_status)
    else:
        statement = statement.where(GeneratedBarcode.status.in_(BARCODE_LIFECYCLE_STATUSES))

    if package_type:
        statement = statement.where(
            GeneratedBarcode.package_type == validate_package_type(package_type)
        )

    if department_id is not None:
        statement = statement.where(GeneratedBarcode.department_id == department_id)

    if department_ids is not None:
        if not department_ids:
            return []
        statement = statement.where(GeneratedBarcode.department_id.in_(department_ids))

    if printed is not None:
        statement = statement.where(GeneratedBarcode.printed == printed)

    statement = statement.limit(validated_limit).offset(validated_offset)
    result = await session.execute(statement)
    return list(result.scalars().all())
