"""add data mode isolation

Revision ID: 202607180009
Revises: 202607170008
Create Date: 2026-07-18 03:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607180009"
down_revision: str | None = "202607170008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCOPED_TABLES = [
    "clinic_sessions",
    "patients",
    "consents",
    "health_histories",
    "visits",
    "queue_records",
    "vital_signs",
    "consultations",
    "prescriptions",
    "prescription_items",
    "dispensing_records",
    "dispensing_items",
    "inventory_batches",
    "inventory_transactions",
    "audit_logs",
]


def add_data_mode_column(table_name: str) -> None:
    op.add_column(
        table_name,
        sa.Column("data_mode", sa.Enum("LIVE", "DEMO", name="datamode"), server_default="LIVE", nullable=False),
    )
    op.create_index(f"ix_{table_name}_data_mode", table_name, ["data_mode"])


def drop_data_mode_column(table_name: str) -> None:
    op.drop_index(f"ix_{table_name}_data_mode", table_name=table_name)
    op.drop_column(table_name, "data_mode")


def upgrade() -> None:
    data_mode_enum = sa.Enum("LIVE", "DEMO", name="datamode")
    data_mode_enum.create(op.get_bind(), checkfirst=True)

    for table_name in SCOPED_TABLES:
        add_data_mode_column(table_name)

    op.add_column("users", sa.Column("can_access_live", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column("users", sa.Column("can_access_demo", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column("users", sa.Column("default_data_mode", sa.Enum("LIVE", "DEMO", name="datamode"), server_default="LIVE", nullable=False))
    op.add_column("users", sa.Column("current_data_mode", sa.Enum("LIVE", "DEMO", name="datamode"), server_default="LIVE", nullable=False))

    op.drop_constraint("uq_session_name_date", "clinic_sessions", type_="unique")
    op.create_unique_constraint("uq_session_mode_name_date", "clinic_sessions", ["data_mode", "name", "session_date"])

    op.drop_constraint("patients_case_number_key", "patients", type_="unique")
    op.create_unique_constraint("uq_patient_mode_case_number", "patients", ["data_mode", "case_number"])

    op.drop_constraint("uq_visit_session_patient", "visits", type_="unique")
    op.create_unique_constraint("uq_visit_mode_session_patient", "visits", ["data_mode", "clinic_session_id", "patient_id"])

    op.drop_constraint("uq_queue_session_number", "queue_records", type_="unique")
    op.create_unique_constraint("uq_queue_mode_session_number", "queue_records", ["data_mode", "clinic_session_id", "queue_number"])

    op.drop_constraint("uq_prescription_visit", "prescriptions", type_="unique")
    op.create_unique_constraint("uq_prescription_mode_visit", "prescriptions", ["data_mode", "visit_id"])


def downgrade() -> None:
    op.drop_constraint("uq_prescription_mode_visit", "prescriptions", type_="unique")
    op.create_unique_constraint("uq_prescription_visit", "prescriptions", ["visit_id"])

    op.drop_constraint("uq_queue_mode_session_number", "queue_records", type_="unique")
    op.create_unique_constraint("uq_queue_session_number", "queue_records", ["clinic_session_id", "queue_number"])

    op.drop_constraint("uq_visit_mode_session_patient", "visits", type_="unique")
    op.create_unique_constraint("uq_visit_session_patient", "visits", ["clinic_session_id", "patient_id"])

    op.drop_constraint("uq_patient_mode_case_number", "patients", type_="unique")
    op.create_unique_constraint("patients_case_number_key", "patients", ["case_number"])

    op.drop_constraint("uq_session_mode_name_date", "clinic_sessions", type_="unique")
    op.create_unique_constraint("uq_session_name_date", "clinic_sessions", ["name", "session_date"])

    op.drop_column("users", "current_data_mode")
    op.drop_column("users", "default_data_mode")
    op.drop_column("users", "can_access_demo")
    op.drop_column("users", "can_access_live")

    for table_name in reversed(SCOPED_TABLES):
        drop_data_mode_column(table_name)

    sa.Enum("LIVE", "DEMO", name="datamode").drop(op.get_bind(), checkfirst=True)
