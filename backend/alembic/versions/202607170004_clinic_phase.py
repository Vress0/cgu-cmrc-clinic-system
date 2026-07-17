"""clinic phase

Revision ID: 202607170004
Revises: 202607170003
Create Date: 2026-07-17 22:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "202607170004"
down_revision: str | None = "202607170003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    blood_glucose_context = postgresql.ENUM(
        "FASTING",
        "BEFORE_MEAL",
        "AFTER_MEAL",
        "RANDOM",
        "UNKNOWN",
        name="bloodglucosecontext",
        create_type=False,
    )
    blood_glucose_context.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "audit_logs",
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)

    op.create_table(
        "vital_signs",
        sa.Column("visit_id", sa.Uuid(), nullable=False),
        sa.Column("systolic_blood_pressure", sa.Integer(), nullable=True),
        sa.Column("diastolic_blood_pressure", sa.Integer(), nullable=True),
        sa.Column("pulse", sa.Integer(), nullable=True),
        sa.Column("temperature", sa.Numeric(4, 1), nullable=True),
        sa.Column("oxygen_saturation", sa.Integer(), nullable=True),
        sa.Column("height_cm", sa.Numeric(5, 2), nullable=True),
        sa.Column("weight_kg", sa.Numeric(5, 2), nullable=True),
        sa.Column("bmi", sa.Numeric(5, 2), nullable=True),
        sa.Column("blood_glucose", sa.Numeric(6, 2), nullable=True),
        sa.Column("blood_glucose_context", blood_glucose_context, nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("measured_by", sa.Uuid(), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["measured_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vital_signs_measured_at"), "vital_signs", ["measured_at"], unique=False)
    op.create_index(op.f("ix_vital_signs_measured_by"), "vital_signs", ["measured_by"], unique=False)
    op.create_index(op.f("ix_vital_signs_visit_id"), "vital_signs", ["visit_id"], unique=False)

    op.create_table(
        "consultations",
        sa.Column("visit_id", sa.Uuid(), nullable=False),
        sa.Column("chief_complaint", sa.Text(), nullable=False),
        sa.Column("symptom_description", sa.Text(), nullable=False),
        sa.Column("symptom_location", sa.Text(), nullable=False),
        sa.Column("symptom_onset", sa.Text(), nullable=False),
        sa.Column("symptom_duration", sa.Text(), nullable=False),
        sa.Column("symptom_frequency", sa.Text(), nullable=False),
        sa.Column("symptom_severity", sa.Text(), nullable=False),
        sa.Column("worsening", sa.Text(), nullable=False),
        sa.Column("previously_sought_care", sa.Text(), nullable=False),
        sa.Column("previous_treatment", sa.Text(), nullable=False),
        sa.Column("student_notes", sa.Text(), nullable=False),
        sa.Column("recorded_by", sa.Uuid(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clinical_findings", sa.Text(), nullable=False),
        sa.Column("assessment_summary", sa.Text(), nullable=False),
        sa.Column("treatment_recommendation", sa.Text(), nullable=False),
        sa.Column("health_education", sa.Text(), nullable=False),
        sa.Column("referral_recommendation", sa.Text(), nullable=False),
        sa.Column("referral_urgency", sa.Text(), nullable=False),
        sa.Column("follow_up_recommendation", sa.Text(), nullable=False),
        sa.Column("requires_pharmacy", sa.Boolean(), nullable=False),
        sa.Column("clinician_notes", sa.Text(), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("inspection", sa.Text(), nullable=False),
        sa.Column("auscultation_olfaction", sa.Text(), nullable=False),
        sa.Column("inquiry", sa.Text(), nullable=False),
        sa.Column("palpation", sa.Text(), nullable=False),
        sa.Column("tongue_notes", sa.Text(), nullable=False),
        sa.Column("pulse_notes", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("visit_id"),
    )
    op.create_index(op.f("ix_consultations_visit_id"), "consultations", ["visit_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_consultations_visit_id"), table_name="consultations")
    op.drop_table("consultations")
    op.drop_index(op.f("ix_vital_signs_visit_id"), table_name="vital_signs")
    op.drop_index(op.f("ix_vital_signs_measured_by"), table_name="vital_signs")
    op.drop_index(op.f("ix_vital_signs_measured_at"), table_name="vital_signs")
    op.drop_table("vital_signs")
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")
    sa.Enum(name="bloodglucosecontext").drop(op.get_bind(), checkfirst=True)
