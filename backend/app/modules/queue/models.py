from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class QueueRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "queue_records"
    __table_args__ = (
        UniqueConstraint("clinic_session_id", "queue_number", name="uq_queue_session_number"),
    )

    clinic_session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("clinic_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    visit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("visits.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    queue_number: Mapped[int] = mapped_column(nullable=False)
    called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    skipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    visit = relationship("Visit", back_populates="queue_record")
