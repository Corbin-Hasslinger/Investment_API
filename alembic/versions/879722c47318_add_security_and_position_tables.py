"""add security and position tables

Revision ID: 879722c47318
Revises: 685edc18786c
Create Date: 2026-08-11 04:04:36.938161

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "879722c47318"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "security",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("exchange", sa.String(length=50), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_table(
        "position",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("portfolio_id", sa.UUID(), nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("shares", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("avg_cost", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolio.id"]),
        sa.ForeignKeyConstraint(["symbol"], ["security.symbol"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("portfolio_id", "symbol", name="uq_portfolio_id_symbol"),
        sa.CheckConstraint("shares > 0", name="ck_position_shares_positive"),
        sa.CheckConstraint("avg_cost >= 0", name="ck_position_avg_cost_non_negative"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("position")
    op.drop_table("security")
