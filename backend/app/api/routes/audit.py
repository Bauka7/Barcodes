from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import AuditLog, User
from app.schemas import AuditLogItem, AuditLogListResponse
from app.services.audit_service import list_audit_logs
from app.services.auth_service import require_roles

router = APIRouter(prefix="/audit-logs", tags=["audit"])


def _audit_log_to_schema(audit_log: AuditLog) -> AuditLogItem:
    return AuditLogItem(
        id=audit_log.id,
        user_id=audit_log.user_id,
        department_id=audit_log.department_id,
        department_name=audit_log.department.name if audit_log.department else None,
        department_code=audit_log.department.code if audit_log.department else None,
        department_full_path=audit_log.department.full_path if audit_log.department else None,
        username=audit_log.username,
        action=audit_log.action,
        entity_type=audit_log.entity_type,
        entity_id=audit_log.entity_id,
        ip_address=audit_log.ip_address,
        user_agent=audit_log.user_agent,
        details=audit_log.details,
        created_at=audit_log.created_at,
    )


@router.get("", response_model=AuditLogListResponse, status_code=status.HTTP_200_OK)
async def get_audit_logs(
    limit: int = Query(default=20),
    offset: int = Query(default=0),
    action: str | None = Query(default=None),
    username: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    department_id: int | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> AuditLogListResponse:
    try:
        audit_logs, total = await list_audit_logs(
            session=session,
            current_user=current_user,
            limit=limit,
            offset=offset,
            action=action,
            username=username,
            entity_type=entity_type,
            entity_id=entity_id,
            department_id=department_id,
            date_from=date_from,
            date_to=date_to,
        )
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return AuditLogListResponse(
        items=[_audit_log_to_schema(audit_log) for audit_log in audit_logs],
        total=total,
        limit=limit,
        offset=offset,
    )
