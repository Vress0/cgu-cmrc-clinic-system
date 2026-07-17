"""add pharmacy dispensing workflow

Revision ID: 202607170006
Revises: 202607170005
Create Date: 2026-07-18 00:06:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607170006"
down_revision: str | None = "202607170005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE visitstatus ADD VALUE IF NOT EXISTS 'WAITING_FOR_VERIFICATION'")
    op.execute("ALTER TYPE prescriptionstatus ADD VALUE IF NOT EXISTS 'DISPENSING'")
    op.execute("ALTER TYPE prescriptionstatus ADD VALUE IF NOT EXISTS 'WAITING_FOR_VERIFICATION'")
    op.execute("ALTER TYPE prescriptionstatus ADD VALUE IF NOT EXISTS 'VERIFIED'")
    op.execute("ALTER TYPE prescriptionstatus ADD VALUE IF NOT EXISTS 'WAITING_FOR_PICKUP'")
    op.execute("ALTER TYPE prescriptionstatus ADD VALUE IF NOT EXISTS 'DISPENSED'")

    dispensing_status = sa.Enum(
        "PENDING",
        "IN_PROGRESS",
        "WAITING_FOR_VERIFICATION",
        "VERIFIED",
        "WAITING_FOR_PICKUP",
        "DISPENSED",
        "RETURNED",
        "CANCELLED",
        name="dispensingstatus",
    )
    return_reason = sa.Enum(
        "OUT_OF_STOCK",
        "UNCLEAR_DOSAGE",
        "UNCLEAR_INSTRUCTIONS",
        "INCORRECT_QUANTITY",
        "ALLERGY_RISK",
        "DUPLICATE_MEDICATION",
        "OTHER",
        name="returnreason",
    )

    op.create_table(
        "dispensing_records",
        sa.Column("visit_id", sa.Uuid(), nullable=False),
        sa.Column("prescription_id", sa.Uuid(), nullable=False),
        sa.Column("status", dispensing_status, nullable=False),
        sa.Column("assigned_to", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("prepared_by", sa.Uuid(), nullable=True),
        sa.Column("prepared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.Uuid(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_exception", sa.Boolean(), nullable=False),
        sa.Column("verification_exception_reason", sa.Text(), nullable=False),
        sa.Column("handed_out_by", sa.Uuid(), nullable=True),
        sa.Column("handed_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("patient_counseling", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("return_reason", return_reason, nullable=True),
        sa.Column("return_details", sa.Text(), nullable=False),
        sa.Column("returned_by", sa.Uuid(), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("handout_idempotency_key", sa.String(length=120), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["handed_out_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["prepared_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["prescription_id"], ["prescriptions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["returned_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("handout_idempotency_key"),
    )
    op.create_index(op.f("ix_dispensing_records_prescription_id"), "dispensing_records", ["prescription_id"], unique=False)
    op.create_index(op.f("ix_dispensing_records_status"), "dispensing_records", ["status"], unique=False)
    op.create_index(op.f("ix_dispensing_records_visit_id"), "dispensing_records", ["visit_id"], unique=False)

    op.create_table(
        "dispensing_items",
        sa.Column("dispensing_record_id", sa.Uuid(), nullable=False),
        sa.Column("prescription_item_id", sa.Uuid(), nullable=False),
        sa.Column("medication_id", sa.Uuid(), nullable=False),
        sa.Column("prescribed_quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("dispensed_quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("inventory_batch_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("dispensed_quantity >= 0", name="ck_dispensing_items_dispensed_nonnegative"),
        sa.CheckConstraint(
            "dispensed_quantity <= prescribed_quantity",
            name="ck_dispensing_items_dispensed_lte_prescribed",
        ),
        sa.ForeignKeyConstraint(["dispensing_record_id"], ["dispensing_records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["prescription_item_id"], ["prescription_items.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_dispensing_items_dispensing_record_id"), "dispensing_items", ["dispensing_record_id"], unique=False)
    op.create_index(op.f("ix_dispensing_items_medication_id"), "dispensing_items", ["medication_id"], unique=False)
    op.create_index(op.f("ix_dispensing_items_prescription_item_id"), "dispensing_items", ["prescription_item_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_dispensing_items_prescription_item_id"), table_name="dispensing_items")
    op.drop_index(op.f("ix_dispensing_items_medication_id"), table_name="dispensing_items")
    op.drop_index(op.f("ix_dispensing_items_dispensing_record_id"), table_name="dispensing_items")
    op.drop_table("dispensing_items")
    op.drop_index(op.f("ix_dispensing_records_visit_id"), table_name="dispensing_records")
    op.drop_index(op.f("ix_dispensing_records_status"), table_name="dispensing_records")
    op.drop_index(op.f("ix_dispensing_records_prescription_id"), table_name="dispensing_records")
    op.drop_table("dispensing_records")
    op.execute("DROP TYPE IF EXISTS returnreason")
    op.execute("DROP TYPE IF EXISTS dispensingstatus")
