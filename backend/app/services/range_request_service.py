from datetime import datetime, timezone
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BarcodeRange, RangeRequest, User
from app.schemas import RangeRequestCreate
from app.services.barcode_number_service import MAX_COUNTER_VALUE, validate_package_type
from app.services.barcode_range_service import create_barcode_range_from_request

RANGE_REQUEST_STATUSES = {"pending", "approved", "rejected", "cancelled"}


def _serialize_payload(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return None

    return json.dumps(payload, ensure_ascii=False)


def deserialize_payload(payload: str | None) -> dict[str, Any] | None:
    if payload is None:
        return None

    try:
        value = json.loads(payload)
    except json.JSONDecodeError:
        return {"raw": payload}

    if isinstance(value, dict):
        return value

    return {"value": value}


def _validate_pagination(limit: int, offset: int) -> tuple[int, int]:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0.")

    return limit, offset


def validate_requested_quantity(requested_quantity: int) -> int:
    if requested_quantity < 1 or requested_quantity > MAX_COUNTER_VALUE:
        raise ValueError(f"requested_quantity must be between 1 and {MAX_COUNTER_VALUE}.")

    return requested_quantity


async def create_range_request(
    session: AsyncSession,
    payload: RangeRequestCreate,
    requester: User,
) -> RangeRequest:
    package_type = validate_package_type(payload.package_type)
    requested_quantity = validate_requested_quantity(payload.requested_quantity)

    if not payload.request_type.strip():
        raise ValueError("request_type is required.")

    range_request = RangeRequest(
        requester_id=requester.id,
        client_id=payload.client_id,
        department_id=payload.department_id,
        package_type=package_type,
        requested_quantity=requested_quantity,
        request_type=payload.request_type.strip(),
        payload=_serialize_payload(payload.payload),
        status="pending",
        notes=payload.notes,
    )
    session.add(range_request)
    await session.flush()
    return range_request


async def get_range_request_by_id(
    session: AsyncSession,
    request_id: int,
) -> RangeRequest | None:
    result = await session.execute(select(RangeRequest).where(RangeRequest.id == request_id))
    return result.scalar_one_or_none()


async def list_range_requests(
    session: AsyncSession,
    current_user: User,
    limit: int = 100,
    offset: int = 0,
    status: str | None = None,
    package_type: str | None = None,
    client_id: int | None = None,
    department_id: int | None = None,
) -> list[RangeRequest]:
    validated_limit, validated_offset = _validate_pagination(limit, offset)
    statement = select(RangeRequest).order_by(RangeRequest.created_at.desc())

    if current_user.role == "client":
        statement = statement.where(RangeRequest.requester_id == current_user.id)

    if status:
        normalized_status = status.strip().lower()
        if normalized_status not in RANGE_REQUEST_STATUSES:
            raise ValueError("status must be one of: pending, approved, rejected, cancelled.")
        statement = statement.where(RangeRequest.status == normalized_status)

    if package_type:
        statement = statement.where(RangeRequest.package_type == validate_package_type(package_type))

    if client_id is not None:
        statement = statement.where(RangeRequest.client_id == client_id)

    if department_id is not None:
        statement = statement.where(RangeRequest.department_id == department_id)

    statement = statement.limit(validated_limit).offset(validated_offset)
    result = await session.execute(statement)
    return list(result.scalars().all())


def can_view_range_request(current_user: User, range_request: RangeRequest) -> bool:
    if current_user.role in {"admin", "operator"}:
        return True

    return current_user.role == "client" and range_request.requester_id == current_user.id


async def approve_range_request(
    session: AsyncSession,
    range_request: RangeRequest,
    handled_by: User,
    notes: str | None = None,
) -> tuple[RangeRequest, BarcodeRange]:
    if range_request.status != "pending":
        raise ValueError("Only pending range requests can be approved.")

    barcode_range = await create_barcode_range_from_request(
        session=session,
        range_request=range_request,
        issued_by_user=handled_by,
    )
    range_request.status = "approved"
    range_request.handled_by = handled_by.id
    range_request.handled_at = datetime.now(timezone.utc)

    if notes is not None:
        range_request.notes = notes

    await session.flush()
    return range_request, barcode_range


async def reject_range_request(
    session: AsyncSession,
    range_request: RangeRequest,
    handled_by: User,
    notes: str | None = None,
) -> RangeRequest:
    if range_request.status != "pending":
        raise ValueError("Only pending range requests can be rejected.")

    range_request.status = "rejected"
    range_request.handled_by = handled_by.id
    range_request.handled_at = datetime.now(timezone.utc)

    if notes is not None:
        range_request.notes = notes

    await session.flush()
    return range_request


async def cancel_range_request(
    session: AsyncSession,
    range_request: RangeRequest,
    handled_by: User,
    notes: str | None = None,
) -> RangeRequest:
    if range_request.status != "pending":
        raise ValueError("Only pending range requests can be cancelled.")

    range_request.status = "cancelled"
    range_request.handled_by = handled_by.id
    range_request.handled_at = datetime.now(timezone.utc)

    if notes is not None:
        range_request.notes = notes

    await session.flush()
    return range_request
