from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Medication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "medications"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    generic_name: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    brand_name: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    dosage_form: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    strength: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    unit: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    route: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    warnings: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    prescription_items = relationship("PrescriptionItem", back_populates="medication")
