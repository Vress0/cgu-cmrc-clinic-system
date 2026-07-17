"""add medications and prescriptions

Revision ID: 202607170005
Revises: 202607170004
Create Date: 2026-07-17 00:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607170005"
down_revision: str | None = "202607170004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "medications",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("generic_name", sa.String(length=160), nullable=False),
        sa.Column("brand_name", sa.String(length=160), nullable=False),
        sa.Column("dosage_form", sa.String(length=80), nullable=False),
        sa.Column("strength", sa.String(length=80), nullable=False),
        sa.Column("unit", sa.String(length=40), nullable=False),
        sa.Column("route", sa.String(length=80), nullable=False),
        sa.Column("manufacturer", sa.String(length=160), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("warnings", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_medications_code"), "medications", ["code"], unique=True)
    op.create_index(op.f("ix_medications_is_active"), "medications", ["is_active"], unique=False)
    op.create_index(op.f("ix_medications_name"), "medications", ["name"], unique=False)

    op.create_table(
        "prescriptions",
        sa.Column("visit_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "CONFIRMED", "SENT_TO_PHARMACY", "RETURNED_TO_CLINIC", "VOIDED", name="prescriptionstatus"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("confirmed_by", sa.Uuid(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_to_pharmacy_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("returned_reason", sa.Text(), nullable=False),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("visit_id", name="uq_prescription_visit"),
    )
    op.create_index(op.f("ix_prescriptions_status"), "prescriptions", ["status"], unique=False)
    op.create_index(op.f("ix_prescriptions_visit_id"), "prescriptions", ["visit_id"], unique=False)

    op.create_table(
        "prescription_items",
        sa.Column("prescription_id", sa.Uuid(), nullable=False),
        sa.Column("medication_id", sa.Uuid(), nullable=False),
        sa.Column("dose", sa.Text(), nullable=False),
        sa.Column("dose_unit", sa.Text(), nullable=False),
        sa.Column("frequency", sa.Text(), nullable=False),
        sa.Column("route", sa.Text(), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["prescription_id"], ["prescriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_prescription_items_medication_id"), "prescription_items", ["medication_id"], unique=False)
    op.create_index(op.f("ix_prescription_items_prescription_id"), "prescription_items", ["prescription_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_prescription_items_prescription_id"), table_name="prescription_items")
    op.drop_index(op.f("ix_prescription_items_medication_id"), table_name="prescription_items")
    op.drop_table("prescription_items")
    op.drop_index(op.f("ix_prescriptions_visit_id"), table_name="prescriptions")
    op.drop_index(op.f("ix_prescriptions_status"), table_name="prescriptions")
    op.drop_table("prescriptions")
    op.execute("DROP TYPE IF EXISTS prescriptionstatus")
    op.drop_index(op.f("ix_medications_name"), table_name="medications")
    op.drop_index(op.f("ix_medications_is_active"), table_name="medications")
    op.drop_index(op.f("ix_medications_code"), table_name="medications")
    op.drop_table("medications")
