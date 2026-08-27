import datetime
import uuid
from datetime import UTC

from sqlalchemy import UUID, Column, DateTime, String
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
    )
    email: str = Field(
        sa_column=Column(
            "email",
            String(100),  # Assuming you want to limit the email to 100 characters
            unique=True,
            nullable=False,
        )
    )
    hashed_password: str = Field(
        sa_column=Column(
            "hashed_password",
            String(
                200
            ),  # Assuming you want to limit the hashed password to 200 characters
            nullable=False,
        )
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
