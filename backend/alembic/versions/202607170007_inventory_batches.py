"""add inventory batches and transactions

Revision ID: 202607170007
Revises: 202607170006
Create Date: 2026-07-18 00:07:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607170007"
down_revision: str | None = "202607170006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    transaction_type = sa.Enum(
        "RECEIVE",
        "RESERVE",
        "RELEASE",
        "DISPENSE",
        "RETURN",
        "ADJUST_INCREASE",
        "ADJUST_DECREASE",
        "EXPIRE",
        "DISCARD",
        name="inventorytransactiontype",
    )

    op.create_table(
        "inventory_batches",
        sa.Column("medication_id", sa.Uuid(), nullable=False),
        sa.Column("batch_number", sa.String(length=120), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("quantity_on_hand", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("reserved_quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=40), nullable=False),
        sa.Column("location", sa.String(length=160), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_batches_quantity_nonnegative"),
        sa.CheckConstraint("reserved_quantity >= 0", name="ck_inventory_batches_reserved_nonnegative"),
        sa.CheckConstraint("reserved_quantity <= quantity_on_hand", name="ck_inventory_batches_reserved_lte_on_hand"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inventory_batches_batch_number"), "inventory_batches", ["batch_number"], unique=False)
    op.create_index(op.f("ix_inventory_batches_expiry_date"), "inventory_batches", ["expiry_date"], unique=False)
    op.create_index(op.f("ix_inventory_batches_is_active"), "inventory_batches", ["is_active"], unique=False)
    op.create_index(op.f("ix_inventory_batches_medication_id"), "inventory_batches", ["medication_id"], unique=False)

    op.create_table(
        "inventory_transactions",
        sa.Column("medication_id", sa.Uuid(), nullable=False),
        sa.Column("inventory_batch_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_type", transaction_type, nullable=False),
        sa.Column("quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quantity_before", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quantity_after", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("reserved_before", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("reserved_after", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("reference_type", sa.String(length=80), nullable=False),
        sa.Column("reference_id", sa.Uuid(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("performed_by", sa.Uuid(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=120), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["inventory_batch_id"], ["inventory_batches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(op.f("ix_inventory_transactions_inventory_batch_id"), "inventory_transactions", ["inventory_batch_id"], unique=False)
    op.create_index(op.f("ix_inventory_transactions_medication_id"), "inventory_transactions", ["medication_id"], unique=False)
    op.create_index(op.f("ix_inventory_transactions_transaction_type"), "inventory_transactions", ["transaction_type"], unique=False)

    op.create_index(op.f("ix_dispensing_items_inventory_batch_id"), "dispensing_items", ["inventory_batch_id"], unique=False)
    op.create_foreign_key(
        "fk_dispensing_items_inventory_batch_id_inventory_batches",
        "dispensing_items",
        "inventory_batches",
        ["inventory_batch_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_dispensing_items_inventory_batch_id_inventory_batches", "dispensing_items", type_="foreignkey")
    op.drop_index(op.f("ix_dispensing_items_inventory_batch_id"), table_name="dispensing_items")
    op.drop_index(op.f("ix_inventory_transactions_transaction_type"), table_name="inventory_transactions")
    op.drop_index(op.f("ix_inventory_transactions_medication_id"), table_name="inventory_transactions")
    op.drop_index(op.f("ix_inventory_transactions_inventory_batch_id"), table_name="inventory_transactions")
    op.drop_table("inventory_transactions")
    op.drop_index(op.f("ix_inventory_batches_medication_id"), table_name="inventory_batches")
    op.drop_index(op.f("ix_inventory_batches_is_active"), table_name="inventory_batches")
    op.drop_index(op.f("ix_inventory_batches_expiry_date"), table_name="inventory_batches")
    op.drop_index(op.f("ix_inventory_batches_batch_number"), table_name="inventory_batches")
    op.drop_table("inventory_batches")
    op.execute("DROP TYPE IF EXISTS inventorytransactiontype")
