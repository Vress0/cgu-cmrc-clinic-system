from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit_logs.models import AuditLog
from app.modules.audit_logs.schemas import AuditLogRead
from app.modules.auth.dependencies import require_permissions

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    action: str | None = None,
    entity_type: str | None = None,
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(require_permissions("audit_logs:read")),
) -> list[AuditLog]:
    statement = select(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        statement = statement.where(AuditLog.action == action)
    if entity_type:
        statement = statement.where(AuditLog.entity_type == entity_type)
    if q:
        keyword = f"%{q}%"
        statement = statement.where(or_(AuditLog.action.ilike(keyword), AuditLog.summary.ilike(keyword)))
    statement = statement.limit(limit)
    return list(db.execute(statement).scalars())
