from datetime import datetime

from pydantic import BaseModel


class AuditLogItem(BaseModel):
    id: int
    user_id: int | None
    username: str | None
    action: str
    entity_type: str | None
    entity_id: str | None
    ip_address: str | None
    user_agent: str | None
    details: str | None
    created_at: datetime
