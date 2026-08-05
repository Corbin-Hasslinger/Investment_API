
import datetime
import uuid

from sqlalchemy import UUID, Column, DateTime, String
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            "id", 
            UUID(as_uuid=True),
            primary_key=True,
            nullable=False
            )
        )
    email: str = Field(
        sa_column=Column(
            "email", 
            String, 
            unique=True, 
            nullable=False
            )
        )
    hashed_password: str = Field(
        sa_column=Column(
            "hashed_password", 
            String, 
            nullable=False
            )
        )
    created_at: datetime.datetime = Field(
        sa_column=Column(
            "created_at", 
            DateTime(timezone=True), 
            nullable=False,
            default=datetime.datetime.utcnow
            )
        )
    updated_at: datetime.datetime = Field(
        sa_column=Column(
            "updated_at", 
            DateTime(timezone=True), 
            nullable=False,
            default=datetime.datetime.utcnow,
            onupdate=datetime.datetime.utcnow
            )
        )


