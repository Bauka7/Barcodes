from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import BarcodeRange, RangeRequest, User
from app.schemas import (
    BarcodeRangeRead,
    RangeRequestCreate,
    RangeRequestDecision,
    RangeRequestRead,
)
from app.services.audit_service import create_audit_log
from app.services.auth_service import require_roles
from app.services.range_request_service import (
    approve_range_request,
    cancel_range_request,
    can_access_range_request,
    create_range_request,
    deserialize_payload,
    get_range_request_by_id,
    get_range_request_by_id_for_update,
    list_range_requests,
    reject_range_request,
)

router = APIRouter(prefix="/range-requests", tags=["range requests"])


def _range_request_to_schema(range_request: RangeRequest) -> RangeRequestRead:
    return RangeRequestRead(
        id=range_request.id,
        requester_id=range_request.requester_id,
        client_id=range_request.client_id,
        department_id=range_request.department_id,
        package_type=range_request.package_type,
        requested_quantity=range_request.requested_quantity,
        request_type=range_request.request_type,
        purpose=range_request.purpose,
        requested_code=range_request.requested_code,
        approved_code=range_request.approved_code,
        decision_notes=range_request.decision_notes,
        payload=deserialize_payload(range_request.payload),
        status=range_request.status,
        handled_by=range_request.handled_by,
        handled_at=range_request.handled_at,
        notes=range_request.notes,
        created_at=range_request.created_at,
        updated_at=range_request.updated_at,
    )


def _barcode_range_to_schema(barcode_range: BarcodeRange) -> BarcodeRangeRead:
    return BarcodeRangeRead(
        id=barcode_range.id,
        package_type=barcode_range.package_type,
        region_code=barcode_range.region_code,
        start_number=barcode_range.start_number,
        end_number=barcode_range.end_number,
        current_number=barcode_range.current_number,
        status=barcode_range.status,
        issued_to_client_id=barcode_range.issued_to_client_id,
        issued_to_department_id=barcode_range.issued_to_department_id,
        request_id=barcode_range.request_id,
        issued_by=barcode_range.issued_by,
        issued_at=barcode_range.issued_at,
        expires_at=barcode_range.expires_at,
        cancellation_reason=barcode_range.cancellation_reason,
        cancelled_by=barcode_range.cancelled_by,
        cancelled_at=barcode_range.cancelled_at,
        notes=barcode_range.notes,
        created_at=barcode_range.created_at,
        updated_at=barcode_range.updated_at,
    )


