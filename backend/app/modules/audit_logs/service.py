from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.audit_logs.models import AuditLog


def write_audit_log(
    db: Session,
    *,
    actor_user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
    summary: str = "",
) -> AuditLog:
    log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
    )
    db.add(log)
    return log
