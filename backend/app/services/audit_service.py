from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AuditEvent, User

async def record_audit_event(
    db: AsyncSession,
    actor_username: str,
    action: str,
    resource_type: str,
    resource_id: str,
    outcome: str = "SUCCESS",
    details: Optional[Dict[str, Any]] = None,
    ip_address: str = "127.0.0.1",
    actor_id: Optional[int] = None
):
    audit = AuditEvent(
        actor_id=actor_id,
        actor_username=actor_username,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        outcome=outcome,
        details=details,
        ip_address=ip_address
    )
    db.add(audit)
    await db.commit()
