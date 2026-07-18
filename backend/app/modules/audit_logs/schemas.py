from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.data_mode import DataMode


class AuditLogRead(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    action: str
    entity_type: str
    entity_id: UUID | None
    summary: str
    data_mode: DataMode
    created_at: datetime

    model_config = {"from_attributes": True}
