import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AuditLog, User
from app.services.department_scope_service import (
    DepartmentScopeError,
    get_user_department_scope_ids,
)

logger = logging.getLogger(__name__)


def _request_ip_address(request: Request | None) -> str | None:
    if request is None or request.client is None:
        return None

    return request.client.host


def _request_user_agent(request: Request | None) -> str | None:
    if request is None:
        return None

    return request.headers.get("user-agent")


def _json_default(value: object) -> object:
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Decimal):
        return float(value)

    return str(value)


def _serialize_details(details: dict[str, Any] | str | None) -> str | None:
    if details is None:
        return None

    if isinstance(details, str):
        return details

    return json.dumps(details, ensure_ascii=False, default=_json_default)


async def create_audit_log(
    session: AsyncSession,
    action: str,
    user: User | None = None,
    username: str | None = None,
    request: Request | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    department_id: int | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user.id if user else None,
        department_id=department_id,
        username=user.username if user else username,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=_request_ip_address(request),
        user_agent=_request_user_agent(request),
        details=_serialize_details(details),
    )
    session.add(audit_log)
    await session.flush()
    return audit_log


async def log_user_action(
    session: AsyncSession,
    action: str,
    user: User | None = None,
    username: str | None = None,
    request: Request | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    department_id: int | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    audit_log = await create_audit_log(
        session=session,
        action=action,
        user=user,
        username=username,
        request=request,
        entity_type=entity_type,
        entity_id=entity_id,
        department_id=department_id,
        details=details,
    )
    await session.commit()
    return audit_log


async def safe_log_user_action(
    session: AsyncSession,
    action: str,
    user: User | None = None,
    username: str | None = None,
    request: Request | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    department_id: int | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog | None:
    try:
        return await log_user_action(
            session=session,
            action=action,
            user=user,
            username=username,
            request=request,
            entity_type=entity_type,
            entity_id=entity_id,
            department_id=department_id,
            details=details,
        )
    except Exception:
        await session.rollback()
        logger.exception("Audit log failed for action '%s'.", action)
        return None


def _validate_audit_pagination(limit: int, offset: int) -> tuple[int, int]:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0.")

    return limit, offset


async def list_audit_logs(
    session: AsyncSession,
    current_user: User,
    limit: int = 20,
    offset: int = 0,
    action: str | None = None,
    username: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    department_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[AuditLog], int]:
    validated_limit, validated_offset = _validate_audit_pagination(limit, offset)
    statement = (
        select(AuditLog)
        .options(selectinload(AuditLog.department))
        .order_by(AuditLog.created_at.desc())
    )

    if current_user.role == "operator":
        try:
            allowed_department_ids = await get_user_department_scope_ids(
                session=session,
                user=current_user,
            )
        except DepartmentScopeError as error:
            raise PermissionError(str(error)) from error
        if not allowed_department_ids:
            return [], 0

        if department_id is not None and department_id not in allowed_department_ids:
            raise PermissionError("Not enough permissions for this department.")

        statement = statement.where(AuditLog.department_id.in_(allowed_department_ids))
    elif current_user.role != "admin":
        raise PermissionError("Not enough permissions to view audit logs.")

    if department_id is not None:
        statement = statement.where(AuditLog.department_id == department_id)

    if action:
        statement = statement.where(AuditLog.action == action)

    if username:
        statement = statement.where(AuditLog.username == username)

    if entity_type:
        statement = statement.where(AuditLog.entity_type == entity_type)

    if entity_id:
        statement = statement.where(AuditLog.entity_id == entity_id)

    if date_from:
        statement = statement.where(AuditLog.created_at >= date_from)

    if date_to:
        statement = statement.where(AuditLog.created_at <= date_to)

    count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
    total = int((await session.execute(count_statement)).scalar_one())
    result = await session.execute(
        statement.limit(validated_limit).offset(validated_offset)
    )
    return list(result.scalars().all()), total
