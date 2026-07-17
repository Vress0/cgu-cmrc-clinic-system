from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Patient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "patients"

    case_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    sex: Mapped[str] = mapped_column(String(20), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    phone: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    residence_area: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    emergency_contact: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    emergency_contact_phone: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    primary_language: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    assistance_needs: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    health_history = relationship("HealthHistory", back_populates="patient", uselist=False)
