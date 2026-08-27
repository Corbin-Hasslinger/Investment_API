import datetime
import uuid
from datetime import UTC

from sqlalchemy import UUID, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlmodel import Field, SQLModel


class Portfolio(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_id_name"),)

    """Represents a portfolio in the database."""
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(
            "user_id",
            UUID(as_uuid=True),
            ForeignKey("user.id"),
            nullable=False,
        )
    )
    name: str = Field(
        min_length=1,
        sa_column=Column(
            "name",
            String(50),
            nullable=False,
        ),
    )
    description: str | None = Field(
        sa_column=Column("description", String(500), nullable=True, default=None)
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
