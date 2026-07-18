from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DataModeScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Consultation(UUIDPrimaryKeyMixin, DataModeScopedMixin, TimestampMixin, Base):
    __tablename__ = "consultations"

    visit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("visits.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    chief_complaint: Mapped[str] = mapped_column(Text, default="", nullable=False)
    symptom_description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    symptom_location: Mapped[str] = mapped_column(Text, default="", nullable=False)
    symptom_onset: Mapped[str] = mapped_column(Text, default="", nullable=False)
    symptom_duration: Mapped[str] = mapped_column(Text, default="", nullable=False)
    symptom_frequency: Mapped[str] = mapped_column(Text, default="", nullable=False)
    symptom_severity: Mapped[str] = mapped_column(Text, default="", nullable=False)
    worsening: Mapped[str] = mapped_column(Text, default="", nullable=False)
    previously_sought_care: Mapped[str] = mapped_column(Text, default="", nullable=False)
    previous_treatment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    student_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    recorded_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    clinical_findings: Mapped[str] = mapped_column(Text, default="", nullable=False)
    assessment_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    treatment_recommendation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    health_education: Mapped[str] = mapped_column(Text, default="", nullable=False)
    referral_recommendation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    referral_urgency: Mapped[str] = mapped_column(Text, default="", nullable=False)
    follow_up_recommendation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    requires_pharmacy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    clinician_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reviewed_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    inspection: Mapped[str] = mapped_column(Text, default="", nullable=False)
    auscultation_olfaction: Mapped[str] = mapped_column(Text, default="", nullable=False)
    inquiry: Mapped[str] = mapped_column(Text, default="", nullable=False)
    palpation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tongue_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    pulse_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    visit = relationship("Visit", back_populates="consultation")
