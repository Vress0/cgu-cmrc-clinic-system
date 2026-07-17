from uuid import UUID

from sqlalchemy import ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class HealthHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "health_histories"

    patient_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    chronic_diseases: Mapped[str] = mapped_column(Text, default="", nullable=False)
    allergies: Mapped[str] = mapped_column(Text, default="", nullable=False)
    current_medications: Mapped[str] = mapped_column(Text, default="", nullable=False)
    surgery_history: Mapped[str] = mapped_column(Text, default="", nullable=False)
    fall_history: Mapped[str] = mapped_column(Text, default="", nullable=False)
    smoking_status: Mapped[str] = mapped_column(Text, default="", nullable=False)
    alcohol_status: Mapped[str] = mapped_column(Text, default="", nullable=False)
    sleep_status: Mapped[str] = mapped_column(Text, default="", nullable=False)
    diet_status: Mapped[str] = mapped_column(Text, default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    patient = relationship("Patient", back_populates="health_history")
