"""Add mastery and last_reviewed_at to user_vocabulary

Revision ID: 003
Revises: 002
Create Date: 2025-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_vocabulary",
        sa.Column("mastery", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "user_vocabulary",
        sa.Column("last_reviewed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_vocabulary", "last_reviewed_at")
    op.drop_column("user_vocabulary", "mastery")
