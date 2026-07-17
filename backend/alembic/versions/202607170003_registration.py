"""registration

Revision ID: 202607170003
Revises: 202607170002
Create Date: 2026-07-17 00:20:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607170003"
down_revision: str | None = "202607170002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clinic_sessions",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("location", sa.String(length=160), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "ACTIVE", "ENDED", "ARCHIVED", name="clinicsessionstatus"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "session_date", name="uq_session_name_date"),
    )
    op.create_index(op.f("ix_clinic_sessions_session_date"), "clinic_sessions", ["session_date"], unique=False)
    op.create_index(op.f("ix_clinic_sessions_status"), "clinic_sessions", ["status"], unique=False)

    op.create_table(
        "patients",
        sa.Column("case_number", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("sex", sa.String(length=20), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=False),
        sa.Column("residence_area", sa.String(length=120), nullable=False),
        sa.Column("emergency_contact", sa.String(length=80), nullable=False),
        sa.Column("emergency_contact_phone", sa.String(length=40), nullable=False),
        sa.Column("primary_language", sa.String(length=40), nullable=False),
        sa.Column("assistance_needs", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_number"),
    )
    op.create_index(op.f("ix_patients_case_number"), "patients", ["case_number"], unique=True)
    op.create_index(op.f("ix_patients_name"), "patients", ["name"], unique=False)

    op.create_table(
        "consents",
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("method", sa.String(length=40), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("staff_name", sa.String(length=120), nullable=False),
        sa.Column("service_consent", sa.Boolean(), nullable=False),
        sa.Column("research_consent", sa.Boolean(), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_consents_patient_id"), "consents", ["patient_id"], unique=False)

    op.create_table(
        "health_histories",
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("chronic_diseases", sa.Text(), nullable=False),
        sa.Column("allergies", sa.Text(), nullable=False),
        sa.Column("current_medications", sa.Text(), nullable=False),
        sa.Column("surgery_history", sa.Text(), nullable=False),
        sa.Column("fall_history", sa.Text(), nullable=False),
        sa.Column("smoking_status", sa.Text(), nullable=False),
        sa.Column("alcohol_status", sa.Text(), nullable=False),
        sa.Column("sleep_status", sa.Text(), nullable=False),
        sa.Column("diet_status", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patient_id"),
    )
    op.create_index(op.f("ix_health_histories_patient_id"), "health_histories", ["patient_id"], unique=True)

    op.create_table(
        "visits",
        sa.Column("clinic_session_id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("queue_number", sa.Integer(), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Enum("REGISTERED", "WAITING_FOR_CLINIC", "IN_CONSULTATION", "WAITING_FOR_PHARMACY", "DISPENSING", "WAITING_FOR_PICKUP", "COMPLETED", "CANCELLED", name="visitstatus"), nullable=False),
        sa.Column("registration_staff", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_session_id"], ["clinic_sessions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_session_id", "patient_id", name="uq_visit_session_patient"),
    )
    op.create_index(op.f("ix_visits_clinic_session_id"), "visits", ["clinic_session_id"], unique=False)
    op.create_index(op.f("ix_visits_patient_id"), "visits", ["patient_id"], unique=False)
    op.create_index(op.f("ix_visits_status"), "visits", ["status"], unique=False)

    op.create_table(
        "queue_records",
        sa.Column("clinic_session_id", sa.Uuid(), nullable=False),
        sa.Column("visit_id", sa.Uuid(), nullable=False),
        sa.Column("queue_number", sa.Integer(), nullable=False),
        sa.Column("called_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("skipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_session_id"], ["clinic_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_session_id", "queue_number", name="uq_queue_session_number"),
        sa.UniqueConstraint("visit_id"),
    )
    op.create_index(op.f("ix_queue_records_clinic_session_id"), "queue_records", ["clinic_session_id"], unique=False)
    op.create_index(op.f("ix_queue_records_visit_id"), "queue_records", ["visit_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_queue_records_visit_id"), table_name="queue_records")
    op.drop_index(op.f("ix_queue_records_clinic_session_id"), table_name="queue_records")
    op.drop_table("queue_records")
    op.drop_index(op.f("ix_visits_status"), table_name="visits")
    op.drop_index(op.f("ix_visits_patient_id"), table_name="visits")
    op.drop_index(op.f("ix_visits_clinic_session_id"), table_name="visits")
    op.drop_table("visits")
    op.drop_index(op.f("ix_health_histories_patient_id"), table_name="health_histories")
    op.drop_table("health_histories")
    op.drop_index(op.f("ix_consents_patient_id"), table_name="consents")
    op.drop_table("consents")
    op.drop_index(op.f("ix_patients_name"), table_name="patients")
    op.drop_index(op.f("ix_patients_case_number"), table_name="patients")
    op.drop_table("patients")
    op.drop_index(op.f("ix_clinic_sessions_status"), table_name="clinic_sessions")
    op.drop_index(op.f("ix_clinic_sessions_session_date"), table_name="clinic_sessions")
    op.drop_table("clinic_sessions")
    sa.Enum(name="visitstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="clinicsessionstatus").drop(op.get_bind(), checkfirst=True)
