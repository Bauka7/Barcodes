from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BarcodeCounter, BarcodeRange, RangeRequest, User
from app.services.barcode_number_service import (
    MAX_COUNTER_VALUE,
    validate_package_type,
)

BARCODE_RANGE_STATUSES = {"active", "exhausted", "expired", "cancelled"}


def _validate_pagination(limit: int, offset: int) -> tuple[int, int]:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0.")

    return limit, offset


async def create_barcode_range_from_request(
    session: AsyncSession,
    range_request: RangeRequest,
    issued_by_user: User,
) -> BarcodeRange:
    package_type = validate_package_type(range_request.package_type)

    result = await session.execute(
        select(BarcodeCounter)
        .where(BarcodeCounter.package_type == package_type)
        .with_for_update()
    )
    counter = result.scalar_one_or_none()

    if counter is None:
        raise LookupError(f"Counter row for package_type '{package_type}' was not found.")

    start_number = counter.current_value + 1
    end_number = counter.current_value + range_request.requested_quantity

    if end_number > MAX_COUNTER_VALUE:
        raise ValueError("Counter exceeded the maximum 6-digit serial value.")

    counter.current_value = end_number
    barcode_range = BarcodeRange(
        package_type=package_type,
        start_number=start_number,
        end_number=end_number,
        current_number=start_number,
        status="active",
        issued_to_client_id=range_request.client_id,
        issued_to_department_id=range_request.department_id,
        request_id=range_request.id,
        issued_by=issued_by_user.id,
        issued_at=datetime.now(timezone.utc),
        notes=range_request.notes,
    )
    session.add(barcode_range)
    await session.flush()
    return barcode_range


async def get_range_by_id(
    session: AsyncSession,
    range_id: int,
) -> BarcodeRange | None:
    result = await session.execute(select(BarcodeRange).where(BarcodeRange.id == range_id))
    return result.scalar_one_or_none()


async def list_ranges(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0,
    package_type: str | None = None,
    status: str | None = None,
    client_id: int | None = None,
    department_id: int | None = None,
) -> list[BarcodeRange]:
    validated_limit, validated_offset = _validate_pagination(limit, offset)
    statement = select(BarcodeRange).order_by(BarcodeRange.created_at.desc())

    if package_type:
        statement = statement.where(BarcodeRange.package_type == validate_package_type(package_type))

    if status:
        normalized_status = status.strip().lower()
        if normalized_status not in BARCODE_RANGE_STATUSES:
            raise ValueError("status must be one of: active, exhausted, expired, cancelled.")
        statement = statement.where(BarcodeRange.status == normalized_status)

    if client_id is not None:
        statement = statement.where(BarcodeRange.issued_to_client_id == client_id)

    if department_id is not None:
        statement = statement.where(BarcodeRange.issued_to_department_id == department_id)

    statement = statement.limit(validated_limit).offset(validated_offset)
    result = await session.execute(statement)
    return list(result.scalars().all())
