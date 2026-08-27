"""replace position security_id with symbol

Revision ID: 20260819_position_use_symbol
Revises: 13582c9486b0
Create Date: 2026-08-19

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260819_position_use_symbol"
down_revision: str | Sequence[str] | None = "13582c9486b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace Position.security_id with the referenced Security.symbol."""
    op.add_column("position", sa.Column("symbol", sa.String(length=10), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE position AS p
            SET symbol = s.symbol
            FROM security AS s
            WHERE p.security_id = s.id
            """
        )
    )

    op.alter_column("position", "symbol", nullable=False)
    op.drop_constraint("position_security_id_fkey", "position", type_="foreignkey")
    op.drop_constraint("uq_portfolio_id_security_id", "position", type_="unique")
    op.drop_column("position", "security_id")
    op.create_foreign_key(
        "position_symbol_fkey",
        "position",
        "security",
        ["symbol"],
        ["symbol"],
    )
    op.create_unique_constraint(
        "uq_portfolio_id_symbol",
        "position",
        ["portfolio_id", "symbol"],
    )


def downgrade() -> None:
    """Restore Position.security_id from the referenced Security.symbol."""
    op.add_column("position", sa.Column("security_id", sa.UUID(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE position AS p
            SET security_id = s.id
            FROM security AS s
            WHERE p.symbol = s.symbol
            """
        )
    )

    op.alter_column("position", "security_id", nullable=False)
    op.drop_constraint("uq_portfolio_id_symbol", "position", type_="unique")
    op.drop_constraint("position_symbol_fkey", "position", type_="foreignkey")
    op.drop_column("position", "symbol")
    op.create_foreign_key(
        "position_security_id_fkey",
        "position",
        "security",
        ["security_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_portfolio_id_security_id",
        "position",
        ["portfolio_id", "security_id"],
    )
