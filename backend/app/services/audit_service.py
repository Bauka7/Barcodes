import json
import logging
from typing import Any

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, User

logger = logging.getLogger(__name__)


def _request_ip_address(request: Request | None) -> str | None:
    if request is None or request.client is None:
        return None

    return request.client.host


def _request_user_agent(request: Request | None) -> str | None:
    if request is None:
        return None

    return request.headers.get("user-agent")


def _serialize_details(details: dict[str, Any] | None) -> str | None:
    if details is None:
        return None

    return json.dumps(details, ensure_ascii=False)


async def create_audit_log(
    session: AsyncSession,
    action: str,
    user: User | None = None,
    username: str | None = None,
    request: Request | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user.id if user else None,
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
    limit: int = 20,
    offset: int = 0,
    action: str | None = None,
    username: str | None = None,
) -> list[AuditLog]:
    validated_limit, validated_offset = _validate_audit_pagination(limit, offset)
    statement = select(AuditLog).order_by(AuditLog.created_at.desc())

    if action:
        statement = statement.where(AuditLog.action == action)

    if username:
        statement = statement.where(AuditLog.username == username)

    statement = statement.limit(validated_limit).offset(validated_offset)
    result = await session.execute(statement)
    return list(result.scalars().all())
