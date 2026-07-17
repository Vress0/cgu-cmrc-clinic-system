from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit_logs.models import AuditLog
from app.modules.audit_logs.schemas import AuditLogRead
from app.modules.auth.dependencies import require_permissions

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    db: Session = Depends(get_db),
    _=Depends(require_permissions("audit_logs:read")),
) -> list[AuditLog]:
    statement = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)
    return list(db.execute(statement).scalars())
