
import datetime
import uuid
from datetime import UTC

from sqlalchemy import UUID, Column, DateTime, String
from sqlmodel import Field, SQLModel


class Security(SQLModel,
               table=True):
    id: uuid.UUID = Field(
                default_factory=uuid.uuid4,
                sa_column=Column(
                    "id", 
                    UUID(as_uuid=True),
                    primary_key=True,
                    nullable=False
                    )
            )
    symbol: str = Field(
                min_length=1,
                sa_column=Column(
                    "ticker", 
                    String(5),
                    nullable=False,
                    unique=True
                    )
            )
    name: str = Field(
                min_length=1,
                sa_column=Column(
                    "name", 
                    String(100),
                    nullable=False,
                    unique=True
                    )
            )
    exchange: str = Field(
                min_length=1,
                sa_column=Column(
                    "exchange", 
                    String(50),
                    nullable=False,
                    )
            )
    currency: str = Field(
                min_length=1,
                sa_column=Column(
                    "currency", 
                    String(10),
                    nullable=False,
                    )
            )
    created_at: datetime.datetime = Field(
                    default_factory=lambda: datetime.datetime.now(UTC),
                    sa_column=Column(
                        "created_at", 
                        DateTime(timezone=True), 
                        nullable=False,
                    )
            )
    updated_at: datetime.datetime = Field(
            default_factory=lambda: datetime.datetime.now(UTC),
            sa_column=Column(
                "updated_at", 
                DateTime(timezone=True), 
                nullable=False,
                onupdate=lambda: datetime.datetime.now(UTC)
                )
        )