from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BarcodeRange, RangeRequest, User
from app.services.barcode_number_service import (
    MAX_COUNTER_VALUE,
    validate_package_type,
)
from app.services.barcode_counter_service import get_or_create_official_counter_for_update
from app.services.shpi_region_service import resolve_generation_shpi_region_code

# MVP lifecycle is active -> exhausted or active -> cancelled.
# Keep "expired" readable for existing rows, but normal flow must not create it.
BARCODE_RANGE_STATUSES = {"active", "exhausted", "cancelled", "expired"}


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
    expires_at: datetime | None = None,
) -> BarcodeRange:
    package_type = validate_package_type(range_request.package_type)
    region_code = await resolve_generation_shpi_region_code(
        session=session,
        department_id=range_request.department_id,
    )

    counter = await get_or_create_official_counter_for_update(
        session=session,
        package_type=package_type,
        region_code=region_code,
    )

    if counter is None:
        raise LookupError(
            f"Counter row for package_type '{package_type}' and region_code "
            f"'{region_code}' was not found."
        )

    start_number = counter.current_value + 1
    end_number = counter.current_value + range_request.requested_quantity

    if end_number > MAX_COUNTER_VALUE:
        raise ValueError("Counter exceeded the maximum 6-digit serial value.")

    counter.current_value = end_number
    barcode_range = BarcodeRange(
        package_type=package_type,
        region_code=region_code,
        start_number=start_number,
        end_number=end_number,
        current_number=start_number,
        status="active",
        issued_to_client_id=range_request.client_id,
        issued_to_department_id=range_request.department_id,
        request_id=range_request.id,
        issued_by=issued_by_user.id,
        issued_at=datetime.now(timezone.utc),
        expires_at=expires_at,
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


async def get_range_by_id_for_update(
    session: AsyncSession,
    range_id: int,
) -> BarcodeRange | None:
    result = await session.execute(
        select(BarcodeRange)
        .where(BarcodeRange.id == range_id)
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def list_ranges(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0,
    package_type: str | None = None,
    status: str | None = None,
    client_id: int | None = None,
    department_id: int | None = None,
    department_ids: list[int] | None = None,
) -> list[BarcodeRange]:
    validated_limit, validated_offset = _validate_pagination(limit, offset)
    statement = select(BarcodeRange).order_by(BarcodeRange.created_at.desc())

    if package_type:
        statement = statement.where(BarcodeRange.package_type == validate_package_type(package_type))

    if status:
        normalized_status = status.strip().lower()
        if normalized_status not in BARCODE_RANGE_STATUSES:
            raise ValueError(
                "status must be one of: active, exhausted, cancelled, expired (legacy)."
            )
        statement = statement.where(BarcodeRange.status == normalized_status)

    if client_id is not None:
        statement = statement.where(BarcodeRange.issued_to_client_id == client_id)

    if department_id is not None:
        statement = statement.where(BarcodeRange.issued_to_department_id == department_id)

    if department_ids is not None:
        if not department_ids:
            return []
        statement = statement.where(BarcodeRange.issued_to_department_id.in_(department_ids))

    statement = statement.limit(validated_limit).offset(validated_offset)
    result = await session.execute(statement)
    return list(result.scalars().all())


async def expire_due_ranges(session: AsyncSession) -> int:
    """Legacy helper kept for future use; not called in the MVP request flow."""

    now = datetime.now(timezone.utc)
    statement = (
        update(BarcodeRange)
        .where(BarcodeRange.status == "active")
        .where(BarcodeRange.expires_at.is_not(None))
        .where(BarcodeRange.expires_at < now)
        .values(status="expired")
    )
    result = await session.execute(statement)
    await session.commit()
    return result.rowcount or 0


async def cancel_range(
    session: AsyncSession,
    barcode_range: BarcodeRange,
    cancelled_by_user: User,
    reason: str,
) -> BarcodeRange:
    """Cancel an active range. Exhausted/cancelled ranges stay immutable."""

    normalized_reason = (reason or "").strip()
    if not normalized_reason:
        raise ValueError("reason is required to cancel a range.")

    if barcode_range.status == "cancelled":
        raise ValueError("Range is already cancelled.")

    if barcode_range.status == "exhausted":
        raise ValueError("Exhausted ranges cannot be cancelled.")

    if barcode_range.status != "active":
        raise ValueError("Only active ranges can be cancelled.")

    barcode_range.status = "cancelled"
    barcode_range.cancellation_reason = normalized_reason
    barcode_range.cancelled_by = cancelled_by_user.id
    barcode_range.cancelled_at = datetime.now(timezone.utc)
    await session.flush()
    return barcode_range


async def renew_range(
    session: AsyncSession,
    barcode_range: BarcodeRange,
    new_expires_at: datetime,
    renewed_by_user: User,
) -> BarcodeRange:
    """Продление диапазона тому же клиенту: задаёт новый срок.

    Для expired — реактивирует (expired → active). Отменённые не продлеваются.
    """

    if barcode_range.status not in {"active", "expired"}:
        raise ValueError("Only active or expired ranges can be renewed.")

    now = datetime.now(timezone.utc)
    expires_at = new_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise ValueError("new expiry date must be in the future.")

    barcode_range.expires_at = expires_at
    if barcode_range.status == "expired":
        barcode_range.status = "active"
    await session.flush()
    return barcode_range
