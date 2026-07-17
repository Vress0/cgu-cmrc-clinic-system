"""add system administration fields

Revision ID: 202607170008
Revises: 202607170007
Create Date: 2026-07-18 00:08:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607170008"
down_revision: str | None = "202607170007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("consents", sa.Column("consented_by", sa.Uuid(), nullable=True))
    op.add_column("consents", sa.Column("research_withdrawn_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("consents", sa.Column("withdrawn_by", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_consents_consented_by_users", "consents", "users", ["consented_by"], ["id"])
    op.create_foreign_key("fk_consents_withdrawn_by_users", "consents", "users", ["withdrawn_by"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_consents_withdrawn_by_users", "consents", type_="foreignkey")
    op.drop_constraint("fk_consents_consented_by_users", "consents", type_="foreignkey")
    op.drop_column("consents", "withdrawn_by")
    op.drop_column("consents", "research_withdrawn_at")
    op.drop_column("consents", "consented_by")