@router.post("", response_model=RangeRequestRead, status_code=status.HTTP_201_CREATED)
async def create_range_request_endpoint(
    payload: RangeRequestCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> RangeRequestRead:
    try:
        async with session.begin():
            range_request = await create_range_request(
                session=session,
                payload=payload,
                requester=current_user,
            )
            await create_audit_log(
                session=session,
                action="range_request_created",
                user=current_user,
                request=request,
                entity_type="range_request",
                entity_id=str(range_request.id),
                department_id=range_request.department_id,
                details={
                    "purpose": range_request.purpose,
                    "requested_quantity": range_request.requested_quantity,
                    "requested_code": range_request.requested_code,
                    "client_id": range_request.client_id,
                    "department_id": range_request.department_id,
                },
            )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return _range_request_to_schema(range_request)


@router.get("", response_model=list[RangeRequestRead], status_code=status.HTTP_200_OK)
async def get_range_requests(
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    status_filter: str | None = Query(default=None, alias="status"),
    package_type: str | None = Query(default=None),
    client_id: int | None = Query(default=None),
    department_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> list[RangeRequestRead]:
    try:
        range_requests = await list_range_requests(
            session=session,
            current_user=current_user,
            limit=limit,
            offset=offset,
            status=status_filter,
            package_type=package_type,
            client_id=client_id,
            department_id=department_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [_range_request_to_schema(range_request) for range_request in range_requests]


@router.get("/{request_id}", response_model=RangeRequestRead, status_code=status.HTTP_200_OK)
async def get_range_request_endpoint(
    request_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> RangeRequestRead:
    range_request = await get_range_request_by_id(session=session, request_id=request_id)

    if range_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Range request with id {request_id} was not found.",
        )

    if not await can_access_range_request(
        session=session,
        current_user=current_user,
        range_request=range_request,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions.",
        )

    return _range_request_to_schema(range_request)


@router.post(
    "/{request_id}/approve",
    response_model=RangeRequestRead,
    status_code=status.HTTP_200_OK,
)
async def approve_range_request_endpoint(
    request_id: int,
    payload: RangeRequestDecision,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> RangeRequestRead:
    try:
        async with session.begin():
            range_request = await get_range_request_by_id_for_update(
                session=session,
                request_id=request_id,
            )

            if range_request is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Range request with id {request_id} was not found.",
                )

            if not await can_access_range_request(
                session=session,
                current_user=current_user,
                range_request=range_request,
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions.",
                )

            range_request, barcode_range = await approve_range_request(
                session=session,
                range_request=range_request,
                handled_by=current_user,
                approved_code=payload.approved_code,
                expires_at=None,
                notes=payload.notes,
            )
            await session.refresh(range_request)
            await session.refresh(barcode_range)
            await create_audit_log(
                session=session,
                action="range_request_approved",
                user=current_user,
                request=request,
                entity_type="range_request",
                entity_id=str(range_request.id),
                department_id=range_request.department_id,
                details={
                    "range_id": barcode_range.id,
                    "approved_code": range_request.approved_code,
                },
            )
            await create_audit_log(
                session=session,
                action="barcode_range_issued",
                user=current_user,
                request=request,
                entity_type="barcode_range",
                entity_id=str(barcode_range.id),
                department_id=barcode_range.issued_to_department_id,
                details=_barcode_range_to_schema(barcode_range).model_dump(mode="json"),
            )
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return _range_request_to_schema(range_request)


@router.post(
    "/{request_id}/reject",
    response_model=RangeRequestRead,
    status_code=status.HTTP_200_OK,
)
async def reject_range_request_endpoint(
    request_id: int,
    payload: RangeRequestDecision,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> RangeRequestRead:
    try:
        async with session.begin():
            range_request = await get_range_request_by_id_for_update(
                session=session,
                request_id=request_id,
            )

            if range_request is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Range request with id {request_id} was not found.",
                )

            if not await can_access_range_request(
                session=session,
                current_user=current_user,
                range_request=range_request,
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions.",
                )

            range_request = await reject_range_request(
                session=session,
                range_request=range_request,
                handled_by=current_user,
                notes=payload.notes,
            )
            await session.refresh(range_request)
            await create_audit_log(
                session=session,
                action="range_request_rejected",
                user=current_user,
                request=request,
                entity_type="range_request",
                entity_id=str(range_request.id),
                department_id=range_request.department_id,
                details={"notes": payload.notes},
            )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return _range_request_to_schema(range_request)


@router.post(
    "/{request_id}/cancel",
    response_model=RangeRequestRead,
    status_code=status.HTTP_200_OK,
)
async def cancel_range_request_endpoint(
    request_id: int,
    payload: RangeRequestDecision,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator", "client")),
) -> RangeRequestRead:
    try:
        async with session.begin():
            range_request = await get_range_request_by_id_for_update(
                session=session,
                request_id=request_id,
            )

            if range_request is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Range request with id {request_id} was not found.",
                )

            # Клиент может отменить только заявку своей организации.
            if not await can_access_range_request(
                session=session,
                current_user=current_user,
                range_request=range_request,
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions.",
                )

            range_request = await cancel_range_request(
                session=session,
                range_request=range_request,
                handled_by=current_user,
                notes=payload.notes,
            )
            await session.refresh(range_request)
            await create_audit_log(
                session=session,
                action=(
                    "range_request_cancelled_by_client"
                    if current_user.role == "client"
                    else "range_request_cancelled"
                ),
                user=current_user,
                request=request,
                entity_type="range_request",
                entity_id=str(range_request.id),
                department_id=range_request.department_id,
                details={"notes": payload.notes},
            )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return _range_request_to_schema(range_request)
