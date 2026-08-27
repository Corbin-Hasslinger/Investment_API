import datetime
import uuid
from datetime import UTC
from decimal import Decimal

from sqlalchemy import (
    UUID,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
)
from sqlmodel import Field, SQLModel, String


class Position(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("portfolio_id", "symbol", name="uq_portfolio_id_symbol"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
    )
    portfolio_id: uuid.UUID = Field(
        sa_column=Column(
            "portfolio_id",
            UUID(as_uuid=True),
            ForeignKey("portfolio.id"),
            nullable=False,
        )
    )
    symbol: str = Field(
        sa_column=Column(
            "symbol",
            String(10),
            ForeignKey("security.symbol"),
            nullable=False,
        )
    )
    shares: Decimal = Field(
        sa_column=Column(
            "shares",
            Numeric(precision=18, scale=6),
            CheckConstraint("shares > 0", name="ck_position_shares_positive"),
            nullable=False,
        )
    )
    average_cost: Decimal = Field(
        ge=0.0,
        sa_column=Column(
            "avg_cost",
            Numeric(precision=18, scale=6),
            CheckConstraint("avg_cost >= 0", name="ck_position_avg_cost_non_negative"),
            nullable=False,
        ),
    )
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(UTC),
        sa_column=Column(
            "created_at",
            DateTime(timezone=True),
            nullable=False,
        ),
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(UTC),
        sa_column=Column(
            "updated_at",
            DateTime(timezone=True),
            nullable=False,
            onupdate=lambda: datetime.datetime.now(UTC),
        ),
    )
