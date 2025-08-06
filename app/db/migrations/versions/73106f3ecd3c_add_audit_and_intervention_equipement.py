"""add audit and intervention_equipement

Revision ID: 73106f3ecd3c
Revises: df44b376bc8a
Create Date: 2025-08-06 15:04:05.699265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "73106f3ecd3c"
down_revision: Union[str, Sequence[str], None] = "df44b376bc8a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit and intervention_equipement tables."""
    op.create_table(
        "audits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("table_name", sa.String(length=255), nullable=False),
        sa.Column("object_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Index("idx_audit_table_object", "table_name", "object_id"),
        sa.Index("idx_audit_user_date", "user_id", "created_at"),
    )

    op.create_table(
        "interventions_equipements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("intervention_id", sa.Integer(), sa.ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("equipement_id", sa.Integer(), sa.ForeignKey("equipements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index("idx_intervention_equipement", "intervention_id", "equipement_id"),
    )


def downgrade() -> None:
    """Drop audit and intervention_equipement tables."""
    op.drop_table("interventions_equipements")
    op.drop_table("audits")
